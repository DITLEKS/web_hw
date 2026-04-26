from asyncio import gather as asyncio_gather
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.database import get_pool
from app.schemas import (
    CreateOrderRequest,
    ErrorResponse,
    OrderCreatedResponse,
    OrderDetailResponse,
    OrderListResponse,
)
from shared.utils import record_to_dict
from app.constants import DeliveryType, DELIVERY_COSTS, DiscountType, ErrorCode, StatusCode

router = APIRouter()


# Хелперы
    """
    Генерирует уникальный номер заказа вида LX-YYYYMMDD-NNNN.

    Advisory lock защищает от гонки при параллельных запросах —
    без него два потока могли бы получить одинаковый COUNT.
    """
    date_part = datetime.now(tz=timezone.utc).strftime("%Y%m%d")
    await conn.execute("SELECT pg_advisory_xact_lock(42)")
    count: int = await conn.fetchval(
        "SELECT COUNT(*) FROM orders WHERE order_number LIKE $1",
        f"LX-{date_part}-%",
    )
    return f"LX-{date_part}-{count + 1:04d}"


async def apply_promo(
    conn: asyncpg.Connection,
    code: Optional[str],
    subtotal: Decimal,
) -> tuple[Optional[int], Decimal]:
    """
    Проверяет промокод и возвращает (promo_id, сумму_скидки).
    Если код не передан — скидки нет.
    """
    if not code:
        return None, Decimal("0")

    promo = await conn.fetchrow(
        """
        SELECT * FROM promo_codes
        WHERE code = $1
          AND is_active = TRUE
          AND valid_from <= NOW()
          AND (valid_until IS NULL OR valid_until >= NOW())
          AND (max_uses IS NULL OR used_count < max_uses)
          AND min_order_amount <= $2
        """,
        code.upper(), subtotal,
    )
    if not promo:
        raise HTTPException(status_code=400, detail={
            "error":   "promo_invalid",
            "message": "Промокод недействителен или не применим к этому заказу",
        })

    if promo["discount_type"] == "percent":
        discount = subtotal * Decimal(str(promo["discount_value"])) / 100
    else:
        discount = Decimal(str(promo["discount_value"]))

    # Скидка не может превышать сумму заказа
    discount = min(discount, subtotal).quantize(Decimal("0.01"))
