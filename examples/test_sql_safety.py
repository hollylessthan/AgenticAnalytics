"""
Test script for SQL Safety Validation.

Tests that dangerous SQL operations are blocked and SQL injection
patterns are detected.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.config import Config
from src.agents.sql_agent import SQLAgent


def test_sql_safety_validation():
    """Test SQL safety validation."""
    print("=" * 60)
    print("SQL SAFETY VALIDATION TEST")
    print("=" * 60)
    
    config = Config()
    agent = SQLAgent(config)
    
    # Test cases: (sql_query, should_pass, description)
    test_cases = [
        # Safe queries (should pass)
        ("SELECT * FROM customers", True, "Basic SELECT"),
        ("SELECT name, email FROM users WHERE active = 1", True, "SELECT with WHERE"),
        ("SELECT COUNT(*) FROM orders", True, "SELECT with aggregate"),
        ("SELECT a.*, b.name FROM orders a JOIN customers b ON a.customer_id = b.id", True, "SELECT with JOIN"),
        ("WITH cte AS (SELECT * FROM sales) SELECT * FROM cte", True, "SELECT with CTE"),
        ("SELECT * FROM products ORDER BY price DESC LIMIT 10;", True, "SELECT with semicolon"),
        
        # Dangerous operations (should fail)
        ("DELETE FROM customers WHERE id = 1", False, "DELETE operation"),
        ("DROP TABLE users", False, "DROP TABLE"),
        ("DROP DATABASE production", False, "DROP DATABASE"),
        ("TRUNCATE TABLE orders", False, "TRUNCATE operation"),
        ("ALTER TABLE users ADD COLUMN password VARCHAR(255)", False, "ALTER TABLE"),
        ("CREATE TABLE temp (id INT)", False, "CREATE TABLE"),
        ("INSERT INTO users VALUES (1, 'hacker')", False, "INSERT operation"),
        ("UPDATE users SET role = 'admin' WHERE id = 1", False, "UPDATE operation"),
        ("REPLACE INTO users VALUES (1, 'test')", False, "REPLACE operation"),
        ("GRANT ALL ON database.* TO 'user'@'localhost'", False, "GRANT privileges"),
        ("REVOKE ALL ON database.* FROM 'user'@'localhost'", False, "REVOKE privileges"),
        
        # SQL injection patterns (should fail)
        ("SELECT * FROM users WHERE id = 1; DROP TABLE users;", False, "SQL injection - multiple statements"),
        ("SELECT * FROM users -- comment", False, "SQL injection - SQL comment"),
        ("SELECT * FROM users /* comment */ WHERE id = 1", False, "SQL injection - multi-line comment"),
        ("SELECT * FROM users UNION SELECT * FROM passwords", False, "SQL injection - UNION SELECT"),
        ("SELECT * FROM users UNION ALL SELECT * FROM admin", False, "SQL injection - UNION ALL"),
        ("SELECT * FROM files INTO OUTFILE '/etc/passwd'", False, "SQL injection - file write"),
        ("SELECT LOAD_FILE('/etc/passwd')", False, "SQL injection - file read"),
        ("EXEC xp_cmdshell 'dir'", False, "SQL injection - command execution"),
        
        # Edge cases
        ("", False, "Empty query"),
        ("   ", False, "Whitespace only"),
        ("EXPLAIN SELECT * FROM users", False, "Non-SELECT start (EXPLAIN)"),
        ("SHOW TABLES", False, "Non-SELECT start (SHOW)"),
    ]
    
    passed = 0
    failed = 0
    
    for i, (sql, should_pass, description) in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {description}")
        print(f"{'='*60}")
        print(f"Query: {sql[:100]}{'...' if len(sql) > 100 else ''}")
        print(f"Expected: {'PASS' if should_pass else 'BLOCK'}")
        
        is_safe, msg = agent._validate_sql_safety(sql)
        print(f"Result: {'SAFE' if is_safe else 'BLOCKED'}")
        print(f"Message: {msg}")
        
        # Verify result matches expectation
        try:
            if should_pass:
                assert is_safe, f"Expected query to pass but was blocked: {msg}"
                print("✅ PASSED")
                passed += 1
            else:
                assert not is_safe, f"Expected query to be blocked but passed"
                print("✅ PASSED (correctly blocked)")
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
        print("✅ SQL injection protection is working correctly")
        print("✅ Dangerous operations are being blocked")
    else:
        print(f"\n⚠️  {failed} TEST(S) FAILED")
    
    return failed == 0


if __name__ == "__main__":
    success = test_sql_safety_validation()
    sys.exit(0 if success else 1)
