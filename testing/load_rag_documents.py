#!/usr/bin/env python3
"""
Load RAG documents into the vector store for SQL Agent context retrieval.

This script indexes schema documentation, best practices, and query patterns
into the LanceDB vector store for RAG-powered SQL generation.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.rag.rag_system import RAGSystem
from langchain_core.documents import Document


def load_markdown_docs(docs_dir: Path) -> list[Document]:
    """Load markdown documents from directory.
    
    Args:
        docs_dir: Directory containing markdown files
        
    Returns:
        List of Document objects
    """
    documents = []
    
    for md_file in docs_dir.rglob("*.md"):
        print(f"   Loading: {md_file.name}")
        
        # Read file content
        content = md_file.read_text(encoding='utf-8')
        
        # Extract metadata from filename
        filename = md_file.stem
        
        # Determine document type and metadata
        metadata = {
            "source": str(md_file.relative_to(docs_dir)),
            "filename": md_file.name
        }
        
        # Add specific metadata based on filename
        if "duckdb" in filename.lower() or "sql" in filename.lower():
            metadata["type"] = "sql_reference"
            metadata["topic"] = "sql_syntax"
            metadata["doc_type"] = "reference"
        elif "schema" in filename.lower():
            metadata["type"] = "database_schema"
            metadata["topic"] = "schema"
            metadata["doc_type"] = "schema"
        elif "best_practice" in filename.lower():
            metadata["type"] = "best_practices"
            metadata["topic"] = "sql_patterns"
            metadata["doc_type"] = "reference"
        elif "query" in filename.lower() or "pattern" in filename.lower():
            metadata["type"] = "query_pattern"
            metadata["topic"] = "sql_patterns"
            metadata["doc_type"] = "examples"
        elif "join" in filename.lower():
            metadata["type"] = "join_reference"
            metadata["topic"] = "sql_joins"
            metadata["doc_type"] = "reference"
        elif "business" in filename.lower() or "glossary" in filename.lower():
            metadata["type"] = "business_context"
            metadata["topic"] = "domain_knowledge"
            metadata["doc_type"] = "reference"
        else:
            metadata["type"] = "general"
            metadata["topic"] = "reference"
            metadata["doc_type"] = "general"
        
        documents.append(Document(
            page_content=content,
            metadata=metadata
        ))
    
    return documents


def main():
    """Load RAG documents into vector store."""
    
    print("=" * 80)
    print("Loading RAG Documents into Vector Store")
    print("=" * 80)
    
    # Document directories
    rag_docs_dir = Path(__file__).parent / "rag_documents"
    
    if not rag_docs_dir.exists():
        print(f"\n❌ Error: RAG documents directory not found: {rag_docs_dir}")
        print("Run generate_rag_documents.py first!")
        return 1
    
    # Initialize RAG system
    print("\n🔧 Initializing RAG system...")
    rag_system = RAGSystem()
    
    # Load markdown documents
    print(f"\n📚 Loading documents from {rag_docs_dir}...")
    documents = load_markdown_docs(rag_docs_dir)
    
    if not documents:
        print(f"\n⚠️  No markdown files found in {rag_docs_dir}")
        return 1
    
    print(f"\n   Found {len(documents)} documents")
    
    # Deduplicate documents by content hash before indexing
    print(f"\n📊 Deduplicating {len(documents)} documents...")
    seen_hashes = set()
    deduped_documents = []
    for doc in documents:
        content_hash = hash(doc.page_content)
        if content_hash not in seen_hashes:
            deduped_documents.append(doc)
            seen_hashes.add(content_hash)
    print(f"   {len(deduped_documents)} unique documents (removed {len(documents) - len(deduped_documents)} duplicates)")

    # Index deduplicated documents
    print(f"\n📊 Indexing {len(deduped_documents)} documents into vector store...")
    rag_system.index_documents(deduped_documents)
    
    print("\n✅ Successfully indexed all deduplicated documents!")
    
    # Print summary by type
    print("\n📋 Document Summary:")
    type_counts = {}
    for doc in documents:
        doc_type = doc.metadata.get('type', 'unknown')
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1
    
    for doc_type, count in sorted(type_counts.items()):
        print(f"   - {doc_type}: {count} document(s)")
    
    # Test retrieval
    print("\n🔍 Testing retrieval...")
    test_queries = [
        ("How to calculate date differences in DuckDB?", "sql_reference"),
        ("What tables contain customer data?", "database_schema"),
        ("Best practices for joining tables", "join_reference")
    ]
    
    for query, expected_type in test_queries:
        print(f"\n   Query: '{query}'")
        results = rag_system.retrieve_context(query, k=2)
        if results:
            print(f"   ✓ Retrieved {len(results)} documents")
            for i, doc in enumerate(results, 1):
                print(f"      {i}. Type: {doc.metadata.get('type', 'unknown')}, "
                      f"Source: {doc.metadata.get('source', 'unknown')}")
        else:
            print(f"   ⚠️  No documents retrieved")
    
    print("\n" + "=" * 80)
    print("✅ RAG Document Loading Complete!")
    print("=" * 80)
    print("\n🎯 Next steps:")
    print("   - Run examples to test RAG-powered SQL generation")
    print("   - The SQL Agent will now use these docs for better query generation")
    print("   - DuckDB-specific syntax will be automatically applied")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