# POST /api/v1/orders
    "",
    status_code=201,
    response_model=OrderCreatedResponse,
    summary="Оформить заказ",
    description=(
        "Создаёт заказ из текущей корзины. После успешного создания корзина очищается автоматически.\n\n"
        "**Стоимость доставки:**\n"
        "- `courier` — 300 ₽\n"
        "- `cdek` — 250 ₽\n"
        "- `pickup` — бесплатно\n\n"
        "**Доступные промокоды для тестирования:**\n"
        "- `SALE20` — скидка 20% при заказе от 500 ₽\n"
        "- `WELCOME` — скидка 150 ₽ без минимальной суммы\n"
        "- `SMART15` — скидка 15% при заказе от 1000 ₽\n\n"
        "Все операции выполняются в одной транзакции — "
        "если что-то пойдёт не так, ни заказ, ни списания не сохранятся."
    ),
    responses={
        201: {"description": "Заказ успешно создан, корзина очищена"},
        400: {
            "description": "Корзина пуста, промокод недействителен или отсутствует X-Session-Id",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "examples": {
                        "cart_empty": {
                            "summary": "Корзина пуста",
                            "value": {
                                "error": "cart_empty",
                                "message": "Невозможно оформить заказ: корзина пуста",
                            },
                        },
                        "promo_invalid": {
                            "summary": "Недействительный промокод",
                            "value": {
                                "error": "promo_invalid",
                                "message": "Промокод недействителен или не применим к этому заказу",
                            },
                        },
                    }
                }
            },
        },
    },
)
async def create_order(
    body: CreateOrderRequest,
    x_session_id: Optional[str] = Header(
        None,
        description="Идентификатор сессии корзины. Обязателен для оформления заказа",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    ),
    pool: asyncpg.Pool = Depends(get_pool),
):
    if not x_session_id:
        raise HTTPException(status_code=400, detail={
            "error":   "session_required",
            "message": "Передайте заголовок X-Session-Id",
        })

    async with pool.acquire() as conn:
        async with conn.transaction():

            # Загружаем корзину внутри транзакции — данные не успеют
            # измениться до момента создания заказа
            cart_items = await conn.fetch(
                "SELECT * FROM cart_items WHERE session_id = $1",
                x_session_id,
            )
            if not cart_items:
                raise HTTPException(status_code=400, detail={
                    "error":   "cart_empty",
                    "message": "Невозможно оформить заказ: корзина пуста",
                })

            subtotal = sum(Decimal(str(i["total_price"])) for i in cart_items)

            promo_id, discount = await apply_promo(conn, body.promo_code, subtotal)

            delivery_cost = DELIVERY_COSTS[DeliveryType(body.delivery_type)]
            total_amount  = (subtotal - discount + delivery_cost).quantize(Decimal("0.01"))
            order_number  = await generate_order_number(conn)

            order = await conn.fetchrow(
                """
                INSERT INTO orders
                    (order_number, status, delivery_type, delivery_city, delivery_street,
                     delivery_zip, promo_code_id, discount_amount, subtotal,
                     delivery_cost, total_amount, payment_method, payment_status)
                VALUES
                    ($1, 'created', $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, 'pending')
                RETURNING id, order_number, status, subtotal, discount_amount,
                          delivery_cost, total_amount, payment_method, payment_status
                """,
                order_number,
                body.delivery_type, body.delivery_city, body.delivery_street,
                body.delivery_zip, promo_id, discount, subtotal,
                delivery_cost, total_amount, body.payment_method,
            )

            order_id = order["id"]

            # Вставляем все позиции одним вызовом — быстрее чем цикл запросов
            await conn.executemany(
                """INSERT INTO order_items
                       (order_id, sku, name, quantity, unit_price, total_price)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                [
                    (order_id, i["sku"], i["name"], i["quantity"],
                     i["unit_price"], i["total_price"])
                    for i in cart_items
                ],
            )

            await conn.execute(
                """INSERT INTO order_status_history (order_id, new_status, comment)
                   VALUES ($1, 'created', 'Заказ создан')""",
                order_id,
            )

            if promo_id:
                await conn.execute(
                    "UPDATE promo_codes SET used_count = used_count + 1 WHERE id = $1",
                    promo_id,
                )

            # Чистим корзину только после успешной вставки заказа
            await conn.execute(
                "DELETE FROM cart_items WHERE session_id = $1",
                x_session_id,
            )

    return {"data": record_to_dict(order), "message": "Заказ создан"}


# ── GET /api/v1/orders ────────────────────────────────────────────── #

@router.get(
    "",
    response_model=OrderListResponse,
    summary="История заказов",
    description=(
        "Возвращает список заказов с пагинацией, отсортированных по дате создания (новые первые). "
        "До добавления авторизации возвращает все заказы. "
        "В модуле 5 будет ограничен заказами текущего пользователя."
    ),
    responses={200: {"description": "Список заказов получен"}},
)
async def list_orders(
    page:  int = Query(1,  ge=1,       description="Номер страницы", example=1),
    limit: int = Query(10, ge=1, le=100, description="Заказов на странице (максимум 100)", example=10),
    pool: asyncpg.Pool = Depends(get_pool),
):
    total: int = await pool.fetchval("SELECT COUNT(*) FROM orders")
    offset = (page - 1) * limit

    rows = await pool.fetch(
        """
        SELECT o.order_number, o.status, o.total_amount,
               (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) AS items_count,
               o.created_at
        FROM orders o
        ORDER BY o.created_at DESC
        LIMIT $1 OFFSET $2
        """,
        limit, offset,
    )

# GET /api/v1/orders/{order_number}
    response_model=OrderDetailResponse,
    summary="Детали заказа",
    description=(
        "Возвращает полную информацию о заказе: позиции, адрес доставки, "
        "историю изменений статуса и данные об оплате. "
        "Номер заказа имеет формат `LX-YYYYMMDD-NNNN`."
    ),
    responses={
        200: {"description": "Детали заказа получены"},
        404: {
            "description": "Заказ с таким номером не найден",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "order_not_found",
                        "message": "Заказ с указанным номером не найден",
                    }
                }
            },
        },
    },
)
async def get_order(
    order_number: str,
    pool: asyncpg.Pool = Depends(get_pool),
):
    row = await pool.fetchrow(
        """
        SELECT o.order_number, o.status, o.delivery_type,
               o.delivery_city, o.delivery_street, o.delivery_zip,
               o.subtotal, o.discount_amount, o.delivery_cost, o.total_amount,
               o.payment_method, o.payment_status, o.tracking_number,
               pc.code AS promo_code
        FROM orders o
        LEFT JOIN promo_codes pc ON pc.id = o.promo_code_id
        WHERE o.order_number = $1
        """,
        order_number,
    )
    if not row:
        raise HTTPException(status_code=404, detail={
            "error":   "order_not_found",
            "message": "Заказ с указанным номером не найден",
        })

    order = record_to_dict(row)

    # Позиции и историю статусов загружаем параллельно
    items, history = await asyncio_gather(
        pool.fetch(
            """SELECT sku, name, quantity, unit_price, total_price
               FROM order_items
               WHERE order_id = (SELECT id FROM orders WHERE order_number = $1)""",
            order_number,
        ),
        pool.fetch(
            """SELECT new_status AS status, changed_at, comment
               FROM order_status_history
               WHERE order_id = (SELECT id FROM orders WHERE order_number = $1)
               ORDER BY changed_at""",
            order_number,
        ),
    )

    order["items"]          = [record_to_dict(i) for i in items]
    order["status_history"] = [record_to_dict(h) for h in history]
    return {"data": order}
