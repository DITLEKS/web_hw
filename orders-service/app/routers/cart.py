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


router = APIRouter()


def resolve_session(x_session_id: Optional[str]) -> tuple[str, bool]:
    """Возвращает (session_id, is_new). Если заголовок не пришёл, то генерирует новый UUID."""
    if x_session_id and len(x_session_id) >= 8:
        return x_session_id, False
    return new_session_id(), True


async def fetch_product(http: httpx.AsyncClient, sku: str) -> dict | None:
    try:
        resp = await http.get(f"/api/v1/products/{sku}")
        if resp.status_code == 200:
            return resp.json()["data"]
    except httpx.RequestError:
        pass
    return None


@router.get(
    "",
    response_model=CartResponse,
    summary="Получить содержимое корзины",
    description=(
        "Возвращает все позиции корзины текущей сессии, общую сумму и применённый промокод. "
        "Корзина идентифицируется по заголовку **`X-Session-Id`**. "
        "Если заголовок не передан, то создаётся новая сессия, "
        "её идентификатор возвращается в заголовке ответа `X-Session-Id`."
    ),
    responses={
        200: {
            "description": "Корзина получена (может быть пустой)",
            "content": {
                "application/json": {
                    "examples": {
                        "с_товарами": {
                            "summary": "Корзина с товарами",
                            "value": {
                                "data": {
                                    "items": [
                                        {
                                            "item_id": 1,
                                            "sku": "LX-LED-E27-9W",
                                            "name": "Лампа LED E27 9Вт",
                                            "quantity": 2,
                                            "unit_price": "89.00",
                                            "total_price": "178.00",
                                        }
                                    ],
                                    "subtotal": "178.00",
                                    "discount_amount": "0.00",
                                    "promo": None,
                                }
                            },
                        },
                        "пустая": {
                            "summary": "Пустая корзина",
                            "value": {
                                "data": {
                                    "items": [],
                                    "subtotal": "0.00",
                                    "discount_amount": "0.00",
                                    "promo": None,
                                }
                            },
                        },
                    }
                }
            },
        }
    },
)
async def get_cart(
    response: Response,
    x_session_id: Optional[str] = Header(
        None,
        alias="X-Session-Id",
        description="Идентификатор сессии корзины (UUID). При первом обращении генерируется автоматически",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    ),
    pool: asyncpg.Pool = Depends(get_pool),
):
    session_id, is_new = resolve_session(x_session_id)
    if is_new:
        response.headers["X-Session-Id"] = session_id

    rows = await pool.fetch(
        "SELECT id AS item_id, sku, name, quantity, unit_price, total_price "
        "FROM cart_items WHERE session_id = $1 ORDER BY added_at",
        session_id,
    )

    items = [record_to_dict(r) for r in rows]

    # subtotal всегда считаем через Decimal и нормализуем до 2 знаков
    subtotal = sum(Decimal(str(i["total_price"])) for i in items) if items else Decimal("0.00")
    subtotal_str = str(subtotal.quantize(Decimal("0.01")))

    return {
        "data": {
            "items": items,
            "subtotal": subtotal_str,
            "discount_amount": "0.00",
            "promo": None,
        }
    }


