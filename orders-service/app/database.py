import asyncpg
import httpx
from fastapi import Request
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5434/orders_db"
    catalog_service_url: str = "http://localhost:3001"
    port: int = 3002

    model_config = {"env_file": ".env"}


settings = Settings()


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=2,
        max_size=10,
    )


def create_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.catalog_service_url,
        timeout=5.0,
    )


# Достаём ресурсы из app.state — они создаются один раз при старте
def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http
