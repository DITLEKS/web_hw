import asyncpg
import httpx
from fastapi import Request

from app.core.config import settings


async def create_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=settings.pool_min_size,
        max_size=settings.pool_max_size,
        command_timeout=settings.command_timeout,
    )


def create_http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url=settings.catalog_service_url,
        timeout=5.0,
    )


def get_pool(request: Request) -> asyncpg.Pool:
    return request.app.state.pool


def get_http(request: Request) -> httpx.AsyncClient:
    return request.app.state.http
