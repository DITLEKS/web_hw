from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.enums import DeliveryType, OrderStatus, PaymentMethod, PaymentStatus


# Корзина

class CartItemOut(BaseModel):
    item_id:     int = Field(..., description="Идентификатор позиции в корзине", example=1)
    sku:         str = Field(..., description="Артикул товара", example="LX-LED-E27-9W")
    name:        str = Field(..., description="Название товара на момент добавления", example="Лампа светодиодная груша 9 Вт E27")
    quantity:    int = Field(..., description="Количество единиц товара", example=2)
    unit_price:  str = Field(..., description="Цена за единицу товара в рублях", example="89.00")
    total_price: str = Field(..., description="Итоговая стоимость позиции (unit_price × quantity)", example="178.00")


class CartOut(BaseModel):
    items:           list[CartItemOut] = Field(..., description="Список позиций в корзине")
    subtotal:        str               = Field(..., description="Сумма всех товаров до скидки и доставки", example="178.00")
    discount_amount: str               = Field(..., description="Сумма скидки по промокоду (0.00 если промокод не применён)", example="0.00")
    promo:           Optional[str]     = Field(None, description="Применённый промокод. null если промокод не применён")


class CartResponse(BaseModel):
    data: CartOut


class AddItemRequest(BaseModel):
    sku:      str = Field(..., description="Артикул товара из каталога", example="LX-LED-E27-9W")
    quantity: int = Field(1, description="Количество товара. Прибавляется к уже имеющемуся в корзине", example=2, ge=1)

    model_config = {
        "json_schema_extra": {"example": {"sku": "LX-LED-E27-9W", "quantity": 2}}
    }


class UpdateItemRequest(BaseModel):
    quantity: int = Field(..., description="Новое количество товара. Заменяет текущее (не прибавляется)", example=3, ge=1)

    model_config = {
        "json_schema_extra": {"example": {"quantity": 3}}
    }


class CartItemAddedData(BaseModel):
    item_id:     int = Field(..., example=1)
    sku:         str = Field(..., example="LX-LED-E27-9W")
    quantity:    int = Field(..., example=2)
    total_price: str = Field(..., example="178.00")


class CartItemAddedResponse(BaseModel):
    data:    CartItemAddedData
    message: str = Field(..., example="Добавлено в корзину")


class CartItemUpdatedData(BaseModel):
    item_id:     int = Field(..., example=1)
    quantity:    int = Field(..., example=3)
    total_price: str = Field(..., example="267.00")


class CartItemUpdatedResponse(BaseModel):
    data:    CartItemUpdatedData
    message: str = Field(..., example="Количество обновлено")


# Заказы

class CreateOrderRequest(BaseModel):
    delivery_type:   DeliveryType   = Field(
        DeliveryType.courier,
        description=(
            "Тип доставки:\n"
            "- `courier` — курьерская доставка, стоимость **300 ₽**\n"
            "- `cdek` — доставка СДЭК, стоимость **250 ₽**\n"
            "- `pickup` — самовывоз, **бесплатно**"
        ),
        example=DeliveryType.courier,
    )
    delivery_city:   Optional[str]  = Field(
        None,
        description="Город доставки. **Обязателен** при типе `courier` или `cdek`",
        example="Москва",
        max_length=100,
    )
    delivery_street: Optional[str]  = Field(
        None,
        description="Улица, дом, квартира. **Обязателен** при типе `courier` или `cdek`",
        example="ул. Ленина, д. 1, кв. 42",
        max_length=255,
    )
    delivery_zip:    Optional[str]  = Field(
        None,
        description="Почтовый индекс (6 цифр для адресов РФ)",
        example="101000",
        max_length=10,
    )
    payment_method:  PaymentMethod  = Field(
        PaymentMethod.card_online,
        description=(
            "Способ оплаты:\n"
            "- `card_online` — оплата картой онлайн\n"
            "- `cash_on_delivery` — наличными при получении\n"
            "- `card_on_delivery` — картой при получении"
        ),
        example=PaymentMethod.card_online,
    )
    promo_code:      Optional[str]  = Field(
        None,
        description="Промокод для получения скидки. Доступные для тестирования: `SALE20`, `WELCOME`, `SMART15`",
        example="SALE20",
        max_length=50,
    )

    @model_validator(mode="after")
    def validate_delivery_address(self) -> "CreateOrderRequest":
        if self.delivery_type in (DeliveryType.courier, DeliveryType.cdek):
            if not self.delivery_city:
                raise ValueError("delivery_city обязателен для типов доставки courier и cdek")
            if not self.delivery_street:
                raise ValueError("delivery_street обязателен для типов доставки courier и cdek")
        return self

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
    order_number:    str           = Field(..., description="Номер заказа в формате LX-YYYYMMDD-NNNN", example="LX-20260412-0001")
    status:          OrderStatus   = Field(..., description="Начальный статус заказа", example=OrderStatus.created)
    subtotal:        str           = Field(..., description="Сумма товаров без скидки и доставки", example="178.00")
    discount_amount: str           = Field(..., description="Сумма скидки по промокоду", example="0.00")
    delivery_cost:   str           = Field(..., description="Стоимость доставки", example="300.00")
    total_amount:    str           = Field(..., description="Итоговая сумма к оплате", example="478.00")
    payment_method:  PaymentMethod = Field(..., example=PaymentMethod.card_online)
    payment_status:  PaymentStatus = Field(..., example=PaymentStatus.pending)


