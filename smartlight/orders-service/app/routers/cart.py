from decimal import Decimal
from typing import Optional

import asyncpg
import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Response

from app.database import get_http, get_pool
from app.schemas import (
    AddItemRequest,
    CartItemAddedResponse,
    CartItemUpdatedResponse,
    CartResponse,
    ErrorResponse,
    UpdateItemRequest,
)
from shared.utils import new_session_id, record_to_dict

# Хелперы
    """
    Возвращает (session_id, is_new).
    Если заголовок не пришёл — генерируем новый UUID.
    """
    if x_session_id and len(x_session_id) >= 8:
        return x_session_id, False
    return new_session_id(), True


async def fetch_product_from_catalog(
    http: httpx.AsyncClient, sku: str
) -> dict | None:
    """Идём в catalog-service за актуальной ценой и остатком."""
    try:
        resp = await http.get(f"/api/v1/products/{sku}")
        if resp.status_code == 200:
            return resp.json()["data"]
    except httpx.RequestError:
        # Catalog недоступен — не роняем сервис, просто вернём None
        pass
# GET /api/v1/cart
    "",
    response_model=CartResponse,
    summary="Получить корзину",
    description=(
        "Возвращает содержимое корзины текущей сессии. "
        "Корзина идентифицируется по заголовку **`X-Session-Id`**. "
        "Если заголовок отсутствует — сервер создаёт новую сессию "
        "и возвращает её ID в заголовке ответа `X-Session-Id`."
    ),
    responses={200: {"description": "Корзина получена (может быть пустой)"}},
)
async def get_cart(
    response: Response,
    x_session_id: Optional[str] = Header(
        None,
        description="Идентификатор сессии (UUID). Генерируется автоматически при первом обращении",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    ),
    pool: asyncpg.Pool = Depends(get_pool),
):
    session_id, is_new = resolve_session(x_session_id)
    if is_new:
        response.headers["X-Session-Id"] = session_id

    rows = await pool.fetch(
        """SELECT id AS item_id, sku, name, quantity, unit_price, total_price
           FROM cart_items WHERE session_id = $1 ORDER BY added_at""",
        session_id,
    )

    items = [record_to_dict(r) for r in rows]
    subtotal = sum(Decimal(i["total_price"]) for i in items)

    return {
        "data": {
            "items":           items,
            "subtotal":        str(subtotal),
            "discount_amount": "0.00",
            "promo":           None,
        }
# POST /api/v1/cart/items
    "/items",
    status_code=200,
    response_model=CartItemAddedResponse,
    summary="Добавить товар в корзину",
    description=(
        "Добавляет товар в корзину или увеличивает его количество, "
        "если товар уже есть в корзине. "
        "Перед добавлением проверяет наличие товара и остаток на складе через catalog-service. "
        "Цена фиксируется на момент добавления."
    ),
    responses={
        200: {"description": "Товар добавлен в корзину"},
        400: {
            "description": "Недостаточно товара на складе",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "insufficient_stock",
                        "message": "Доступно только 1 шт.",
                        "available": 1,
                    }
                }
            },
        },
        404: {
            "description": "Товар не найден в каталоге",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "product_not_found"}
                }
            },
        },
    },
)
async def add_item(
    body: AddItemRequest,
    response: Response,
    x_session_id: Optional[str] = Header(
        None,
        description="Идентификатор сессии",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    ),
    pool: asyncpg.Pool     = Depends(get_pool),
    http: httpx.AsyncClient = Depends(get_http),
):
    session_id, is_new = resolve_session(x_session_id)
    if is_new:
        response.headers["X-Session-Id"] = session_id

    product = await fetch_product_from_catalog(http, body.sku)
    if not product:
        raise HTTPException(status_code=404, detail={"error": "product_not_found"})

    # Суммируем с уже имеющимся количеством в корзине
    existing = await pool.fetchrow(
        "SELECT quantity FROM cart_items WHERE session_id = $1 AND sku = $2",
        session_id, body.sku,
    )
    current_qty = existing["quantity"] if existing else 0
    new_qty = current_qty + body.quantity

    if new_qty > product["stock_quantity"]:
        raise HTTPException(status_code=400, detail={
            "error":     "insufficient_stock",
            "message":   f"Доступно только {product['stock_quantity']} шт.",
            "available": product["stock_quantity"],
        })

    unit_price  = Decimal(str(product["price"]))
    total_price = unit_price * new_qty

    row = await pool.fetchrow(
        """
        INSERT INTO cart_items (session_id, sku, name, unit_price, quantity, total_price)
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (session_id, sku) DO UPDATE
          SET quantity    = $5,
              unit_price  = $4,
              total_price = $6
        RETURNING id AS item_id, sku, quantity, total_price
        """,
        session_id, body.sku, product["name"], unit_price, new_qty, total_price,
    )

# PATCH /api/v1/cart/items/{item_id}
    "/items/{item_id}",
    response_model=CartItemUpdatedResponse,
    summary="Обновить количество товара в корзине",
    description=(
        "Устанавливает новое количество для позиции в корзине. "
        "Значение **заменяет** текущее (не прибавляется). "
        "При изменении проверяется актуальный остаток на складе."
    ),
    responses={
        200: {"description": "Количество обновлено"},
        400: {
            "description": "Недостаточно товара на складе",
            "model": ErrorResponse,
        },
        404: {
            "description": "Позиция в корзине не найдена",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "item_not_found"}
                }
            },
        },
    },
)
async def update_item(
    item_id: int,
    body: UpdateItemRequest,
    x_session_id: Optional[str] = Header(
        None,
        description="Идентификатор сессии",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    ),
    pool: asyncpg.Pool     = Depends(get_pool),
    http: httpx.AsyncClient = Depends(get_http),
):
    session_id, _ = resolve_session(x_session_id)

    item = await pool.fetchrow(
        "SELECT sku, unit_price FROM cart_items WHERE id = $1 AND session_id = $2",
        item_id, session_id,
    )
    if not item:
        raise HTTPException(status_code=404, detail={"error": "item_not_found"})

    # Проверяем актуальный остаток — мог измениться с момента добавления
    product = await fetch_product_from_catalog(http, item["sku"])
    if product and body.quantity > product["stock_quantity"]:
        raise HTTPException(status_code=400, detail={
            "error":     "insufficient_stock",
            "message":   f"Доступно только {product['stock_quantity']} шт.",
            "available": product["stock_quantity"],
        })

    total_price = Decimal(str(item["unit_price"])) * body.quantity

    row = await pool.fetchrow(
        """UPDATE cart_items SET quantity = $1, total_price = $2
           WHERE id = $3 AND session_id = $4
           RETURNING id AS item_id, quantity, total_price""",
        body.quantity, total_price, item_id, session_id,
    )

# DELETE /api/v1/cart/items/{item_id}
    "/items/{item_id}",
    status_code=204,
    summary="Удалить позицию из корзины",
    description="Удаляет одну позицию из корзины по её `item_id`. Остальные позиции не затрагиваются.",
    responses={
        204: {"description": "Позиция удалена"},
        404: {
            "description": "Позиция не найдена",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "item_not_found"}
                }
            },
        },
    },
)
async def delete_item(
    item_id: int,
    x_session_id: Optional[str] = Header(
        None,
        description="Идентификатор сессии",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    ),
    pool: asyncpg.Pool = Depends(get_pool),
):
    session_id, _ = resolve_session(x_session_id)
    result = await pool.execute(
        "DELETE FROM cart_items WHERE id = $1 AND session_id = $2",
        item_id, session_id,
    )
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail={"error": "item_not_found"})
