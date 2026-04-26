from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import create_http_client, create_pool
from app.routers import cart, orders


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Пул БД и HTTP-клиент создаём один раз при старте
    app.state.pool = await create_pool()
    app.state.http = create_http_client()
    yield
    await app.state.pool.close()
    await app.state.http.aclose()


app = FastAPI(
    title="SmartLight — Orders Service",
    description=(
        "## Микросервис управления заказами\n\n"
        "Обрабатывает корзину покупателя и оформление заказов. "
        "Для проверки остатков и цен обращается в **catalog-service**.\n\n"
        "### Базовый URL\n"
        "- Docker: `http://orders-service:3002`\n"
        "- Локально: `http://localhost:3002`\n\n"
        "### Идентификация сессии\n"
        "Корзина привязана к сессии через заголовок **`X-Session-Id`** (UUID). "
        "Если заголовок не передан — сервер автоматически создаёт новую сессию "
        "и возвращает её ID в заголовке ответа `X-Session-Id`.\n\n"
        "### Статусы заказа\n"
        "| Статус | Описание |\n"
        "|---|---|\n"
        "| `created` | Заказ создан, ожидает подтверждения |\n"
        "| `confirmed` | Подтверждён оператором |\n"
        "| `in_assembly` | Собирается на складе |\n"
        "| `shipped` | Передан в службу доставки |\n"
        "| `delivered` | Доставлен покупателю |\n"
        "| `cancelled` | Отменён |\n\n"
        "### Аутентификация\n"
        "Пока не требуется — авторизация будет добавлена в модуле 5."
    ),
    version="1.0.0",
    lifespan=lifespan,
    contact={"name": "SmartLight Dev Team"},
    license_info={"name": "Proprietary"},
)

app.include_router(cart.router,   prefix="/api/v1/cart",   tags=["Корзина"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["Заказы"])


@app.get("/health", tags=["Служебные"], summary="Проверка работоспособности сервиса")
async def health():
    """Возвращает статус сервиса. Используется Docker healthcheck и мониторингом."""
    return {"status": "ok", "service": "orders-service"}
