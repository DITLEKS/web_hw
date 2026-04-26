"""
Pydantic-схемы для catalog-service.

Все поля задокументированы по описаниям из ТЗ — они отображаются
в Swagger UI как description, а examples попадают прямо в форму.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

# Категории
    id: int = Field(..., description="Уникальный идентификатор категории (автоинкремент)", example=1)
    slug: str = Field(
        ...,
        description="URL-идентификатор категории (уникальный)",
        example="led",
    )
    name: str = Field(..., description="Название категории", example="LED")
    color_hex: str = Field(
        ...,
        description="HEX-код цвета для отображения в UI",
        example="#3B82F6",
    )
    sort_order: int = Field(
        ...,
        description="Порядок сортировки категорий в меню (0 — первая)",
        example=0,
    )

    model_config = {"from_attributes": True}


# Атрибуты и изображения
    attr_key: str = Field(
        ...,
        description="Ключ атрибута товара",
        example="wattage",
    )
    attr_value: str = Field(
        ...,
        description="Значение атрибута",
        example="9",
    )
    unit: Optional[str] = Field(
        None,
        description="Единица измерения: Вт, лм, K, ч, мес или null",
        example="Вт",
    )


class ProductImageOut(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор изображения", example=1)
    url: str = Field(
        ...,
        description="URL изображения на CDN",
        example="https://cdn.smartlight.ru/products/lx-led-e27-9w.jpg",
    )
    alt_text: Optional[str] = Field(
        None,
        description="Альтернативный текст для accessibility",
        example="Лампа LED E27 9Вт",
    )
    is_primary: bool = Field(
        ...,
        description="Флаг основного изображения — отображается первым в карточке",
        example=True,
    )
    sort_order: int = Field(
        ...,
        description="Порядок сортировки изображений (0 — первое)",
        example=0,
    )


# Товары — список
    id: int = Field(..., description="Уникальный идентификатор товара", example=1)
    sku: str = Field(
        ...,
        description="Артикул товара (уникальный). Формат: LX-{категория}-{цоколь}-{мощность}",
        example="LX-LED-E27-9W",
    )
    category: CategoryBriefOut = Field(..., description="Категория товара")
    name: str = Field(
        ...,
        description="Полное название товара",
        example="Лампа светодиодная груша 9 Вт E27",
    )
    price: str = Field(
        ...,
        description="Текущая цена товара в рублях",
        example="89.00",
    )
    old_price: Optional[str] = Field(
        None,
        description="Старая цена до скидки в рублях (null — скидки нет)",
        example="99.00",
    )
    stock_quantity: int = Field(
        ...,
        description="Количество единиц товара на складе",
        example=150,
    )
    status: str = Field(
        ...,
        description="Статус товара: active — активен, archived — архивирован, out_of_stock — нет в наличии",
        example="active",
    )
    primary_image: Optional[str] = Field(
        None,
        description="URL основного изображения товара (null — изображений нет)",
        example="https://cdn.smartlight.ru/products/lx-led-e27-9w.jpg",
    )


class PaginationMeta(BaseModel):
    page: int = Field(..., description="Текущая страница", example=1)
    limit: int = Field(..., description="Количество записей на странице", example=12)
    total: int = Field(..., description="Общее количество товаров по фильтру", example=20)
    total_pages: int = Field(..., description="Всего страниц", example=2)


# Товар — карточка
    description: Optional[str] = Field(
        None,
        description="Подробное описание товара",
        example="Энергосберегающая LED лампа с цоколем E27. Мощность 9 Вт заменяет лампу накаливания 75 Вт.",
    )
    created_at: str = Field(..., description="Дата и время создания товара (ISO 8601)", example="2026-01-15T10:00:00+00:00")
    updated_at: str = Field(..., description="Дата и время последнего обновления (ISO 8601)", example="2026-04-12T15:35:00+00:00")
    attributes: list[ProductAttributeOut] = Field(
        default_factory=list,
        description="Технические характеристики товара",
    )
    images: list[ProductImageOut] = Field(
        default_factory=list,
        description="Изображения товара, отсортированные по sort_order",
    )


# Запросы на создание / обновление
    sku: str = Field(
        ...,
        description="Артикул товара. Должен быть уникальным. Формат: LX-{тип}-{цоколь}-{мощность}",
        example="LX-LED-E27-9W",
        min_length=3,
        max_length=50,
    )
    category_id: int = Field(
        ...,
        description="ID категории из таблицы categories",
        example=1,
        ge=1,
    )
    name: str = Field(
        ...,
        description="Полное название товара",
        example="Лампа светодиодная груша 9 Вт E27",
        min_length=2,
        max_length=255,
    )
    description: Optional[str] = Field(
        None,
        description="Подробное описание товара (необязательно)",
        example="Энергосберегающая LED лампа с цоколем E27.",
    )
    price: Decimal = Field(
        ...,
        description="Цена товара в рублях. Должна быть больше 0",
        example=89.00,
        gt=0,
    )
    old_price: Optional[Decimal] = Field(
        None,
        description="Старая цена до скидки. Передайте null если скидки нет",
        example=99.00,
    )
    stock_quantity: int = Field(
        0,
        description="Количество товара на складе. По умолчанию 0",
        example=150,
        ge=0,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "sku": "LX-LED-E27-9W",
                "category_id": 1,
                "name": "Лампа светодиодная груша 9 Вт E27",
                "description": "Энергосберегающая LED лампа с цоколем E27.",
                "price": 89.00,
                "old_price": None,
                "stock_quantity": 150,
            }
        }
    }


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        description="Новое название товара",
        example="Лампа светодиодная груша 9 Вт E27 (обновлённая)",
        min_length=2,
        max_length=255,
    )
    description: Optional[str] = Field(
        None,
        description="Новое описание товара",
        example="Обновлённое описание.",
    )
    price: Optional[Decimal] = Field(
        None,
        description="Новая цена. Должна быть больше 0",
        example=99.00,
        gt=0,
    )
    old_price: Optional[Decimal] = Field(
        None,
        description="Старая цена (для отображения зачёркнутой цены). Передайте null чтобы убрать",
        example=89.00,
    )
    stock_quantity: Optional[int] = Field(
        None,
        description="Новый остаток на складе",
        example=200,
        ge=0,
    )
    status: Optional[str] = Field(
        None,
        description="Новый статус товара: active — активен, archived — архивирован, out_of_stock — нет в наличии",
        example="active",
    )
    category_id: Optional[int] = Field(
        None,
        description="ID новой категории",
        example=2,
        ge=1,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "price": 99.00,
                "stock_quantity": 200,
            }
# Ответы на создание
    id: int = Field(..., description="ID созданного товара", example=21)
    sku: str = Field(..., description="Артикул созданного товара", example="LX-LED-E27-9W")
    status: str = Field(..., description="Начальный статус", example="active")
    created_at: str = Field(..., example="2026-04-12T15:30:00+00:00")


class ProductCreatedResponse(BaseModel):
    data: ProductCreatedData
    message: str = Field(..., example="Товар успешно создан")


class ProductUpdatedData(BaseModel):
    sku: str = Field(..., example="LX-LED-E27-9W")
    price: str = Field(..., example="99.00")
    stock_quantity: int = Field(..., example=200)
    status: str = Field(..., example="active")
    updated_at: str = Field(..., example="2026-04-12T15:35:00+00:00")


# Ошибки
    error: str = Field(..., description="Машиночитаемый код ошибки", example="product_not_found")
    message: Optional[str] = Field(None, description="Человекочитаемое описание ошибки", example="Товар с указанным SKU не найден")


class ValidationDetail(BaseModel):
    field: str = Field(..., example="price")
    message: str = Field(..., example="Цена должна быть > 0")


class ValidationErrorResponse(BaseModel):
    error: str = Field("validation_error", example="validation_error")
    details: list[ValidationDetail]
