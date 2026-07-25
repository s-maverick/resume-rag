from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")


class Settings(BaseSettings):
    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    supabase_url: str = Field(alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(alias="SUPABASE_SERVICE_ROLE_KEY")
    generation_model: str = Field("gemini-3.5-flash", alias="GEMINI_GENERATION_MODEL")
    embedding_model: str = Field("gemini-embedding-2", alias="GEMINI_EMBEDDING_MODEL")
    embedding_dimensions: int = Field(1536, alias="EMBEDDING_DIMENSIONS")
    retrieval_match_count: int = Field(12, alias="RETRIEVAL_MATCH_COUNT")

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")

    @field_validator("embedding_dimensions")
    @classmethod
    def validate_embedding_dimensions(cls, value: int) -> int:
        if not 128 <= value <= 3072:
            raise ValueError("EMBEDDING_DIMENSIONS must be between 128 and 3072")
        return value

    @field_validator("supabase_url", mode="before")
    @classmethod
    def normalize_supabase_url(cls, value: str) -> str:
        """Accept a project URL even if its REST path was copied too."""
        return str(value).strip().rstrip("/").removesuffix("/rest/v1")


@lru_cache
def get_settings() -> Settings:
    return Settings()
