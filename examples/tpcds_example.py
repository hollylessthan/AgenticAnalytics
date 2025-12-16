#!/usr/bin/env python3
"""
Example: Using TPC-DS test database with Agentic Analytics
Shows how to integrate the test database with the main application
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config
from src.agents.orchestrator import AgentOrchestrator
from src.utils.database_factory import get_database_engine
from src.rag.rag_system import RAGSystem


def setup_test_environment(scale: int = 1, rag_enabled: bool = True):
    """
    Setup the application to use TPC-DS test database
    
    Args:
        scale: Data scale (1, 10, or 100 GB)
        rag_enabled: Whether to enable RAG with test documents
    
    Returns:
        Configured orchestrator ready to use
    """
    print(f"🔧 Setting up test environment (scale={scale}GB)")
    
    # Create configuration
    config = Config()
    config.DATABASE_TYPE = "duckdb"
    config.DATABASE_PATH = f"testing/tpcds_{scale}gb.duckdb"
    config.RAG_ENABLED = rag_enabled
    
    # Verify database exists
    db_path = Path(config.DATABASE_PATH)
    if not db_path.exists():
        print(f"❌ Database not found: {config.DATABASE_PATH}")
        print(f"Run: cd testing && python setup_tpcds_duckdb.py --scale {scale}")
        sys.exit(1)
    
    print(f"✅ Using database: {config.DATABASE_PATH}")
    
    # Initialize database
    engine = get_database_engine(config)
    
    # Initialize RAG if enabled
    rag_system = None
    if rag_enabled:
        rag_docs_path = Path("testing/rag_documents")
        if not rag_docs_path.exists():
            print(f"⚠️  RAG documents not found: {rag_docs_path}")
            print("Run: cd testing && python generate_rag_documents.py")
            print("Continuing without RAG...")
            config.RAG_ENABLED = False
        else:
            print(f"✅ Loading RAG documents from: {rag_docs_path}")
            rag_system = RAGSystem(config)
            # Load documents
            documents = []
            for md_file in rag_docs_path.rglob("*.md"):
                with open(md_file) as f:
                    content = f.read()
                    documents.append({
                        "content": content,
                        "metadata": {"source": str(md_file)}
                    })
            
            if documents:
                print(f"📚 Indexing {len(documents)} documents...")
                # Note: RAGSystem needs to support bulk indexing
                # For now, users can pre-index documents
                print("✅ RAG system ready")
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(config, engine)
    
    print("✅ Environment ready!\n")
    return orchestrator


def run_example_queries(orchestrator: AgentOrchestrator):
    """Run example queries against TPC-DS data"""
    
    # Example queries that work well with TPC-DS schema
    queries = [
        {
            "question": "What are the total sales in the database?",
            "description": "Simple aggregation",
        },
        {
            "question": "Show me sales by year",
            "description": "Time-based aggregation with JOIN",
        },
        {
            "question": "What are the top 10 products by revenue?",
            "description": "JOIN with GROUP BY and ORDER BY",
        },
        {
            "question": "Create a bar chart showing sales by year",
            "description": "Visualization request",
        },
        {
            "question": "Calculate year-over-year sales growth",
            "description": "Advanced analytics with window functions",
        },
    ]
    
    print("="*70)
    print("🧪 Running Example Queries")
    print("="*70)
    
    for i, query_info in enumerate(queries, 1):
        question = query_info["question"]
        description = query_info["description"]
        
        print(f"\n📍 Query {i}/{len(queries)}")
        print(f"❓ Question: {question}")
        print(f"📝 Type: {description}")
        print("-"*70)
        
        try:
            # Run query
            result = orchestrator.run(question)
            
            # Display results
            if result.get("sql_query"):
                print(f"\n✅ Generated SQL:")
                print(result["sql_query"])
            
            if result.get("data") is not None:
                print(f"\n📊 Retrieved {len(result['data'])} rows")
                # Show first few rows
                if hasattr(result["data"], "head"):
                    print(result["data"].head())
            
            if result.get("analysis"):
                print(f"\n💡 Analysis:")
                print(result["analysis"][:300] + "...")
            
            if result.get("visualization_path"):
                print(f"\n📈 Visualization saved: {result['visualization_path']}")
            
            print(f"\n✅ Query completed successfully!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        print()


def interactive_mode(orchestrator: AgentOrchestrator):
    """Interactive query mode"""
    print("="*70)
    print("🎯 Interactive Mode")
    print("="*70)
    print("\nEnter your questions (or 'quit' to exit)")
    print("\nSuggested questions:")
    print("  - How many customers do we have?")
    print("  - What are total sales by product category?")
    print("  - Show me return rates by reason")
    print("  - Create a chart of monthly sales trends")
    print()
    
    while True:
        try:
            question = input("\n💬 Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            print("\n⏳ Processing...")
            result = orchestrator.run(question)
            
            print("\n" + "="*70)
            
            if result.get("sql_query"):
                print(f"\n📝 SQL:")
                print(result["sql_query"])
            
            if result.get("data") is not None:
                print(f"\n📊 Results:")
                if hasattr(result["data"], "head"):
                    print(result["data"].head(10))
                else:
                    print(result["data"])
            
            if result.get("analysis"):
                print(f"\n💡 Analysis:")
                print(result["analysis"])
            
            if result.get("visualization_path"):
                print(f"\n📈 Chart: {result['visualization_path']}")
            
            print("="*70)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Agentic Analytics with TPC-DS data")
    parser.add_argument("--scale", type=int, default=1, choices=[1, 10, 100],
                        help="Data scale (1, 10, or 100 GB)")
    parser.add_argument("--no-rag", action="store_true",
                        help="Disable RAG system")
    parser.add_argument("--interactive", action="store_true",
                        help="Run in interactive mode")
    args = parser.parse_args()
    
    print("🤖 Agentic Analytics - TPC-DS Testing")
    print("="*70)
    
    # Setup environment
    orchestrator = setup_test_environment(
        scale=args.scale,
        rag_enabled=not args.no_rag
    )
    
    # Run mode
    if args.interactive:
        interactive_mode(orchestrator)
    else:
        run_example_queries(orchestrator)
    
    print("\n✅ Done!")


if __name__ == "__main__":
    main()
