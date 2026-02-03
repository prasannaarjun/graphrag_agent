"""
Application configuration using Pydantic Settings.
Loads from environment variables and .env file.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = Field(default="GraphRAG Agent", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Groq LLM Configuration
    groq_api_key: str = Field(..., validation_alias="GROQ_API_KEY")

    # Neo4j Configuration
    neo4j_uri: str = Field(default="bolt://localhost:7687", validation_alias="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", validation_alias="NEO4J_USER")
    neo4j_password: str = Field(..., validation_alias="NEO4J_PASSWORD")

    # PostgreSQL + pgvector Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/graphrag",
        validation_alias="DATABASE_URL",
    )

    # MinIO Configuration
    minio_endpoint: str = Field(default="localhost:9000", validation_alias="MINIO_ENDPOINT")
    minio_access_key: str = Field(..., validation_alias="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(..., validation_alias="MINIO_SECRET_KEY")
    minio_secure: bool = Field(default=False, validation_alias="MINIO_SECURE")

    # JWT Configuration
    jwt_secret: str = Field(..., validation_alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=1440, validation_alias="JWT_EXPIRE_MINUTES")

    # OAuth - Google
    google_client_id: Optional[str] = Field(default=None, validation_alias="GOOGLE_CLIENT_ID")
    google_client_secret: Optional[str] = Field(
        default=None, validation_alias="GOOGLE_CLIENT_SECRET"
    )

    # OAuth - GitHub
    github_client_id: Optional[str] = Field(default=None, validation_alias="GITHUB_CLIENT_ID")
    github_client_secret: Optional[str] = Field(
        default=None, validation_alias="GITHUB_CLIENT_SECRET"
    )

    # Embedding Configuration
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384)

    # Agent Configuration
    max_retrieval_depth: int = Field(default=2)
    community_levels: int = Field(default=3)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
