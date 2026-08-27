from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CONVENIA_",
    )

    api_key: str
    base_url: str = "https://public-api.convenia.com.br"
    timeout: float = 30.0
    page_size: int = 1000
    env: str = "prd"  # "dev" desabilita o bloqueio de 6h no dashboard


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
