"""Embedding factory for creating embedding models from different providers."""

from typing import Optional
from langchain_core.embeddings import Embeddings
from ..config import config


def get_embeddings(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> Embeddings:
    """Get embeddings instance based on provider configuration.
    
    Args:
        provider: Embedding provider (openai, huggingface, cohere, bedrock, vertex_ai)
        model: Model name (provider-specific)
        **kwargs: Additional provider-specific arguments
        
    Returns:
        Embeddings instance
        
    Raises:
        ValueError: If provider is not supported or credentials are missing
    """
    provider = provider or config.embedding_provider
    model = model or config.embedding_model
    
    if provider == "openai":
        return _get_openai_embeddings(model, **kwargs)
    elif provider == "huggingface":
        return _get_huggingface_embeddings(model, **kwargs)
    elif provider == "cohere":
        return _get_cohere_embeddings(model, **kwargs)
    elif provider == "bedrock":
        return _get_bedrock_embeddings(model, **kwargs)
    elif provider == "vertex_ai":
        return _get_vertex_ai_embeddings(model, **kwargs)
    else:
        raise ValueError(
            f"Unsupported embedding provider: {provider}. "
            f"Supported providers: openai, huggingface, cohere, bedrock, vertex_ai"
        )


def _get_openai_embeddings(model: str, **kwargs) -> Embeddings:
    """Get OpenAI embeddings instance."""
    from langchain_openai import OpenAIEmbeddings
    
    if not config.openai_api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    
    return OpenAIEmbeddings(
        model=model,
        api_key=config.openai_api_key,
        **kwargs
    )


def _get_huggingface_embeddings(model: str, **kwargs) -> Embeddings:
    """Get HuggingFace embeddings instance."""
    from langchain_huggingface import HuggingFaceEmbeddings
    
    # HuggingFace embeddings can work without API key (using local models)
    # but API key enables using Inference API
    return HuggingFaceEmbeddings(
        model_name=model,
        **kwargs
    )


def _get_cohere_embeddings(model: str, **kwargs) -> Embeddings:
    """Get Cohere embeddings instance."""
    from langchain_cohere import CohereEmbeddings
    
    if not config.cohere_api_key:
        raise ValueError("COHERE_API_KEY not set in environment")
    
    return CohereEmbeddings(
        model=model,
        cohere_api_key=config.cohere_api_key,
        **kwargs
    )


def _get_bedrock_embeddings(model: str, **kwargs) -> Embeddings:
    """Get AWS Bedrock embeddings instance."""
    from langchain_aws import BedrockEmbeddings
    
    if not config.aws_access_key_id or not config.aws_secret_access_key:
        raise ValueError("AWS credentials not set in environment")
    
    return BedrockEmbeddings(
        model_id=model,
        region_name=config.aws_region,
        **kwargs
    )


def _get_vertex_ai_embeddings(model: str, **kwargs) -> Embeddings:
    """Get Google Vertex AI embeddings instance."""
    from langchain_google_vertexai import VertexAIEmbeddings
    
    if not config.google_api_key and not config.bigquery_credentials_path:
        raise ValueError("Google credentials not set in environment")
    
    return VertexAIEmbeddings(
        model_name=model,
        **kwargs
    )
