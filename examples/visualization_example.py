"""Example: Advanced visualization workflows."""

from src.agents.orchestrator import AgentOrchestrator
from src.utils.database import DatabaseManager
import pandas as pd


def main():
    """Demonstrate advanced visualization capabilities."""
    
    print("Advanced Visualization Example")
    print("=" * 60)
    
    # Initialize
    orchestrator = AgentOrchestrator()
    
    # Example 1: Time series visualization
    print("\n1. Time Series Analysis")
    print("-" * 60)
    
    query1 = "Create a line chart showing sales trends over time"
    result1 = orchestrator.run(query1)
    
    print(f"Query: {query1}")
    print(f"SQL: {result1.sql_query}")
    print(f"Visualization: {result1.visualization_path}")
    print(f"Answer: {result1.final_answer}")
    
    # Example 2: Category comparison
    print("\n2. Category Comparison")
    print("-" * 60)
    
    query2 = "Show me a bar chart of total sales by product category"
    result2 = orchestrator.run(query2)
    
    print(f"Query: {query2}")
    print(f"Visualization: {result2.visualization_path}")
    
    # Example 3: Distribution analysis
    print("\n3. Distribution Analysis")
    print("-" * 60)
    
    query3 = "Create a histogram of order amounts to see the distribution"
    result3 = orchestrator.run(query3)
    
    print(f"Query: {query3}")
    print(f"Visualization: {result3.visualization_path}")
    
    # Example 4: Correlation heatmap
    print("\n4. Correlation Analysis")
    print("-" * 60)
    
    query4 = "Show me a heatmap of correlations between product price, quantity, and total sales"
    result4 = orchestrator.run(query4)
    
    print(f"Query: {query4}")
    print(f"Visualization: {result4.visualization_path}")
    
    print("\n" + "=" * 60)
    print("All visualizations saved to outputs/visualizations/")
    print("=" * 60)


if __name__ == "__main__":
    main()
