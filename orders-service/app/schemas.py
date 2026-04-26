"""
Pydantic-схемы для orders-service.

Описания полей соответствуют ТЗ — таблицам orders, order_items,
order_status_history, cart_items, promo_codes.
"""
from __future__ import annotations

from typing import Optional

# Корзина
    item_id: int = Field(..., description="Идентификатор позиции в корзине", example=1)
    sku: str = Field(
        ...,
        description="Артикул товара (берётся из catalog-service)",
        example="LX-LED-E27-9W",
    )
    name: str = Field(
        ...,
        description="Название товара на момент добавления в корзину",
        example="Лампа светодиодная груша 9 Вт E27",
    )
    quantity: int = Field(..., description="Количество единиц товара", example=2)
    unit_price: str = Field(..., description="Цена за единицу товара в рублях", example="89.00")
    total_price: str = Field(..., description="Итоговая стоимость позиции (unit_price × quantity)", example="178.00")


class CartOut(BaseModel):
    items: list[CartItemOut] = Field(..., description="Список позиций в корзине")
    subtotal: str = Field(..., description="Сумма всех товаров в корзине до скидки и доставки", example="178.00")
    discount_amount: str = Field(..., description="Сумма скидки по промокоду (0.00 если промокод не применён)", example="0.00")
    promo: Optional[str] = Field(None, description="Применённый промокод (null если не применён)", example=None)


class CartResponse(BaseModel):
    data: CartOut


class AddItemRequest(BaseModel):
    sku: str = Field(
        ...,
        description="Артикул товара из каталога",
        example="LX-LED-E27-9W",
    )
    quantity: int = Field(
        1,
        description="Количество единиц для добавления. Суммируется с уже имеющимся количеством в корзине",
        example=2,
        ge=1,
    )

    model_config = {
        "json_schema_extra": {
            "example": {"sku": "LX-LED-E27-9W", "quantity": 2}
        }
    }


class UpdateItemRequest(BaseModel):
    quantity: int = Field(
        ...,
        description="Новое количество товара (заменяет текущее, не прибавляется)",
        example=3,
        ge=1,
    )

    model_config = {
        "json_schema_extra": {
            "example": {"quantity": 3}
        }
    }


class CartItemAddedData(BaseModel):
    item_id: int = Field(..., example=1)
    sku: str = Field(..., example="LX-LED-E27-9W")
    quantity: int = Field(..., example=2)
    total_price: str = Field(..., example="178.00")


class CartItemAddedResponse(BaseModel):
    data: CartItemAddedData
    message: str = Field(..., example="Добавлено в корзину")


class CartItemUpdatedData(BaseModel):
    item_id: int = Field(..., example=1)
    quantity: int = Field(..., example=3)
    total_price: str = Field(..., example="267.00")


# Заказы
    delivery_type: str = Field(
        "courier",
        description=(
            "Тип доставки:\n"
            "- `courier` — курьерская доставка, стоимость 300 ₽\n"
            "- `cdek` — доставка СДЭК, стоимость 250 ₽\n"
            "- `pickup` — самовывоз, бесплатно"
        ),
        example="courier",
        pattern="^(courier|pickup|cdek)$",
    )
    delivery_city: Optional[str] = Field(
        None,
        description="Город доставки. Обязателен для типов `courier` и `cdek`",
        example="Москва",
        max_length=100,
    )
    delivery_street: Optional[str] = Field(
        None,
        description="Адрес доставки: улица, дом, квартира",
        example="ул. Ленина, д. 1, кв. 42",
        max_length=255,
    )
    delivery_zip: Optional[str] = Field(
        None,
        description="Почтовый индекс (6 цифр для РФ)",
        example="101000",
        max_length=10,
    )
    payment_method: str = Field(
        "card_online",
        description=(
            "Способ оплаты:\n"
            "- `card_online` — оплата картой онлайн\n"
            "- `cash_on_delivery` — наличными при получении\n"
            "- `card_on_delivery` — картой при получении"
        ),
        example="card_online",
        pattern="^(card_online|cash_on_delivery|card_on_delivery)$",
    )
    promo_code: Optional[str] = Field(
        None,
        description="Промокод для получения скидки. Доступные промокоды: SALE20, WELCOME, SMART15",
        example="SALE20",
        max_length=50,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "delivery_type": "courier",
                "delivery_city": "Москва",
                "delivery_street": "ул. Ленина, д. 1, кв. 42",
                "delivery_zip": "101000",
                "payment_method": "card_online",
                "promo_code": None,
            }
        }
    }


