from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import create_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()

tags_metadata = [
    {"name": "Категории", "description": "Справочник категорий товаров."},
    {"name": "Товары", "description": "Управление каталогом товаров."},
    {"name": "Служебные", "description": "Health check и проверка доступности сервиса."},
]

app = FastAPI(
    title="SmartLight — Сервис управления товарами",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=tags_metadata,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.routers import categories, products

app.include_router(categories.router, prefix="/api/v1/categories", tags=["Категории"])
app.include_router(products.router,   prefix="/api/v1/products",   tags=["Товары"])

@app.get("/health", tags=["Служебные"])
async def health():
    return {"status": "ok", "service": "catalog-service"}
