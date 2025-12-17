"""
Test script for hybrid routing system.

This demonstrates the 3-tier classifier and improved agent orchestration.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.config import Config
from src.agents.orchestrator import AgentOrchestrator
from src.agents.query_classifier import classify_query, PlanType


def test_classifier():
    """Test the query classifier with various query types."""
    print("=" * 80)
    print("TESTING QUERY CLASSIFIER (3-Tier Hybrid Routing)")
    print("=" * 80)
    
    test_queries = [
        # Tier 1: Regex patterns (should get confidence 1.0 or 0.95)
        "show me all tables in the database",
        "list all columns in the customer table",
        "what tables are available?",
        
        # Tier 2: Keyword scoring (should get confidence 0.85-0.95)
        "plot the sales trend over time",
        "analyze the correlation between price and quantity",
        "create a chart showing customer distribution",
        
        # Mixed queries
        "show me top 10 customers by revenue and visualize it",
        "analyze sales patterns and create a trend graph",
        
        # Ambiguous (may go to Tier 3 LLM)
        "what's happening with our business?",
        "tell me something interesting about the data",
    ]
    
    config = Config()
    
    for query in test_queries:
        plan_type, confidence = classify_query(query, config)
        
        # Determine tier based on confidence
        if confidence == 1.0:
            tier = "T1 (Regex)"
        elif confidence >= 0.95:
            tier = "T1 (Regex Pattern)"
        elif confidence >= 0.85:
            tier = "T2 (Keywords)"
        else:
            tier = "T3 (LLM Fallback)"
        
        print(f"\nQuery: {query}")
        print(f"  Plan: {plan_type.value}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Routing Tier: {tier}")


def test_orchestrator():
    """Test the full orchestrator with a simple query."""
    print("\n" + "=" * 80)
    print("TESTING ORCHESTRATOR")
    print("=" * 80)
    
    config = Config()
    orchestrator = AgentOrchestrator(config)
    
    # Test with a simple metadata query (should be fast)
    test_query = "show me what tables are in the database"
    
    print(f"\nQuery: {test_query}")
    print("-" * 80)
    
    try:
        result = orchestrator.run(test_query)
        
        print("\n✓ Orchestrator completed successfully!")
        print(f"Plan Type: {result.plan_type}")
        print(f"Confidence: {result.confidence_score}")
        print(f"Agent Chain: {' → '.join(result.agent_chain)}")
        print(f"Routing Tier: {result.metadata.get('routing_tier', 'Unknown')}")
        
        if result.errors:
            print(f"\n⚠ Errors encountered: {result.errors}")
        
        if result.final_response:
            print(f"\nResponse Preview: {result.final_response[:200]}...")
        
        # Show metrics
        print("\n" + "-" * 80)
        print("ROUTING METRICS:")
        metrics = orchestrator.get_metrics()
        print(f"Total queries: {metrics.get('total_queries', 0)}")
        if 'tier_percentages' in metrics:
            for tier, pct in metrics['tier_percentages'].items():
                print(f"  {tier}: {pct:.1f}%")
        
        print("\nAGENT LATENCIES:")
        for agent, latency in metrics['agent_latencies'].items():
            print(f"  {agent}: {latency*1000:.1f}ms")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Hybrid Routing System Test")
    print("Testing 3-tier classifier (Regex → Keywords → LLM)")
    print()
    
    # Test classifier
    test_classifier()
    
    # Test full orchestrator (requires database connection)
    print("\n" + "=" * 80)
    response = input("\nTest full orchestrator? (requires database) [y/N]: ")
    if response.lower() == 'y':
        test_orchestrator()
    else:
        print("Skipping orchestrator test.")
    
    print("\n" + "=" * 80)
    print("Test complete!")
