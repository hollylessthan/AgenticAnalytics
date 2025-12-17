"""
Test script for Smart LIMIT feature.

Tests that the SQL agent automatically adds LIMIT clauses to queries
when smart_limit is enabled.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config
from src.agents.sql_agent import SQLAgent


def test_smart_limit():
    """Test smart limit functionality."""
    print("=" * 60)
    print("SMART LIMIT FEATURE TEST")
    print("=" * 60)
    
    config = Config()
    
    # Test cases
    test_cases = [
        {
            "name": "Query without LIMIT (should add)",
            "input": "SELECT * FROM customers",
            "smart_limit": True,
            "limit_rows": 1000,
            "should_contain": "LIMIT 1000"
        },
        {
            "name": "Query with existing LIMIT (should not modify)",
            "input": "SELECT * FROM orders LIMIT 50",
            "smart_limit": True,
            "limit_rows": 1000,
            "should_contain": "LIMIT 50"
        },
        {
            "name": "Query without LIMIT, smart_limit disabled",
            "input": "SELECT * FROM products",
            "smart_limit": False,
            "limit_rows": 1000,
            "should_not_contain": "LIMIT"
        },
        {
            "name": "Metadata query (should not add LIMIT)",
            "input": "SELECT table_name FROM information_schema.tables",
            "smart_limit": True,
            "limit_rows": 1000,
            "should_not_contain": "LIMIT"
        },
        {
            "name": "COUNT query (should not add LIMIT)",
            "input": "SELECT COUNT(*) FROM sales",
            "smart_limit": True,
            "limit_rows": 1000,
            "should_not_contain": "LIMIT"
        },
        {
            "name": "Query with semicolon (should add LIMIT before semicolon)",
            "input": "SELECT * FROM transactions;",
            "smart_limit": True,
            "limit_rows": 500,
            "should_contain": "LIMIT 500;"
        },
        {
            "name": "Query with TOP (should not add LIMIT)",
            "input": "SELECT TOP 10 * FROM users",
            "smart_limit": True,
            "limit_rows": 1000,
            "should_not_contain": "LIMIT"
        },
        {
            "name": "GROUP BY query (should add LIMIT)",
            "input": "SELECT category, COUNT(*) FROM products GROUP BY category",
            "smart_limit": True,
            "limit_rows": 1000,
            "should_contain": "LIMIT 1000"
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {test['name']}")
        print(f"{'='*60}")
        print(f"Input:  {test['input']}")
        print(f"Smart Limit: {test['smart_limit']} (rows={test['limit_rows']})")
        
        # Create SQL agent
        agent = SQLAgent(
            config=config,
            smart_limit=test['smart_limit'],
            smart_limit_rows=test['limit_rows']
        )
        
        # Apply smart limit
        result = agent._apply_smart_limit(test['input'])
        print(f"Output: {result}")
        
        # Verify
        try:
            if 'should_contain' in test:
                assert test['should_contain'] in result, \
                    f"Expected to contain '{test['should_contain']}'"
                print(f"✅ PASSED: Contains '{test['should_contain']}'")
                passed += 1
            elif 'should_not_contain' in test:
                assert test['should_not_contain'] not in result, \
                    f"Should not contain '{test['should_not_contain']}'"
                print(f"✅ PASSED: Does not contain '{test['should_not_contain']}'")
                passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {str(e)}")
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
    
    return failed == 0


if __name__ == "__main__":
    success = test_smart_limit()
    sys.exit(0 if success else 1)
