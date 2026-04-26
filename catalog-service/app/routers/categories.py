import asyncpg
from fastapi import APIRouter, Depends

from app.database import get_pool
from app.schemas import CategoryListResponse
from shared.utils import record_to_dict

router = APIRouter()


@router.get(
    "",
    response_model=CategoryListResponse,
    summary="Список всех категорий",
    description=(
        "Возвращает все категории товаров, отсортированные по полю `sort_order`. "
        "Значение `slug` используйтся как параметр `category` при фильтрации каталога товаров."
    ),
    responses={
        200: {
            "description": "Список категорий успешно получен",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {"id": 1, "slug": "led",      "name": "LED",      "color_hex": "#3B82F6", "sort_order": 0},
                            {"id": 2, "slug": "filament", "name": "Filament", "color_hex": "#F59E0B", "sort_order": 1},
                            {"id": 3, "slug": "smart",    "name": "Smart",    "color_hex": "#10B981", "sort_order": 2},
                            {"id": 4, "slug": "halogen",  "name": "Halogen",  "color_hex": "#EF4444", "sort_order": 3},
                        ]
                    }
                }
            },
        }
    },
)
async def list_categories(pool: asyncpg.Pool = Depends(get_pool)):
    rows = await pool.fetch(
        "SELECT id, slug, name, color_hex, sort_order FROM categories ORDER BY sort_order"
    )
    return {"data": [record_to_dict(r) for r in rows]}
