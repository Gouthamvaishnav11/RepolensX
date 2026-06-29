from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    APP_NAME:    str  = "RepoLens X"
    DEBUG:       bool = True
    SECRET_KEY:  str  = "change-this-secret-key"
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000,http://localhost:80"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://repolens:repolens123@localhost:5432/repolensdb"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # ChromaDB
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001

    # GitHub
    GITHUB_TOKEN:       str = ""
    GITHUB_CLIENT_ID:   str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI:  str = "http://localhost:8080/api/auth/github/callback"

    # Ollama
    OLLAMA_BASE_URL:   str = "http://localhost:11434"
    OLLAMA_MODEL:      str = "mistral"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # JWT
    JWT_SECRET_KEY:                  str = "jwt-secret-change-this"
    JWT_ALGORITHM:                   str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS:   int = 30

    # Payments
    RAZORPAY_KEY_ID:     str = ""
    RAZORPAY_KEY_SECRET: str = ""

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        extra    = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
