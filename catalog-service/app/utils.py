from datetime import datetime
from decimal import Decimal


# Конвертируем специфичные типы asyncpg в строки, пригодные для JSON.
def record_to_dict(record) -> dict:
    result = {}
    for key, value in dict(record).items():
        if isinstance(value, Decimal):
            result[key] = str(value)
        elif isinstance(value, datetime):
            result[key] = value.isoformat()
        else:
            result[key] = value
    return result
