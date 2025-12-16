"""Example: Using different LLM providers."""

import os
from dotenv import load_dotenv

load_dotenv()

from src.utils.llm_factory import get_llm
from src.agents.orchestrator import AgentOrchestrator


def test_provider(provider_name: str, model_name: str):
    """Test a specific LLM provider.
    
    Args:
        provider_name: Name of the provider
        model_name: Model name to use
    """
    print(f"\n{'=' * 60}")
    print(f"Testing {provider_name.upper()} with model: {model_name}")
    print('=' * 60)
    
    try:
        # Get LLM instance
        llm = get_llm(provider=provider_name, model=model_name)
        print(f"✅ Successfully initialized {provider_name} LLM")
        
        # Create orchestrator with this LLM
        orchestrator = AgentOrchestrator(llm=llm)
        print(f"✅ Successfully created orchestrator")
        
        # Test simple query
        query = "What are the top 5 customers by total spending?"
        print(f"\n📝 Query: {query}")
        
        result = orchestrator.run(query)
        
        if result.final_answer:
            print(f"\n✅ Response:")
            print(result.final_answer[:200] + "..." if len(result.final_answer) > 200 else result.final_answer)
        
        if result.errors:
            print(f"\n⚠️ Errors: {result.errors}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def main():
    """Test different LLM providers."""
    
    print("=" * 60)
    print("Multi-Provider LLM Example")
    print("=" * 60)
    
    # Test configurations
    providers = []
    
    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        providers.append(("openai", "gpt-3.5-turbo"))
    
    # Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append(("anthropic", "claude-3-haiku-20240307"))
    
    # Google
    if os.getenv("GOOGLE_API_KEY"):
        providers.append(("google", "gemini-pro"))
    
    # AWS Bedrock
    if os.getenv("AWS_ACCESS_KEY_ID"):
        providers.append(("bedrock", "anthropic.claude-3-haiku-20240307-v1:0"))
    
    # Azure OpenAI
    if os.getenv("AZURE_OPENAI_API_KEY"):
        providers.append(("azure", os.getenv("AZURE_DEPLOYMENT_NAME", "gpt-35-turbo")))
    
    if not providers:
        print("\n⚠️ No LLM providers configured!")
        print("Please set API keys in your .env file.")
        print("\nSupported providers:")
        print("  - OpenAI: OPENAI_API_KEY")
        print("  - Anthropic: ANTHROPIC_API_KEY")
        print("  - Google: GOOGLE_API_KEY")
        print("  - AWS Bedrock: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("  - Azure OpenAI: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT")
        return
    
    # Test each configured provider
    for provider, model in providers:
        test_provider(provider, model)
    
    # Comparison
    print(f"\n{'=' * 60}")
    print("Summary")
    print('=' * 60)
    print(f"Tested {len(providers)} provider(s):")
    for provider, model in providers:
        print(f"  ✓ {provider.upper()}: {model}")


if __name__ == "__main__":
    main()
