# SQL Security & Validation

## Overview
The SQL Agent now includes comprehensive security validation to prevent dangerous operations and SQL injection attacks. All queries are validated before execution.

## Security Features

### 1. Read-Only Enforcement
**Only SELECT and WITH queries are allowed.**

✅ **Allowed:**
- `SELECT * FROM customers`
- `SELECT COUNT(*) FROM orders WHERE date > '2024-01-01'`
- `WITH cte AS (SELECT ...) SELECT * FROM cte`

❌ **Blocked:**
- `DELETE FROM users WHERE id = 1`
- `DROP TABLE customers`
- `TRUNCATE TABLE orders`
- `INSERT INTO users VALUES (...)`
- `UPDATE products SET price = 0`
- `ALTER TABLE users ADD COLUMN ...`
- `CREATE TABLE temp (...)`

### 2. Dangerous Operation Detection
The following operations are automatically blocked:

| Operation | Risk | Example |
|-----------|------|---------|
| DELETE | Data loss | `DELETE FROM table` |
| DROP | Schema destruction | `DROP TABLE/DATABASE` |
| TRUNCATE | Bulk data deletion | `TRUNCATE TABLE` |
| ALTER | Schema modification | `ALTER TABLE ADD COLUMN` |
| CREATE | Unauthorized objects | `CREATE TABLE/VIEW` |
| INSERT | Data injection | `INSERT INTO table VALUES` |
| UPDATE | Data corruption | `UPDATE table SET column = value` |
| GRANT/REVOKE | Privilege escalation | `GRANT ALL PRIVILEGES` |
| EXECUTE/EXEC/CALL | Code execution | `EXEC stored_procedure` |

### 3. SQL Injection Prevention
Detects and blocks common SQL injection patterns:

| Pattern | Attack Type | Example |
|---------|-------------|---------|
| `--` | SQL comment | `SELECT * FROM users WHERE id = 1 -- ` |
| `/* */` | Multi-line comment | `SELECT * /* DROP TABLE */ FROM users` |
| `;` (multiple) | Statement chaining | `SELECT *; DROP TABLE users;` |
| `UNION SELECT` | Union-based injection | `SELECT * FROM users UNION SELECT * FROM passwords` |
| `INTO OUTFILE` | File write | `SELECT * INTO OUTFILE '/etc/passwd'` |
| `LOAD_FILE` | File read | `SELECT LOAD_FILE('/etc/passwd')` |
| `XP_CMDSHELL` | Command execution (SQL Server) | `EXEC xp_cmdshell 'dir'` |
| `DBMS_JAVA` | Java execution (Oracle) | `EXEC DBMS_JAVA...` |
| `UTL_FILE` | File operations (Oracle) | Oracle file exploits |

### 4. LLM Prompt Security
The SQL generation prompt explicitly instructs the LLM:

```
CRITICAL RULES:
5. ONLY generate SELECT or WITH queries (READ-ONLY operations)
6. NEVER generate DELETE, DROP, INSERT, UPDATE, TRUNCATE, ALTER, or any data-modifying operations
7. Do NOT include SQL comments (--) or multiple statements (;;)

SECURITY: You are operating in read-only mode. Any attempt to modify data will be blocked.
```

## Validation Process

```
User Query: "Delete all customers"
         ↓
    LLM generates SQL
         ↓
SQL: "DELETE FROM customers"
         ↓
   Security Validation
         ↓
🚫 BLOCKED: "Dangerous operation detected: DELETE"
         ↓
Error returned to user (query not executed)
```

## Error Messages

When a query is blocked, users see clear error messages:

```
❌ SQL Security Validation Failed: Dangerous operation detected: DELETE
Blocked query: DELETE FROM customers WHERE inactive = 1
```

## Validation Logic

```python
def _validate_sql_safety(sql_query: str) -> tuple[bool, str]:
    # 1. Check for dangerous keywords
    if 'DELETE ' in query or 'DROP ' in query:
        return False, "Dangerous operation detected"
    
    # 2. Check for SQL injection patterns
    if '--' in query or 'UNION SELECT' in query:
        return False, "Potential SQL injection detected"
    
    # 3. Ensure SELECT-only
    if not query.startswith('SELECT') and not query.startswith('WITH'):
        return False, "Only SELECT queries allowed"
    
    # 4. Check for multiple statements
    if query.count(';') > 1:
        return False, "Multiple statements detected"
    
    return True, "Query validated successfully"
```

## Testing

Run the SQL safety test suite:
```bash
python examples/test_sql_safety.py
```

Tests cover:
- ✅ Safe SELECT queries (should pass)
- ✅ Dangerous operations (should block)
- ✅ SQL injection patterns (should block)
- ✅ Edge cases (empty queries, non-SELECT starts)

## Configuration

### Disabling Validation (Not Recommended)
If you need to disable validation for testing:

```python
# In sql_agent.py
def execute(self, state: AgentState) -> AgentState:
    # Comment out validation
    # is_safe, validation_msg = self._validate_sql_safety(sql_query)
    # if not is_safe:
    #     raise ValueError(validation_msg)
```

**⚠️ WARNING: Only do this in isolated development environments!**

## Best Practices

### 1. Use Database User Permissions
Create a read-only database user:

```sql
-- PostgreSQL
CREATE USER analytics_readonly WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE mydb TO analytics_readonly;
GRANT USAGE ON SCHEMA public TO analytics_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO analytics_readonly;

-- MySQL
CREATE USER 'analytics_readonly'@'localhost' IDENTIFIED BY 'secure_password';
GRANT SELECT ON mydb.* TO 'analytics_readonly'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Use Dedicated Analytics Database
Point the agent to a read-only replica or analytics-specific database:

```env
DATABASE_URL=postgresql://readonly_user:password@analytics-replica:5432/analytics_db
```

### 3. Monitor Query Logs
Enable query logging to detect suspicious patterns:

```python
# In sql_agent.py execute method
print(f"[SQL Agent] Query validated: {sql_query[:200]}")
# Log to file or monitoring system
```

### 4. Rate Limiting (Future Enhancement)
Consider adding rate limits to prevent abuse:
- Max queries per minute per user
- Max query execution time
- Max result set size

## Limitations

### What This Protects Against:
✅ Accidental data modification
✅ LLM-generated dangerous queries
✅ Common SQL injection patterns
✅ Malicious user input

### What This Does NOT Protect Against:
❌ Complex injection via encoded strings
❌ Time-based blind SQL injection (info disclosure)
❌ Database server vulnerabilities
❌ Network-level attacks
❌ Compromised LLM API keys

**Defense in depth:** Use database permissions, network security, and input validation in addition to this SQL validation.

## Compliance

This security layer helps meet compliance requirements:
- **GDPR**: Prevents unauthorized data deletion
- **SOX**: Audit trail for query validation
- **HIPAA**: Read-only access to sensitive data
- **PCI-DSS**: Protects against SQL injection

## Future Enhancements

1. **Allowlist Mode**: Only allow pre-approved query patterns
2. **Table-Level Permissions**: Restrict access to specific tables
3. **Data Masking**: Auto-mask sensitive columns (SSN, credit cards)
4. **Query Complexity Limits**: Block queries with too many JOINs or subqueries
5. **Semantic Analysis**: Use ML to detect anomalous query patterns
6. **Real-time Alerts**: Notify admins of blocked dangerous queries
