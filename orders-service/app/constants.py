from enum import Enum
from decimal import Decimal


class ErrorCode(str, Enum):
    """Машиночитаемые коды ошибок."""
    PRODUCT_NOT_FOUND = "product_not_found"
    INSUFFICIENT_STOCK = "insufficient_stock"
    CART_EMPTY = "cart_empty"
    PROMO_INVALID = "promo_invalid"
    ITEM_NOT_FOUND = "item_not_found"
    SESSION_REQUIRED = "session_required"
    SKU_ALREADY_EXISTS = "sku_already_exists"
    VALIDATION_ERROR = "validation_error"
    ORDER_NOT_FOUND = "order_not_found"


class DeliveryType(str, Enum):
    """Типы доставки с ценами."""
    COURIER = "courier"
    CDEK = "cdek"
    PICKUP = "pickup"


DELIVERY_COSTS: dict[DeliveryType, Decimal] = {
    DeliveryType.COURIER: Decimal("300"),
    DeliveryType.CDEK: Decimal("250"),
    DeliveryType.PICKUP: Decimal("0"),
}


class StatusCode:
    """HTTP статусы."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    NOT_FOUND = 404
    CONFLICT = 409


class DiscountType(str, Enum):
    PERCENT = "percent"
    FIXED = "fixed"