"""Configuration management for the application."""

import os
from typing import Optional, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Application configuration."""
    
    # LLM Provider Settings
    llm_provider: Literal["openai", "anthropic", "google", "bedrock", "azure"] = os.getenv(
        "LLM_PROVIDER", "openai"
    )
    
    # API Keys for different providers
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    
    # AWS Settings (supports both explicit credentials and boto3/IAM role)
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_profile: str = os.getenv("AWS_PROFILE", "")  # For boto3 profile-based auth
    use_boto3_session: bool = os.getenv("USE_BOTO3_SESSION", "false").lower() == "true"
    
    # Redshift-specific IAM settings
    redshift_iam_role: str = os.getenv("REDSHIFT_IAM_ROLE", "")  # IAM role ARN for Redshift
    redshift_cluster_id: str = os.getenv("REDSHIFT_CLUSTER_ID", "")  # Cluster ID for temp credentials
    
    # Database Settings
    database_type: Literal[
        "sqlite", "postgresql", "mysql", "duckdb", "snowflake", "redshift", "bigquery"
    ] = os.getenv("DATABASE_TYPE", "duckdb")
    database_url: str = os.getenv("DATABASE_URL", "duckdb:///./testing/tpcds_1gb.duckdb")
    
    # Snowflake specific
    snowflake_account: Optional[str] = os.getenv("SNOWFLAKE_ACCOUNT")
    snowflake_user: Optional[str] = os.getenv("SNOWFLAKE_USER")
    snowflake_password: Optional[str] = os.getenv("SNOWFLAKE_PASSWORD")
    snowflake_database: Optional[str] = os.getenv("SNOWFLAKE_DATABASE")
    snowflake_schema: Optional[str] = os.getenv("SNOWFLAKE_SCHEMA")
    snowflake_warehouse: Optional[str] = os.getenv("SNOWFLAKE_WAREHOUSE")
    
    # BigQuery specific
    bigquery_project: Optional[str] = os.getenv("BIGQUERY_PROJECT")
    bigquery_credentials_path: Optional[str] = os.getenv("BIGQUERY_CREDENTIALS_PATH")
    
    # Vector Store Settings
    vector_store_type: Literal[
        "faiss", "weaviate", "opensearch", "kendra", "aurora_pgvector", "dynamodb", 
        "azure_search", "vertex_ai", "pinecone", "chroma"
    ] = os.getenv("VECTOR_STORE_TYPE", "faiss")
    
    # Embedding Model Settings
    embedding_provider: Literal["openai", "huggingface", "cohere", "bedrock", "vertex_ai"] = os.getenv(
        "EMBEDDING_PROVIDER", "openai"
    )
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002")
    
    # Weaviate
    weaviate_url: Optional[str] = os.getenv("WEAVIATE_URL")
    weaviate_api_key: Optional[str] = os.getenv("WEAVIATE_API_KEY")
    
    # OpenSearch
    opensearch_url: Optional[str] = os.getenv("OPENSEARCH_URL")
    opensearch_username: Optional[str] = os.getenv("OPENSEARCH_USERNAME")
    opensearch_password: Optional[str] = os.getenv("OPENSEARCH_PASSWORD")
    
    # AWS Configuration
    aws_region: Optional[str] = os.getenv("AWS_REGION", "us-east-1")
    
    # AWS Kendra
    kendra_index_id: Optional[str] = os.getenv("KENDRA_INDEX_ID")
    
    # AWS Aurora PostgreSQL with pgvector
    aurora_host: Optional[str] = os.getenv("AURORA_HOST")
    aurora_port: Optional[int] = int(os.getenv("AURORA_PORT", "5432")) if os.getenv("AURORA_PORT") else 5432
    aurora_user: Optional[str] = os.getenv("AURORA_USER")
    aurora_password: Optional[str] = os.getenv("AURORA_PASSWORD")
    aurora_db_name: Optional[str] = os.getenv("AURORA_DB_NAME", "analytics")
    
    # AWS DynamoDB
    dynamodb_table_name: Optional[str] = os.getenv("DYNAMODB_TABLE_NAME")
    
    # Azure Cognitive Search
    azure_search_endpoint: Optional[str] = os.getenv("AZURE_SEARCH_ENDPOINT")
    azure_search_key: Optional[str] = os.getenv("AZURE_SEARCH_KEY")
    azure_search_index_name: Optional[str] = os.getenv("AZURE_SEARCH_INDEX_NAME")
    
    # Google Cloud Platform Configuration
    gcp_project_id: Optional[str] = os.getenv("GCP_PROJECT_ID")
    gcp_region: Optional[str] = os.getenv("GCP_REGION", "us-central1")
    
    # Google Vertex AI Vector Search
    vertex_ai_index_id: Optional[str] = os.getenv("VERTEX_AI_INDEX_ID")
    vertex_ai_endpoint: Optional[str] = os.getenv("VERTEX_AI_ENDPOINT")
    
    # Pinecone
    pinecone_api_key: Optional[str] = os.getenv("PINECONE_API_KEY")
    pinecone_environment: Optional[str] = os.getenv("PINECONE_ENVIRONMENT")
    pinecone_index_name: Optional[str] = os.getenv("PINECONE_INDEX_NAME")
    
    # Chroma
    chroma_host: Optional[str] = os.getenv("CHROMA_HOST")
    chroma_port: Optional[int] = int(os.getenv("CHROMA_PORT", "8000")) if os.getenv("CHROMA_PORT") else 8000
    
    # Cohere (for embeddings)
    cohere_api_key: Optional[str] = os.getenv("COHERE_API_KEY")
    
    # HuggingFace (for embeddings)
    huggingface_api_key: Optional[str] = os.getenv("HUGGINGFACE_API_KEY")
    
    # Agent Settings
    max_iterations: int = int(os.getenv("MAX_ITERATIONS", "10"))
    agent_temperature: float = float(os.getenv("AGENT_TEMPERATURE", "0.0"))
    agent_model: str = os.getenv(
        "AGENT_MODEL",
        "gpt-4.1"  # Default model
    )
    
    # Agent Retry Settings
    agent_retry_count: int = int(os.getenv("AGENT_RETRY_COUNT", "2"))  # Number of retries per agent
    agent_retry_delay_ms: int = int(os.getenv("AGENT_RETRY_DELAY_MS", "500"))  # Delay between retries in ms
    
    # Cache Settings (NEW)
    enable_data_cache: bool = os.getenv("ENABLE_DATA_CACHE", "true").lower() == "true"
    max_cache_rows: int = int(os.getenv("MAX_CACHE_ROWS", "10000"))  # Max rows to cache
    max_cache_size_mb: int = int(os.getenv("MAX_CACHE_SIZE_MB", "100"))  # Max cache size in MB
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # 1 hour default
    auto_sample_large_results: bool = os.getenv("AUTO_SAMPLE_LARGE_RESULTS", "false").lower() == "true"
    sample_size: int = int(os.getenv("SAMPLE_SIZE", "1000"))  # Sample size for large results
    
    # Streamlit
    streamlit_port: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    class Config:
        """Pydantic config."""
        env_file = ".env"


# Global config instance
config = Config()