class OrderCreatedResponse(BaseModel):
    data:    OrderCreatedData
    message: str = Field(..., example="Заказ создан")


class OrderListItemOut(BaseModel):
    order_number: str         = Field(..., example="LX-20260412-0001")
    status:       OrderStatus = Field(..., example=OrderStatus.confirmed)
    total_amount: str         = Field(..., example="478.00")
    items_count:  int         = Field(..., description="Количество позиций в заказе", example=2)
    created_at:   str         = Field(..., example="2026-04-12T15:00:00+00:00")


class OrderListMeta(BaseModel):
    page:  int = Field(..., example=1)
    limit: int = Field(..., example=10)
    total: int = Field(..., description="Общее количество заказов", example=1)


class OrderListResponse(BaseModel):
    data: list[OrderListItemOut]
    meta: OrderListMeta


class OrderItemOut(BaseModel):
    sku:         str = Field(..., example="LX-LED-E27-9W")
    name:        str = Field(..., example="Лампа светодиодная груша 9 Вт E27")
    quantity:    int = Field(..., example=2)
    unit_price:  str = Field(..., example="89.00")
    total_price: str = Field(..., example="178.00")


class StatusHistoryItemOut(BaseModel):
    status:     str           = Field(..., example="created")
    changed_at: str           = Field(..., example="2026-04-12T15:00:00+00:00")
    comment:    Optional[str] = Field(None, example="Заказ создан")


class OrderDetailOut(BaseModel):
    order_number:    str                      = Field(..., example="LX-20260412-0001")
    status:          OrderStatus              = Field(..., example=OrderStatus.in_assembly)
    delivery_type:   DeliveryType             = Field(..., example=DeliveryType.courier)
    delivery_city:   Optional[str]            = Field(None, example="Москва")
    delivery_street: Optional[str]            = Field(None, example="ул. Ленина, д. 1, кв. 42")
    delivery_zip:    Optional[str]            = Field(None, example="101000")
    subtotal:        str                      = Field(..., example="178.00")
    discount_amount: str                      = Field(..., example="0.00")
    delivery_cost:   str                      = Field(..., example="300.00")
    total_amount:    str                      = Field(..., example="478.00")
    payment_method:  PaymentMethod            = Field(..., example=PaymentMethod.card_online)
    payment_status:  PaymentStatus            = Field(..., example=PaymentStatus.paid)
    promo_code:      Optional[str]            = Field(None, description="Применённый промокод")
    items:           list[OrderItemOut]       = Field(..., description="Позиции заказа")
    status_history:  list[StatusHistoryItemOut] = Field(..., description="История изменений статуса")


class OrderDetailResponse(BaseModel):
    data: OrderDetailOut


class ErrorResponse(BaseModel):
    error:   str = Field(..., description="Машиночитаемый код ошибки", example="order_not_found")
    message: str = Field(..., description="Человекочитаемое описание ошибки", example="Заказ с указанным номером не найден")
