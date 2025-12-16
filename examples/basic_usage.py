"""
Example: Basic usage of the Agentic Analytics system.

This example demonstrates how to use the system programmatically
to answer data analysis questions.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_analytics.orchestrator import AgenticOrchestrator
from agentic_analytics.utils.database import get_schema_info, create_sample_database


def main():
    """Main example function."""
    
    # Ensure database exists
    os.makedirs("data/examples", exist_ok=True)
    db_path = "data/examples/sample.db"
    
    if not os.path.exists(db_path):
        print("Creating sample database...")
        create_sample_database(db_path)
        print("✅ Sample database created!\n")
    
    # Get database schema
    print("Loading database schema...")
    schema = get_schema_info(db_path)
    print("✅ Schema loaded!\n")
    
    # Initialize orchestrator
    print("Initializing orchestrator...")
    orchestrator = AgenticOrchestrator(db_path, schema)
    print("✅ Orchestrator initialized!\n")
    
    # Note: To actually run queries, you need to set OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  WARNING: OPENAI_API_KEY not set!")
        print("   Set it in .env file or as environment variable to run queries.\n")
        print("Example questions you could ask:")
        print("- What are the total sales by product?")
        print("- Show me the top 3 selling products")
        print("- Create a bar chart of sales by product")
        print("- What's the average price by category?")
        return
    
    # Example questions
    questions = [
        "What are the total sales by product?",
        "Show me all products and their stock levels",
        "What's the average revenue per sale?",
    ]
    
    print("Running example questions...\n")
    print("=" * 60)
    
    for i, question in enumerate(questions, 1):
        print(f"\nQuestion {i}: {question}")
        print("-" * 60)
        
        try:
            # Run the orchestrator
            result = orchestrator.run(question)
            
            # Display results
            print(f"\nSQL Query:\n{result.get('sql_query', 'N/A')}")
            
            data = result.get('data')
            if data is not None:
                print(f"\nData (showing first 5 rows):")
                print(data.head().to_string())
            
            analysis = result.get('analysis', '')
            if analysis:
                print(f"\nAnalysis:\n{analysis}")
            
            print("\n" + "=" * 60)
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            print("=" * 60)


if __name__ == "__main__":
    main()
