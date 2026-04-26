from enum import Enum


class ProductStatus(str, Enum):
    active       = "active"
    archived     = "archived"
    out_of_stock = "out_of_stock"
