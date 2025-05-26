from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # ----- общие -----
    app_name: str = "Bruteforce-API"
    secret_key: str
    access_token_expire_minutes: int = 60

    # ----- База данных -----
    db_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'app.db'}"

    # ----- Celery / redislite -----
    redis_path: str = "memory://"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # вычисляемые свойства — НЕ валидируются Pydantic
    @property
    def broker_url(self) -> str:
        return self.redis_path

    @property
    def result_backend(self) -> str:
        return "rpc://"


@lru_cache
def get_settings() -> Settings:
    return Settings()
