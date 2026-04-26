import asyncpg
from fastapi import APIRouter, Depends

from app.database import get_pool
from app.schemas import CategoriesResponse
from app.utils import record_to_dict

router = APIRouter()


@router.get(
    "",
    response_model=CategoriesResponse,
    summary="Список категорий товаров",
    description=(
        "Возвращает все категории каталога в порядке сортировки. "
        "Используется для построения навигационного меню и фильтров."
    ),
    responses={200: {"description": "Список категорий успешно получен"}},
)
async def list_categories(pool: asyncpg.Pool = Depends(get_pool)):
    rows = await pool.fetch(
        "SELECT id, slug, name, color_hex, sort_order FROM categories ORDER BY sort_order"
    )
    return {"data": [record_to_dict(r) for r in rows]}
