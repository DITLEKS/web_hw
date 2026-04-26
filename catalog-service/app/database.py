import asyncpg
from fastapi import Request
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5433/catalog_db"
    port: int = 3001

    model_config = {"env_file": ".env"}


settings = Settings()


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
    )


# Зависимость FastAPI — достаём пул из состояния приложения.
# Такой подход безопаснее глобальных переменных: пул явно
# привязан к жизненному циклу конкретного экземпляра приложения.
def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool
