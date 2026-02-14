from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    DATABASE_URL: str = "sqlite:///./data/stopmonkey.db"
    UPLOAD_DIR: str = "./uploads"
    ADMIN_USERNAME: str = "hector"
    ADMIN_PASSWORD: str = "changeme"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