class OrderCreatedData(BaseModel):
    order_number: str = Field(
        ...,
        description="Уникальный номер заказа. Формат: LX-YYYYMMDD-NNNN",
        example="LX-20260412-0001",
    )
    status: str = Field(..., description="Начальный статус заказа", example="created")
    subtotal: str = Field(..., description="Сумма товаров без скидки и доставки", example="178.00")
    discount_amount: str = Field(..., description="Сумма скидки по промокоду", example="0.00")
    delivery_cost: str = Field(..., description="Стоимость доставки", example="300.00")
    total_amount: str = Field(..., description="Итоговая сумма к оплате", example="478.00")
    payment_method: str = Field(..., example="card_online")
    payment_status: str = Field(
        ...,
        description="Статус оплаты: pending — ожидает, paid — оплачен, refunded — возврат, failed — ошибка",
        example="pending",
    )


class OrderCreatedResponse(BaseModel):
    data: OrderCreatedData
    message: str = Field(..., example="Заказ создан")


class OrderListItemOut(BaseModel):
    order_number: str = Field(..., description="Уникальный номер заказа", example="LX-20260412-0001")
    status: str = Field(
        ...,
        description="Текущий статус: created, confirmed, in_assembly, shipped, delivered, cancelled",
        example="confirmed",
    )
    total_amount: str = Field(..., description="Итоговая сумма заказа", example="478.00")
    items_count: int = Field(..., description="Количество позиций в заказе", example=2)
    created_at: str = Field(..., description="Дата и время создания (ISO 8601)", example="2026-04-12T15:00:00+00:00")


class OrderListMeta(BaseModel):
    page: int = Field(..., example=1)
    limit: int = Field(..., example=10)
    total: int = Field(..., description="Общее количество заказов", example=1)


class OrderListResponse(BaseModel):
    data: list[OrderListItemOut]
    meta: OrderListMeta


class OrderItemOut(BaseModel):
    sku: str = Field(..., description="Артикул товара на момент заказа", example="LX-LED-E27-9W")
    name: str = Field(..., description="Название товара на момент заказа", example="Лампа светодиодная груша 9 Вт E27")
    quantity: int = Field(..., description="Заказанное количество", example=2)
    unit_price: str = Field(..., description="Цена за единицу на момент заказа", example="89.00")
    total_price: str = Field(..., description="Итоговая стоимость позиции", example="178.00")


class StatusHistoryItemOut(BaseModel):
    status: str = Field(
        ...,
        description="Статус, в который перешёл заказ",
        example="created",
    )
    changed_at: str = Field(..., description="Дата и время изменения статуса (ISO 8601)", example="2026-04-12T15:00:00+00:00")
    comment: Optional[str] = Field(None, description="Комментарий к изменению статуса", example="Заказ создан")


class OrderDetailOut(BaseModel):
    order_number: str = Field(..., example="LX-20260412-0001")
    status: str = Field(
        ...,
        description="Текущий статус заказа: created, confirmed, in_assembly, shipped, delivered, cancelled",
        example="in_assembly",
    )
    delivery_type: str = Field(
        ...,
        description="Тип доставки: courier, pickup, cdek",
        example="courier",
    )
    delivery_city: Optional[str] = Field(None, description="Город доставки", example="Москва")
    delivery_street: Optional[str] = Field(None, description="Улица, дом, квартира", example="ул. Ленина, д. 1, кв. 42")
    delivery_zip: Optional[str] = Field(None, description="Почтовый индекс", example="101000")
    subtotal: str = Field(..., description="Сумма товаров без скидки и доставки", example="178.00")
    discount_amount: str = Field(..., description="Сумма скидки", example="0.00")
    delivery_cost: str = Field(..., description="Стоимость доставки", example="300.00")
    total_amount: str = Field(..., description="Итоговая сумма", example="478.00")
    payment_method: str = Field(..., example="card_online")
    payment_status: str = Field(
        ...,
        description="Статус оплаты: pending, paid, refunded, failed",
        example="paid",
    )
    tracking_number: Optional[str] = Field(
        None,
        description="Трек-номер отправления (появляется после передачи в службу доставки)",
        example=None,
    )
    promo_code: Optional[str] = Field(
        None,
        description="Применённый промокод (null если не использовался)",
        example=None,
    )
    items: list[OrderItemOut] = Field(..., description="Позиции заказа")
    status_history: list[StatusHistoryItemOut] = Field(..., description="История изменений статуса заказа")


# Ошибки
    error: str = Field(..., description="Машиночитаемый код ошибки", example="cart_empty")
    message: Optional[str] = Field(None, description="Человекочитаемое описание ошибки")
    available: Optional[int] = Field(None, description="Доступный остаток (только для insufficient_stock)", example=5)
