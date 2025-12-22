"""Example demonstrating profiling, preprocessing, and modeling workflow.

This example shows how the system handles:
1. Data profiling / EDA (Exploratory Data Analysis)
2. Feature engineering / preprocessing  
3. Predictive modeling

Note: You'll see "[LanceDB] Opened existing table: analytics_rag" messages during
initialization - this is the RAG system loading method cards for intelligent 
agent routing and method selection.
"""

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
from src.utils.database import DatabaseManager


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def main():
    """Run profiling, preprocessing, and modeling examples."""
    
    print("=" * 80)
    print("Profiling, Preprocessing & Modeling - Example Usage")
    print("=" * 80)
    
    # Initialize orchestrator
    print("\n1. Initializing orchestrator...")
    orchestrator = AgentOrchestrator()
    
    # Example queries demonstrating different terminology
    queries = [
        # Query 1: Data Profiling / EDA
        {
            "query": "Can you do EDA on the customer demographics data? Show me data quality issues.",
            "description": "Using 'EDA' terminology - should trigger profiling agent"
        },
        
        # Query 2: Data Exploration
        {
            "query": "Explore the store sales data and check for missing values",
            "description": "Using 'explore' terminology - should trigger profiling agent"
        },
        
        # Query 3: Feature Engineering
        {
            "query": "Get customer sales data and apply feature engineering to prepare it for modeling",
            "description": "Using 'feature engineering' terminology - should trigger preprocessing"
        },
        
        # Query 4: Data Transformation
        {
            "query": "Transform and clean the customer data - encode categorical variables and scale numeric features",
            "description": "Using 'transform/encode/scale' terminology - should trigger preprocessing"
        },
        
        # Query 5: Predictive Modeling
        {
            "query": "Build a model to predict customer lifetime value using store sales and demographics",
            "description": "Modeling query - should trigger profiling → preprocessing → modeling"
        },
        
        # Query 6: Multi-turn workflow - preprocessing reuse
        {
            "query": "Now build a random forest classification model to predict customer churn",
            "description": "Modeling query after preprocessing - should trigger profiling → preprocessing → modeling"
        }
    ]
    
    print("\n2. Running profiling, preprocessing, and modeling examples...\n")
    
    # Run each query
    for i, example in enumerate(queries, 1):
        print_section(f"Query {i}: {example['query'][:60]}...")
        print(f"📝 Description: {example['description']}")
        print()
        
        try:
            # Execute query
            result = orchestrator.run(example["query"])
            
            # Print results
            print(f"\n✅ Final Answer:")
            final_resp = getattr(result, "final_response", "No response")
            print(final_resp[:500] + "..." if len(final_resp) > 500 else final_resp)
            
            # Show agent chain
            if hasattr(result, "agent_chain") and result.agent_chain:
                print(f"\n🔄 Agent Chain: {' → '.join(result.agent_chain)}")
            
            # Show plan type and routing tier
            if hasattr(result, "metadata") and result.metadata:
                print(f"📊 Plan Type: {result.metadata.get('plan_type', 'N/A')}")
                print(f"🎯 Routing Tier: {result.metadata.get('routing_tier', 'N/A')}")
            
            # Show data profiling results if available
            if hasattr(result, "data_profile") and result.data_profile:
                print(f"\n📈 Data Profile Generated: ✅")
                profile = result.data_profile
                print(f"   - Rows: {profile.get('row_count', 'N/A')}")
                print(f"   - Columns: {profile.get('column_count', 'N/A')}")
                print(f"   - Missing values: {profile.get('missing_count', 'N/A')}")
            
            # Show preprocessing results if available
            if hasattr(result, "preprocessing_applied") and result.preprocessing_applied:
                print(f"\n🔧 Preprocessing Applied: ✅")
                transformations = result.preprocessing_applied
                for j, transform in enumerate(transformations[:5], 1):
                    print(f"   {j}. {transform}")
                if len(transformations) > 5:
                    print(f"   ... and {len(transformations) - 5} more")
            
            # Show model results if available
            if hasattr(result, "model_results") and result.model_results:
                print(f"\n🤖 Model Trained: ✅")
                print(f"   Model Type: {result.model_results.get('model_type', 'N/A')}")
                if result.model_results.get('metrics'):
                    print(f"   Metrics: {result.model_results['metrics']}")
            
            # Show preprocessing reuse prompt if available
            if hasattr(result, "preprocessing_reuse_prompt") and result.preprocessing_reuse_prompt:
                print(f"\n⚠️  Preprocessing Reuse Confirmation:")
                print(result.preprocessing_reuse_prompt)
            
            # Show errors if any
            if hasattr(result, "errors") and result.errors:
                print(f"\n⚠️  Errors:")
                for error in result.errors:
                    print(f"   - ❌ {error}")
            
        except Exception as e:
            print(f"\n❌ Error executing query: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print_section("Example Complete!")
    print("\nKey Takeaways:")
    print("✅ System recognizes alternative terminology:")
    print("   - 'EDA', 'explore', 'profile' → Profiling Agent")
    print("   - 'feature engineering', 'transform', 'preprocess' → Preprocessing Agent")
    print("   - 'predict', 'model', 'classify' → Full pipeline (profiling → preprocessing → modeling)")
    print("\n✅ Multi-turn conversations supported:")
    print("   - Cached data persists across queries")
    print("   - System asks for confirmation before reusing preprocessed data")
    print()


if __name__ == "__main__":
    main()
