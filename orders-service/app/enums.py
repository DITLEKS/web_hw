from enum import Enum


class OrderStatus(str, Enum):
    created     = "created"
    confirmed   = "confirmed"
    in_assembly = "in_assembly"
    shipped     = "shipped"
    delivered   = "delivered"
    cancelled   = "cancelled"


class DeliveryType(str, Enum):
    courier = "courier"
    cdek    = "cdek"
    pickup  = "pickup"


class PaymentMethod(str, Enum):
    card_online      = "card_online"
    cash_on_delivery = "cash_on_delivery"
    card_on_delivery = "card_on_delivery"


class PaymentStatus(str, Enum):
    pending  = "pending"
    paid     = "paid"
    refunded = "refunded"
    failed   = "failed"


class DiscountType(str, Enum):
    percent = "percent"
    fixed   = "fixed"
