"""Example: Using different vector stores and embedding models."""

import os
from dotenv import load_dotenv

load_dotenv()

from langchain_core.documents import Document
from src.utils.embedding_factory import get_embeddings
from src.rag.vector_store import get_vector_store


def test_embeddings(provider: str, model: str):
    """Test embedding provider.
    
    Args:
        provider: Embedding provider name
        model: Model name
    """
    print(f"\n{'=' * 60}")
    print(f"Testing {provider.upper()} Embeddings: {model}")
    print('=' * 60)
    
    try:
        embeddings = get_embeddings(provider=provider, model=model)
        print(f"✅ Successfully initialized embeddings")
        
        # Test embedding
        test_text = "This is a test document for embeddings"
        embedding = embeddings.embed_query(test_text)
        print(f"✅ Generated embedding vector (dimension: {len(embedding)})")
        print(f"   Sample values: {embedding[:5]}...")
        
        return embeddings
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_vector_store(store_type: str, embeddings):
    """Test vector store.
    
    Args:
        store_type: Vector store type
        embeddings: Embeddings instance
    """
    print(f"\n{'=' * 60}")
    print(f"Testing {store_type.upper()} Vector Store")
    print('=' * 60)
    
    try:
        # Create vector store
        vector_store = get_vector_store(
            vector_store_type=store_type,
            embeddings=embeddings
        )
        print(f"✅ Successfully initialized vector store")
        
        # Test documents
        test_docs = [
            Document(
                page_content="Python is a high-level programming language",
                metadata={"source": "test1", "topic": "programming"}
            ),
            Document(
                page_content="Machine learning models require training data",
                metadata={"source": "test2", "topic": "ml"}
            ),
            Document(
                page_content="SQL is used for database queries",
                metadata={"source": "test3", "topic": "database"}
            )
        ]
        
        # Add documents
        print(f"📝 Adding {len(test_docs)} test documents...")
        vector_store.add_documents(test_docs)
        print(f"✅ Documents added successfully")
        
        # Test search
        query = "programming languages"
        print(f"\n🔍 Searching for: '{query}'")
        results = vector_store.similarity_search(query, k=2)
        
        print(f"✅ Found {len(results)} results:")
        for i, doc in enumerate(results, 1):
            print(f"\n{i}. {doc.page_content}")
            print(f"   Metadata: {doc.metadata}")
        
        # Test save/load if supported
        if store_type in ["faiss", "chroma"]:
            print(f"\n💾 Testing save/load...")
            vector_store.save(f"{store_type}_test")
            print(f"✅ Saved to {store_type}_test")
            
            # Load
            vector_store.load(f"{store_type}_test")
            print(f"✅ Loaded from {store_type}_test")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def main():
    """Test different vector stores and embeddings."""
    
    print("=" * 60)
    print("Vector Store & Embedding Models Example")
    print("=" * 60)
    
    # Test embedding providers
    embedding_configs = []
    
    # OpenAI
    if os.getenv("OPENAI_API_KEY"):
        embedding_configs.append(("openai", "text-embedding-ada-002"))
    
    # HuggingFace (works without API key for local models)
    embedding_configs.append(("huggingface", "sentence-transformers/all-MiniLM-L6-v2"))
    
    # Cohere
    if os.getenv("COHERE_API_KEY"):
        embedding_configs.append(("cohere", "embed-english-v3.0"))
    
    # AWS Bedrock
    if os.getenv("AWS_ACCESS_KEY_ID"):
        embedding_configs.append(("bedrock", "amazon.titan-embed-text-v1"))
    
    # Test embeddings
    embeddings_map = {}
    for provider, model in embedding_configs:
        embeddings = test_embeddings(provider, model)
        if embeddings:
            embeddings_map[provider] = embeddings
    
    if not embeddings_map:
        print("\n⚠️ No embedding providers available!")
        print("At minimum, HuggingFace should work (no API key needed)")
        return
    
    # Get one embedding instance for vector store testing
    default_embeddings = next(iter(embeddings_map.values()))
    
    # Test vector stores
    print("\n" + "=" * 60)
    print("Testing Vector Stores")
    print("=" * 60)
    
    vector_stores = []
    
    # FAISS (always available)
    vector_stores.append("faiss")
    
    # Weaviate (if configured)
    if os.getenv("WEAVIATE_URL"):
        vector_stores.append("weaviate")
    
    # OpenSearch (if configured)
    if os.getenv("OPENSEARCH_URL"):
        vector_stores.append("opensearch")
    
    # Pinecone (if configured)
    if os.getenv("PINECONE_API_KEY"):
        vector_stores.append("pinecone")
    
    # Chroma (always available)
    vector_stores.append("chroma")
    
    # Azure Search (if configured)
    if os.getenv("AZURE_SEARCH_ENDPOINT"):
        vector_stores.append("azure_search")
    
    # Test each vector store
    results = {}
    for store_type in vector_stores:
        success = test_vector_store(store_type, default_embeddings)
        results[store_type] = success
    
    # Summary
    print(f"\n{'=' * 60}")
    print("Summary")
    print('=' * 60)
    
    print(f"\n📊 Embedding Providers Tested: {len(embeddings_map)}")
    for provider in embeddings_map.keys():
        print(f"  ✓ {provider.upper()}")
    
    print(f"\n📚 Vector Stores Tested: {len(results)}")
    for store, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {store.upper()}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    print("  - Development: FAISS + HuggingFace (free, local)")
    print("  - Production (small): Chroma + OpenAI (easy setup)")
    print("  - Production (large): Pinecone/Weaviate + OpenAI (scalable)")
    print("  - Enterprise: Azure Search/OpenSearch + Cohere (managed)")


if __name__ == "__main__":
    main()
