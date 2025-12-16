"""Configuration settings for the Agentic Analytics system."""

import os
from typing import Literal
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    """Application settings."""
    
    # API Keys
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Model settings
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    temperature: float = float(os.getenv("TEMPERATURE", "0.0"))
    
    # Vector store settings
    vector_store_type: Literal["faiss", "weaviate"] = os.getenv("VECTOR_STORE_TYPE", "faiss")
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://localhost:8080")
    
    # Database settings
    database_path: str = os.getenv("DATABASE_PATH", "data/examples/sample.db")
    
    # Agent settings
    max_iterations: int = int(os.getenv("MAX_ITERATIONS", "10"))
    verbose: bool = os.getenv("VERBOSE", "true").lower() == "true"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()
