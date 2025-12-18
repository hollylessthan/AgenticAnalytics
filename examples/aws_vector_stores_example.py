"""AWS Vector Store Integration Examples

This example demonstrates how to use different AWS vector storage solutions
with AgenticAnalytics, including OpenSearch, Kendra, Aurora pgvector, and DynamoDB.

Each provider has different tradeoffs in terms of cost, performance, and features.
"""

import os
from dotenv import load_dotenv
from src.rag.rag_system import RAGSystem
from src.rag.vector_store import get_vector_store
from src.utils.embedding_factory import get_embeddings
from langchain_core.documents import Document

load_dotenv()


# ============================================================================
# Example 1: AWS OpenSearch (Already Implemented - Showcase)
# ============================================================================

def example_opensearch():
    """AWS OpenSearch - Managed vector search at scale.
    
    Setup:
        1. Create OpenSearch cluster in AWS Console or using CloudFormation
        2. Set environment variables:
           OPENSEARCH_URL=https://your-domain.us-east-1.es.amazonaws.com
           OPENSEARCH_USERNAME=admin
           OPENSEARCH_PASSWORD=YourSecurePassword123!
        3. Optionally use IAM auth instead of basic auth
    
    Cost: ~$100-500/month depending on cluster size
    Pros: Scalable, managed, great for large datasets (10M+ documents)
    Cons: Requires cluster management, higher cost for small datasets
    """
    print("\n" + "="*70)
    print("Example 1: AWS OpenSearch Vector Store")
    print("="*70)
    
    # Check if OpenSearch is configured
    if not os.getenv("OPENSEARCH_URL"):
        print("⚠️  OpenSearch not configured. Set OPENSEARCH_URL environment variable.")
        return
    
    try:
        # Get embeddings from AWS Bedrock (native AWS integration)
        embeddings = get_embeddings(provider="bedrock", model="amazon.titan-embed-text-v1")
        
        # Get OpenSearch vector store
        vector_store = get_vector_store("opensearch", embeddings)
        
        # Add sample documents
        documents = [
            Document(
                page_content="AWS OpenSearch is a managed service for search and analytics.",
                metadata={"source": "aws_docs"}
            ),
            Document(
                page_content="Vector search enables similarity-based document retrieval.",
                metadata={"source": "vector_search_guide"}
            ),
        ]
        
        vector_store.add_documents(documents)
        
        # Search for similar documents
        results = vector_store.similarity_search("AWS vector search capabilities", k=2)
        
        print(f"\n✓ Added {len(documents)} documents to OpenSearch")
        print(f"✓ Found {len(results)} similar documents:")
        for i, doc in enumerate(results, 1):
            print(f"  {i}. {doc.page_content[:60]}...")
            
    except Exception as e:
        print(f"✗ Error: {e}")


# ============================================================================
# Example 2: AWS Kendra (Enterprise Document Retrieval)
# ============================================================================

def example_kendra():
    """AWS Kendra - Intelligent document retrieval with natural language understanding.
    
    Setup:
        1. Create Kendra index in AWS Console
        2. Set environment variables:
           KENDRA_INDEX_ID=your-index-id
           AWS_REGION=us-east-1
        3. AWS credentials must be configured (IAM role or access keys)
    
    Cost: ~$0.30 per 1M queries + storage (~$0.20 per GB/month)
    Pros: 
        - ML-powered relevance, no embeddings needed
        - Enterprise features: access control, faceted search
        - Handles PDFs, docs natively
    Cons: 
        - Higher cost for high-volume queries
        - Requires AWS credentials setup
        - Slower than pure vector search
    """
    print("\n" + "="*70)
    print("Example 2: AWS Kendra Vector Store")
    print("="*70)
    
    # Check if Kendra is configured
    if not os.getenv("KENDRA_INDEX_ID"):
        print("⚠️  Kendra not configured. Set KENDRA_INDEX_ID environment variable.")
        print("\nSetup steps:")
        print("  1. Create Kendra index: AWS Console > Kendra > Create index")
        print("  2. Note the Index ID")
        print("  3. Set: export KENDRA_INDEX_ID=your-index-id")
        return
    
    try:
        # Kendra doesn't require embeddings - it uses its own ML models
        vector_store = get_vector_store("kendra")
        
        # Add sample documents
        documents = [
            Document(
                page_content="AWS Kendra uses machine learning to understand search intent.",
                metadata={"source": "kendra_whitepaper"}
            ),
            Document(
                page_content="Kendra supports multiple document types: PDF, Word, HTML, plain text.",
                metadata={"source": "kendra_features"}
            ),
        ]
        
        vector_store.add_documents(documents)
        
        # Search
        results = vector_store.similarity_search("How does Kendra understand search intent?", k=2)
        
        print(f"\n✓ Added {len(documents)} documents to Kendra")
        print(f"✓ Found {len(results)} relevant documents:")
        for i, doc in enumerate(results, 1):
            score = doc.metadata.get('score', 'N/A')
            print(f"  {i}. {doc.page_content[:50]}... (Confidence: {score})")
            
    except Exception as e:
        print(f"✗ Error: {e}")


