"""LLM factory for creating language model instances from different providers."""

from typing import Optional
from langchain_core.language_models import BaseChatModel
from ..config import config


def get_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> BaseChatModel:
    """Get LLM instance based on provider configuration.
    
    Args:
        provider: LLM provider (openai, anthropic, google, bedrock, azure)
        model: Model name (provider-specific)
        temperature: Model temperature
        **kwargs: Additional provider-specific arguments
        
    Returns:
        Language model instance
        
    Raises:
        ValueError: If provider is not supported or credentials are missing
    """
    provider = provider or config.llm_provider
    model = model or config.agent_model
    temperature = temperature if temperature is not None else config.agent_temperature
    
    if provider == "openai":
        return _get_openai_llm(model, temperature, **kwargs)
    elif provider == "anthropic":
        return _get_anthropic_llm(model, temperature, **kwargs)
    elif provider == "google":
        return _get_google_llm(model, temperature, **kwargs)
    elif provider == "bedrock":
        return _get_bedrock_llm(model, temperature, **kwargs)
    elif provider == "azure":
        return _get_azure_llm(model, temperature, **kwargs)
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: openai, anthropic, google, bedrock, azure"
        )


def _get_openai_llm(model: str, temperature: float, **kwargs) -> BaseChatModel:
    """Get OpenAI LLM instance."""
    from langchain_openai import ChatOpenAI
    
    if not config.openai_api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")
    
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=config.openai_api_key,
        **kwargs
    )


def _get_anthropic_llm(model: str, temperature: float, **kwargs) -> BaseChatModel:
    """Get Anthropic (Claude) LLM instance."""
    from langchain_anthropic import ChatAnthropic
    
    if not config.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment")
    
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        anthropic_api_key=config.anthropic_api_key,
        **kwargs
    )


def _get_google_llm(model: str, temperature: float, **kwargs) -> BaseChatModel:
    """Get Google (Gemini) LLM instance."""
    from langchain_google_genai import ChatGoogleGenerativeAI
    
    if not config.google_api_key:
        raise ValueError("GOOGLE_API_KEY not set in environment")
    
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=config.google_api_key,
        **kwargs
    )


def _get_bedrock_llm(model: str, temperature: float, **kwargs) -> BaseChatModel:
    """Get AWS Bedrock LLM instance."""
    from langchain_aws import ChatBedrock
    
    if not config.aws_access_key_id or not config.aws_secret_access_key:
        raise ValueError("AWS credentials not set in environment")
    
    return ChatBedrock(
        model_id=model,
        model_kwargs={"temperature": temperature},
        region_name=config.aws_region,
        **kwargs
    )


def _get_azure_llm(model: str, temperature: float, **kwargs) -> BaseChatModel:
    """Get Azure OpenAI LLM instance."""
    from langchain_openai import AzureChatOpenAI
    
    if not config.azure_openai_api_key or not config.azure_openai_endpoint:
        raise ValueError("Azure OpenAI credentials not set in environment")
    
    return AzureChatOpenAI(
        azure_deployment=model,
        temperature=temperature,
        api_key=config.azure_openai_api_key,
        azure_endpoint=config.azure_openai_endpoint,
        **kwargs
    )
