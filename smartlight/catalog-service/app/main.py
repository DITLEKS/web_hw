from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.database import create_pool
from app.routers import categories, products


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Пул соединений создаём один раз при старте
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()


app = FastAPI(
    title="SmartLight — Catalog Service",
    description=(
        "## Микросервис управления товарами\n\n"
        "Отвечает за каталог товаров, категории, атрибуты и изображения.\n\n"
        "### Базовый URL\n"
        "- Docker: `http://catalog-service:3001`\n"
        "- Локально: `http://localhost:3001`\n\n"
        "### Аутентификация\n"
        "Пока не требуется — авторизация будет добавлена в модуле 5.\n\n"
        "### SKU-формат\n"
        "Артикул товара строится по схеме `LX-{ТИП}-{ЦОКОЛЬ}-{МОЩНОСТЬ}`, "
        "например `LX-LED-E27-9W`."
    ),
    version="1.0.0",
    lifespan=lifespan,
    contact={"name": "SmartLight Dev Team"},
    license_info={"name": "Proprietary"},
)

app.include_router(categories.router, prefix="/api/v1/categories", tags=["Категории"])
app.include_router(products.router,   prefix="/api/v1/products",   tags=["Товары"])


@app.get("/health", tags=["Служебные"], summary="Проверка работоспособности сервиса")
async def health():
    """Возвращает статус сервиса. Используется Docker healthcheck и мониторингом."""
    return {"status": "ok", "service": "catalog-service"}