@router.post(
    "/items",
    status_code=200,
    response_model=CartItemAddedResponse,
    summary="Добавить товар в корзину",
    description=(
        "Добавляет товар в корзину или **увеличивает** количество, если товар уже есть. "
        "Перед добавлением проверяет наличие товара и остаток на складе через catalog-service. "
        "Цена фиксируется на момент добавления."
    ),
    responses={
        200: {"description": "Товар успешно добавлен в корзину"},
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
            "description": "Товар с таким SKU не найден в каталоге",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "product_not_found",
                        "message": "Товар не найден в каталоге",
                    }
                }
            },
        },
        503: {
            "description": "Сервис каталога недоступен. Повторите попытку позже",
            "content": {
                "application/json": {
                    "example": {
                        "error": "catalog_unavailable",
                        "message": "Не удалось получить информацию о товаре. Повторите попытку позже.",
                    }
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
        alias="X-Session-Id",
        description="Идентификатор сессии. Если не передан — создаётся автоматически",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    ),
    pool: asyncpg.Pool = Depends(get_pool),
    http: httpx.AsyncClient = Depends(get_http),
):
    session_id, is_new = resolve_session(x_session_id)
    if is_new:
        response.headers["X-Session-Id"] = session_id

    try:
        resp = await http.get(f"/api/v1/products/{body.sku}")
    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "catalog_unavailable",
                "message": "Не удалось получить информацию о товаре. Повторите попытку позже.",
            },
        )

    if resp.status_code == 404:
        raise HTTPException(
            status_code=404,
            detail={"error": "product_not_found", "message": "Товар не найден в каталоге"},
        )

    product = resp.json()["data"]

    existing = await pool.fetchrow(
        "SELECT quantity FROM cart_items WHERE session_id = $1 AND sku = $2",
        session_id,
        body.sku,
    )
    current_qty = existing["quantity"] if existing else 0
    new_qty = current_qty + body.quantity

    if new_qty > product["stock_quantity"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_stock",
                "message": f"Доступно только {product['stock_quantity']} шт.",
                "available": product["stock_quantity"],
            },
        )

    unit_price = Decimal(str(product["price"]))
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
        session_id,
        body.sku,
        product["name"],
        unit_price,
        new_qty,
        total_price,
    )

    return {"data": record_to_dict(row), "message": "Добавлено в корзину"}


@router.patch(
    "/items/{item_id}",
    response_model=CartItemUpdatedResponse,
    summary="Изменить количество товара в корзине",
    description=(
        "Устанавливает новое количество для позиции корзины. "
        "Значение **заменяет** текущее — не прибавляется. "
        "При изменении проверяется актуальный остаток на складе."
    ),
    responses={
        200: {"description": "Количество успешно обновлено"},
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
            "description": "Позиция с таким item_id не найдена в корзине",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "item_not_found",
                        "message": "Позиция не найдена в корзине",
                    }
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
        alias="X-Session-Id",
        description="Идентификатор сессии",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    ),
    pool: asyncpg.Pool = Depends(get_pool),
    http: httpx.AsyncClient = Depends(get_http),
):
    session_id, _ = resolve_session(x_session_id)

    item = await pool.fetchrow(
        "SELECT sku, unit_price FROM cart_items WHERE id = $1 AND session_id = $2",
        item_id,
        session_id,
    )
    if not item:
        raise HTTPException(
            status_code=404,
            detail={"error": "item_not_found", "message": "Позиция не найдена в корзине"},
        )

    product = await fetch_product(http, item["sku"])
    if product and body.quantity > product["stock_quantity"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_stock",
                "message": f"Доступно только {product['stock_quantity']} шт.",
                "available": product["stock_quantity"],
            },
        )

    total_price = Decimal(str(item["unit_price"])) * body.quantity

    row = await pool.fetchrow(
        "UPDATE cart_items "
        "SET quantity = $1, total_price = $2 "
        "WHERE id = $3 AND session_id = $4 "
        "RETURNING id AS item_id, quantity, total_price",
        body.quantity,
        total_price,
        item_id,
        session_id,
    )

    return {"data": record_to_dict(row), "message": "Количество обновлено"}


@router.delete(
    "/items/{item_id}",
    status_code=204,
    summary="Удалить позицию из корзины",
    description="Удаляет одну позицию из корзины по её `item_id`. Остальные позиции не затрагиваются.",
    responses={
        204: {"description": "Позиция успешно удалена"},
        404: {
            "description": "Позиция с таким item_id не найдена в корзине",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "item_not_found",
                        "message": "Позиция не найдена в корзине",
                    }
                }
            },
        },
    },
)
async def delete_item(
    item_id: int,
    x_session_id: Optional[str] = Header(
        None,
        alias="X-Session-Id",
        description="Идентификатор сессии",
        example="a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    ),
    pool: asyncpg.Pool = Depends(get_pool),
):
    session_id, _ = resolve_session(x_session_id)
    result = await pool.execute(
        "DELETE FROM cart_items WHERE id = $1 AND session_id = $2",
        item_id,
        session_id,
    )
    if result == "DELETE 0":
        raise HTTPException(
            status_code=404,
            detail={"error": "item_not_found", "message": "Позиция не найдена в корзине"},
        )