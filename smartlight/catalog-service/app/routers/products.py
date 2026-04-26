from asyncio import gather
from decimal import Decimal
from typing import Optional

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query

from app.database import get_pool
from app.schemas import (
    ErrorResponse,
    ProductCreate,
    ProductCreatedResponse,
    ProductDetailResponse,
    ProductListResponse,
    ProductUpdate,
    ProductUpdatedResponse,
    ValidationErrorResponse,
)
from shared.utils import record_to_dict
from app.constants import ErrorCode, StatusCode

router = APIRouter()

ALLOWED_PATCH_FIELDS = [
    "name", "description", "price", "old_price",
    "stock_quantity", "status", "category_id",
]


# GET /api/v1/products

@router.get(
    "",
    response_model=ProductListResponse,
    summary="Каталог товаров",
    description=(
        "Возвращает список товаров с фильтрацией и постраничной навигацией. "
        "Без фильтра **status** архивные товары не отображаются. "
        "Параметр **category** принимает slug категории из `/api/v1/categories`."
    ),
    responses={
        200: {"description": "Список товаров успешно получен"},
        400: {
            "description": "Некорректные параметры запроса",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "invalid_params",
                        "message": "Параметр limit должен быть от 1 до 100",
                    }
                }
            },
        },
    },
)
async def list_products(
    category: Optional[str] = Query(
        None,
        description="Slug категории для фильтрации. Возможные значения: `led`, `filament`, `smart`, `halogen`",
        example="led",
    ),
    status: Optional[str] = Query(
        None,
        description=(
            "Статус товара для фильтрации (только для admin). "
            "Возможные значения: `active`, `archived`, `out_of_stock`. "
            "Без этого параметра архивные товары не отображаются."
        ),
        example="active",
    ),
    page: int = Query(1, ge=1, description="Номер страницы (начиная с 1)", example=1),
    limit: int = Query(12, ge=1, le=100, description="Количество товаров на странице (от 1 до 100)", example=12),
    pool: asyncpg.Pool = Depends(get_pool),
):
    conditions: list[str] = []
    params: list = []

    if category:
        params.append(category)
        conditions.append(f"c.slug = ${len(params)}")

    if status:
        params.append(status)
        conditions.append(f"p.status = ${len(params)}")
    else:
        # В публичном каталоге архивные товары не показываем
        conditions.append("p.status != 'archived'")

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    total: int = await pool.fetchval(
        f"SELECT COUNT(*) FROM products p JOIN categories c ON p.category_id = c.id {where}",
        *params,
    )

    offset = (page - 1) * limit
    params += [limit, offset]

    rows = await pool.fetch(
        f"""
        SELECT p.id, p.sku,
               json_build_object('id', c.id, 'slug', c.slug, 'name', c.name) AS category,
               p.name, p.price, p.old_price, p.stock_quantity, p.status, p.created_at,
               (
                   SELECT url FROM product_images
                   WHERE product_id = p.id AND is_primary = TRUE
                   LIMIT 1
               ) AS primary_image
        FROM products p
        JOIN categories c ON p.category_id = c.id
        {where}
        ORDER BY p.id
        LIMIT ${len(params) - 1} OFFSET ${len(params)}
        """,
        *params,
    )

    return {
        "data": [record_to_dict(r) for r in rows],
        "meta": {
            "page":        page,
            "limit":       limit,
            "total":       total,
            "total_pages": -(-total // limit),
        },
    }


# GET /api/v1/products/{sku}

@router.get(
    "/{sku}",
    response_model=ProductDetailResponse,
    summary="Карточка товара",
    description=(
        "Возвращает полную информацию о товаре по SKU: "
        "характеристики, изображения, категорию. "
        "SKU — уникальный артикул в формате `LX-{тип}-{цоколь}-{мощность}`."
    ),
    responses={
        200: {"description": "Товар найден"},
        404: {
            "description": "Товар с таким SKU не существует",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "product_not_found",
                        "message": "Товар с указанным SKU не найден",
                    }
                }
            },
        },
    },
)
async def get_product(sku: str, pool: asyncpg.Pool = Depends(get_pool)):
    row = await pool.fetchrow(
        """
        SELECT p.id, p.sku,
               json_build_object('id', c.id, 'slug', c.slug, 'name', c.name) AS category,
               p.name, p.description, p.price, p.old_price,
               p.stock_quantity, p.status, p.created_at, p.updated_at
        FROM products p
        JOIN categories c ON p.category_id = c.id
        WHERE p.sku = $1
        """,
        sku,
    )
    if not row:
        raise HTTPException(status_code=404, detail={
            "error":   "product_not_found",
            "message": "Товар с указанным SKU не найден",
        })

    product = record_to_dict(row)
    pid = product["id"]

    # Атрибуты и изображения загружаем параллельно
    attrs, images = await gather(
        pool.fetch(
            "SELECT attr_key, attr_value, unit FROM product_attributes WHERE product_id = $1",
            pid,
        ),
        pool.fetch(
            """SELECT id, url, alt_text, is_primary, sort_order
               FROM product_images WHERE product_id = $1 ORDER BY sort_order""",
            pid,
        ),
    )

    product["attributes"] = [dict(a) for a in attrs]
    product["images"]     = [dict(i) for i in images]
    return {"data": product}


