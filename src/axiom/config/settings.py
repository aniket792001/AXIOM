"""Axiom & SCORE Configuration Module.

Type-safe settings management using Pydantic Settings v2.
Loads environment variables from .env file or system environment.
"""

from functools import lru_cache
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application and engine configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application & Runtime
    app_env: str = Field(default="development", description="Runtime environment")
    app_name: str = Field(default="Axiom-RAG", description="Application name")
    app_host: str = Field(default="0.0.0.0", description="API host")
    app_port: int = Field(default=8000, description="API port")
    log_level: str = Field(default="INFO", description="Logging level")

    # LLM Providers
    gemini_api_key: Optional[str] = Field(default=None, description="Google Gemini API Key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API Key")
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API Key")

    # Model Tiering
    fast_model: str = Field(
        default="gemini-1.5-flash",
        description="Fast model for routing, grading, and self-correction loops",
    )
    reasoning_model: str = Field(
        default="gemini-1.5-pro",
        description="High-reasoning model for citation-grounded synthesis",
    )

    # Vector Database
    vector_store_type: str = Field(default="qdrant", description="Vector store: qdrant or chroma")
    qdrant_url: str = Field(default="http://localhost:6333", description="Qdrant service URL")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API Key")
    qdrant_collection: str = Field(default="axiom_contracts", description="Vector collection name")

    # Retrieval & Re-ranking
    embedding_model: str = Field(
        default="text-embedding-004",
        description="Embedding model name",
    )
    bm25_enabled: bool = Field(default=True, description="Enable sparse BM25 keyword retrieval")
    reranker_enabled: bool = Field(default=False, description="Enable cross-encoder re-ranking")
    cohere_api_key: Optional[str] = Field(default=None, description="Cohere API key for re-ranking")

    # Web Search Fallback
    tavily_api_key: Optional[str] = Field(default=None, description="Tavily Web Search API key")

    # Agent Loop Thresholds
    max_loop_count: int = Field(default=3, description="Maximum self-correction loop limit")
    min_relevance_score: float = Field(default=0.7, description="Document relevance threshold")

    # Observability (LangSmith / OpenTelemetry)
    langchain_tracing_v2: bool = Field(default=False, description="Enable LangSmith tracing")
    langchain_api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    langchain_project: str = Field(default="axiom-production", description="LangSmith project name")


@lru_cache()
def get_settings() -> Settings:
    """Return cached instance of application settings."""
    return Settings()
