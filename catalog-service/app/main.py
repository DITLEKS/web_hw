from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_pool


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()


tags_metadata = [
    {
        "name": "Категории",
        "description": (
            "Справочник категорий товаров. "
            "Используйте `slug` категории как значение параметра `category` "
            "при запросе каталога товаров."
        ),
    },
    {
        "name": "Товары",
        "description": (
            "Управление каталогом товаров: просмотр, создание, редактирование и архивация. "
            "Удаление реализовано как **soft delete** — товар получает статус `archived` "
            "и перестаёт отображаться в публичном каталоге без физического удаления из БД.\n\n"
            "**Статусы товара:**\n"
            "- `active` — доступен для покупки\n"
            "- `out_of_stock` — нет в наличии\n"
            "- `archived` — скрыт из каталога"
        ),
    },
    {
        "name": "Служебные",
        "description": "Health check и проверка доступности сервиса.",
    },
]

app = FastAPI(
    title="SmartLight — Сервис управления товарами",
    description=(
        "## Микросервис каталога товаров\n\n"
        "Предоставляет API для управления ассортиментом интернет-магазина умных светильников SmartLight.\n\n"
        "### Базовый URL\n"
        "- Docker: `http://catalog-service:3001`\n"
        "- Локально: `http://localhost:3001`\n\n"
        "### Аутентификация\n"
        "Методы чтения (`GET`) публичны. "
        "Методы записи (`POST`, `PATCH`, `DELETE`) требуют JWT-токена администратора "
        "(авторизация добавляется в модуле 5).\n\n"
        "### Формат ошибок\n"
        "```json\n"
        "{\n"
        "  \"error\": \"машиночитаемый_код\",\n"
        "  \"message\": \"Человекочитаемое описание ошибки\"\n"
        "}\n"
        "```"
    ),
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
    contact={"name": "SmartLight Dev Team"},
    license_info={"name": "Proprietary"},
)

from app.routers import categories, products  # noqa: E402

app.include_router(categories.router, prefix="/api/v1/categories", tags=["Категории"])
app.include_router(products.router,   prefix="/api/v1/products",   tags=["Товары"])


@app.get("/health", tags=["Служебные"], summary="Проверка работоспособности сервиса")
async def health():
    """Возвращает статус `ok` если сервис запущен. Используется Docker healthcheck."""
    return {"status": "ok", "service": "catalog-service"}