# POST /api/v1/products

@router.post(
    "",
    status_code=201,
    response_model=ProductCreatedResponse,
    summary="Создать товар",
    description=(
        "Создаёт новый товар в каталоге. "
        "SKU должен быть уникальным. "
        "Начальный статус — `active`. "
        "**Доступно только для администраторов** (авторизация добавляется в модуле 5)."
    ),
    responses={
        201: {"description": "Товар успешно создан"},
        400: {
            "description": "Ошибка валидации данных",
            "model": ValidationErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": ErrorCode.VALIDATION_ERROR,
                        "details": [{"field": "price", "message": "Цена должна быть > 0"}],
                    }
                }
            },
        },
        409: {
            "description": "Товар с таким SKU уже существует",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {
                        "error": "sku_already_exists",
                        "message": "Товар с таким SKU уже существует",
                    }
                }
            },
        },
    },
)
async def create_product(body: ProductCreate, pool: asyncpg.Pool = Depends(get_pool)):
    try:
        row = await pool.fetchrow(
            """
            INSERT INTO products
                (sku, category_id, name, description, price, old_price, stock_quantity)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, sku, status, created_at
            """,
            body.sku, body.category_id, body.name, body.description,
            body.price, body.old_price, body.stock_quantity,
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail={
            "error":   ErrorCode.SKU_ALREADY_EXISTS,
            "message": "Товар с таким SKU уже существует",
        })
    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(status_code=400, detail={
            "error":   "validation_error",
            "details": [{"field": "category_id", "message": "Категория не найдена"}],
        })

# PATCH /api/v1/products/{sku}

@router.patch(
    "/{sku}",
    response_model=ProductUpdatedResponse,
    summary="Обновить товар",
    description=(
        "Частичное обновление товара — передавайте только те поля, которые нужно изменить. "
        "Например, для обновления цены и остатка достаточно передать `price` и `stock_quantity`. "
        "**Доступно только для администраторов**."
    ),
    responses={
        200: {"description": "Товар успешно обновлён"},
        400: {
            "description": "Ошибка валидации или нет полей для обновления",
            "model": ErrorResponse,
        },
        404: {
            "description": "Товар не найден",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "product_not_found"}
                }
            },
        },
    },
)
async def update_product(
    sku: str,
    body: ProductUpdate,
    pool: asyncpg.Pool = Depends(get_pool),
):
    data = body.model_dump(exclude_none=True)
    updates: list[str] = []
    params: list = []

    for field in ALLOWED_PATCH_FIELDS:
        if field in data:
            params.append(data[field])
            updates.append(f"{field} = ${len(params)}")

    if not updates:
        raise HTTPException(status_code=400, detail={
            "error":   ErrorCode.VALIDATION_ERROR,
            "message": "Нет полей для обновления",
        })

    params.append(sku)
    try:
        row = await pool.fetchrow(
            f"""
            UPDATE products
            SET {', '.join(updates)}, updated_at = NOW()
            WHERE sku = ${len(params)}
            RETURNING sku, price, stock_quantity, status, updated_at
            """,
            *params,
        )
    except asyncpg.ForeignKeyViolationError:
        raise HTTPException(status_code=400, detail={
            "error":   ErrorCode.VALIDATION_ERROR,
            "details": [{"field": "category_id", "message": "Категория не найдена"}],
        })

    if not row:
        raise HTTPException(status_code=404, detail={"error": ErrorCode.PRODUCT_NOT_FOUND})

# DELETE /api/v1/products/{sku}

@router.delete(
    "/{sku}",
    status_code=204,
    summary="Удалить товар",
    description=(
        "Удаляет товар из каталога вместе со всеми атрибутами и изображениями (CASCADE). "
        "Операция необратима. "
        "**Доступно только для администраторов**."
    ),
    responses={
        204: {"description": "Товар успешно удалён"},
        404: {
            "description": "Товар не найден",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"error": "product_not_found"}
                }
            },
        },
    },
)
async def delete_product(sku: str, pool: asyncpg.Pool = Depends(get_pool)):
    result = await pool.execute("DELETE FROM products WHERE sku = $1", sku)
    if result == "DELETE 0":
        raise HTTPException(status_code=404, detail={"error": "product_not_found"})