# ============================================================================
# Example 3: AWS Aurora PostgreSQL with pgvector
# ============================================================================

def example_aurora_pgvector():
    """AWS Aurora PostgreSQL with pgvector extension.
    
    Setup:
        1. Create Aurora PostgreSQL cluster in AWS Console
        2. Connect and run: CREATE EXTENSION vector;
        3. Set environment variables:
           AURORA_HOST=your-cluster.region.rds.amazonaws.com
           AURORA_USER=postgres
           AURORA_PASSWORD=SecurePassword123
           AURORA_DB_NAME=analytics
           AWS_REGION=us-east-1
    
    Cost: ~$50-200/month for managed database
    Pros:
        - Cost-effective for medium datasets
        - Native PostgreSQL with vector extensions
        - Built-in scalability, backups, replication
        - Great for hybrid use cases (vectors + relational queries)
    Cons:
        - Requires pgvector extension setup
        - Slower than specialized vector DBs for very large scale
        - Need to manage indexes manually
    """
    print("\n" + "="*70)
    print("Example 3: AWS Aurora PostgreSQL with pgvector")
    print("="*70)
    
    # Check if Aurora is configured
    required_vars = ["AURORA_HOST", "AURORA_USER", "AURORA_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"⚠️  Aurora not configured. Missing: {', '.join(missing)}")
        print("\nSetup steps:")
        print("  1. Create Aurora cluster: AWS Console > RDS > Databases > Create")
        print("  2. Choose 'Amazon Aurora' > PostgreSQL compatible")
        print("  3. Connect and run: CREATE EXTENSION vector;")
        print("  4. Set environment variables:")
        print("     export AURORA_HOST=your-endpoint.rds.amazonaws.com")
        print("     export AURORA_USER=postgres")
        print("     export AURORA_PASSWORD=YourPassword")
        print("     export AURORA_DB_NAME=analytics")
        return
    
    try:
        # Get embeddings
        embeddings = get_embeddings(provider="bedrock", model="amazon.titan-embed-text-v1")
        
        # Get Aurora pgvector store
        vector_store = get_vector_store("aurora_pgvector", embeddings)
        
        # Add documents
        documents = [
            Document(
                page_content="Aurora pgvector combines PostgreSQL reliability with vector search.",
                metadata={"source": "aurora_guide"}
            ),
            Document(
                page_content="pgvector supports HNSW and IVFFlat indexes for fast similarity search.",
                metadata={"source": "pgvector_docs"}
            ),
        ]
        
        vector_store.add_documents(documents)
        
        # Search
        results = vector_store.similarity_search("PostgreSQL vector extensions", k=2)
        
        print(f"\n✓ Connected to Aurora PostgreSQL")
        print(f"✓ Added {len(documents)} documents")
        print(f"✓ Found {len(results)} similar documents:")
        for i, doc in enumerate(results, 1):
            score = doc.metadata.get('similarity_score', 'N/A')
            print(f"  {i}. {doc.page_content[:50]}... (Similarity: {score:.3f})")
            
    except Exception as e:
        print(f"✗ Error: {e}")


# ============================================================================
# Example 4: AWS DynamoDB Vector Store
# ============================================================================

def example_dynamodb():
    """AWS DynamoDB - Serverless NoSQL with vector search.
    
    Setup:
        1. Create DynamoDB table in AWS Console
        2. Add attributes: id (PK), source, content, embedding, timestamp
        3. Set environment variables:
           DYNAMODB_TABLE_NAME=documents
           AWS_REGION=us-east-1
    
    Cost: ~$1.25/GB stored + $1.25 per million read units
    Pros:
        - Serverless (no infrastructure management)
        - Automatic scaling
        - Great for variable workloads
        - Integrates with Lambda functions
    Cons:
        - In-memory similarity scoring (not optimized)
        - Slower for large datasets (no native vector index)
        - Best for <100K documents
        - Requires full table scan for each query
    """
    print("\n" + "="*70)
    print("Example 4: AWS DynamoDB Vector Store")
    print("="*70)
    
    # Check if DynamoDB is configured
    if not os.getenv("DYNAMODB_TABLE_NAME"):
        print("⚠️  DynamoDB not configured. Set DYNAMODB_TABLE_NAME environment variable.")
        print("\nSetup steps:")
        print("  1. Create table: AWS Console > DynamoDB > Create table")
        print("  2. Table name: documents (or your choice)")
        print("  3. Partition key: id (String)")
        print("  4. Enable 'Pay per request' billing")
        print("  5. Set: export DYNAMODB_TABLE_NAME=documents")
        return
    
    try:
        # Get embeddings
        embeddings = get_embeddings(provider="bedrock", model="amazon.titan-embed-text-v1")
        
        # Get DynamoDB store
        vector_store = get_vector_store("dynamodb", embeddings)
        
        # Add documents
        documents = [
            Document(
                page_content="DynamoDB is a serverless NoSQL database with flexible scaling.",
                metadata={"source": "dynamodb_guide"}
            ),
            Document(
                page_content="Vector embeddings enable semantic search on DynamoDB items.",
                metadata={"source": "vector_guide"}
            ),
        ]
        
        vector_store.add_documents(documents)
        
        # Search
        results = vector_store.similarity_search("Serverless vector database", k=2)
        
        print(f"\n✓ Connected to DynamoDB")
        print(f"✓ Added {len(documents)} documents")
        print(f"✓ Found {len(results)} similar documents:")
        for i, doc in enumerate(results, 1):
            score = doc.metadata.get('similarity_score', 'N/A')
            print(f"  {i}. {doc.page_content[:50]}... (Similarity: {score:.3f})")
            
    except Exception as e:
        print(f"✗ Error: {e}")


# ============================================================================
# Provider Selection Guide
# ============================================================================

def print_selection_guide():
    """Print guide for choosing the right AWS vector store."""
    print("\n" + "="*70)
    print("AWS Vector Store Selection Guide")
    print("="*70)
    
    comparison = {
        "OpenSearch": {
            "Cost": "$100-500/mo",
            "Scale": "10M+ docs",
            "Speed": "Very Fast",
            "Setup": "Medium",
            "Best For": "Enterprise scale"
        },
        "Kendra": {
            "Cost": "$0.30/1M queries",
            "Scale": "Any",
            "Speed": "Medium",
            "Setup": "Easy",
            "Best For": "Enterprise search"
        },
        "Aurora pgvector": {
            "Cost": "$50-200/mo",
            "Scale": "1M+ docs",
            "Speed": "Fast",
            "Setup": "Hard",
            "Best For": "Hybrid queries"
        },
        "DynamoDB": {
            "Cost": "$1.25/GB",
            "Scale": "<100K docs",
            "Speed": "Slow",
            "Setup": "Easy",
            "Best For": "Serverless"
        }
    }
    
    for provider, details in comparison.items():
        print(f"\n{provider}:")
        for key, value in details.items():
            print(f"  {key:15}: {value}")


# ============================================================================
# Main: Run All Examples
# ============================================================================

def main():
    """Run all AWS vector store examples."""
    print("\n" + "="*70)
    print("AWS Vector Store Integration Examples")
    print("="*70)
    
    # Show selection guide
    print_selection_guide()
    
    # Run examples
    example_opensearch()
    example_kendra()
    example_aurora_pgvector()
    example_dynamodb()
    
    print("\n" + "="*70)
    print("Examples completed!")
    print("="*70)


if __name__ == "__main__":
    main()
