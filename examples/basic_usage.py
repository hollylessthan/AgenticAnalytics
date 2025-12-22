"""Example script demonstrating basic usage."""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from src.agents.orchestrator import AgentOrchestrator
from src.rag.rag_system import RAGSystem
from src.utils.database import DatabaseManager


def main():
    """Run example queries."""
    
    print("=" * 60)
    print("Agentic Analytics - Example Usage")
    print("=" * 60)
    
    # Initialize systems
    print("\n1. Initializing systems...")
    orchestrator = AgentOrchestrator()
    rag_system = RAGSystem()
    
    # Index database schema
    print("\n2. Indexing database schema...")
    try:
        db = DatabaseManager()
        schema = db.get_schema_info()
        print(f"\nDatabase Schema:\n{schema}\n")
        
        rag_system.index_database_schema(schema)
        rag_system.save_index()
        print("Schema indexed successfully!")
    except Exception as e:
        print(f"Error indexing schema: {e}")
    
    # Example queries
    queries = [
        "Show me the top 10 customers by total sales",
        "What is the average order value by month?",
        "Create a visualization showing sales trends over time"
    ]
    
    print("\n3. Running example queries...\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 60}")
        print(f"Query {i}: {query}")
        print('=' * 60)
        
        try:
            result = orchestrator.run(query)
            
            print(f"\n✅ Final Answer:")
            print(result.final_answer)
            
            if result.sql_query:
                print(f"\n📝 SQL Query:")
                print(result.sql_query)
            
            if result.query_results is not None:
                print(f"\n📊 Data Preview:")
                print(result.query_results.head())
            
            if result.visualization_path:
                print(f"\n📈 Visualization saved to: {result.visualization_path}")
            
            if result.errors:
                print(f"\n⚠️ Errors:")
                for error in result.errors:
                    print(f"  - {error}")
        
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
