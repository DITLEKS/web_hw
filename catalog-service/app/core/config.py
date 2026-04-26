from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://postgres:postgres@localhost:5433/catalog_db"
    port: int = 3001
    pool_min_size: int = 2
    pool_max_size: int = 10
    command_timeout: int = 30

    model_config = {"env_file": ".env"}


settings = Settings()
