from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    MODE: str = "DEV"
    DOCS_USER: str = "docsadmin"
    DOCS_PASSWORD: str = "docssecret"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
