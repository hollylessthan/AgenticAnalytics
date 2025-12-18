# Error-Aware Retry Mechanism

## Overview

The Analysis and Visualization agents now include an intelligent error-aware retry mechanism. When code generation fails (e.g., invalid Python code, incorrect column names), the agent **analyzes the error and regenerates corrected code** instead of blindly retrying the same code.

## How It Works

### Traditional Retry (Old)
```
Attempt 1: Generate code → Execute → FAILS with "NameError: 'x' is not defined"
          ↓ (wait 500ms)
Attempt 2: Generate SAME code → Execute → FAILS with SAME error
          ↓ (wait 1s)
Attempt 3: Generate SAME code → Execute → FAILS again
          ↓
Result: ❌ Error
```

### Error-Aware Retry (New)
```
Attempt 1: Generate code → Execute → FAILS with "KeyError: 'column_name'"
          ↓ (CAPTURE ERROR)
Attempt 2: LLM sees error → Regenerates corrected code → Execute → SUCCESS ✓
```

## Agents with Error-Aware Retry

### 1. SQL Agent
- **Triggers**: SQL syntax errors and execution errors
- **What it fixes**:
  - Missing or incorrect column names
  - Missing or incorrect table names
  - SQL syntax errors
  - Type mismatches in queries
  - Ambiguous column references
  - Invalid JOIN conditions

**Example**:
```sql
-- User asks: "Select customer names and their orders"
-- LLM generates: SELECT name, orders FROM customers;
-- Error: "unknown column 'orders'"
-- 
-- LLM sees error and regenerates:
-- SELECT c.name, COUNT(o.id) as orders 
-- FROM customers c LEFT JOIN orders o ON c.id = o.customer_id
-- GROUP BY c.id;
-- SUCCESS ✓
```

### 2. Analysis Agent
- **Triggers**: Python code execution errors during data analysis
- **What it fixes**: 
  - KeyError (column doesn't exist)
  - TypeError (type incompatibility)
  - ValueError (invalid parameters)
  - AttributeError (wrong method/attribute names)
  - ZeroDivisionError (division by zero)

**Example**:
```python
# User asks: "Calculate the average of column x"
# LLM generates: results['avg'] = df['column_x'].mean()
# Error: KeyError - no column 'column_x'
# 
# LLM sees error and regenerates:
# results['avg'] = df['x'].mean()  # Uses correct column name
# SUCCESS ✓
```

### 2. Visualization Agent
- **Triggers**: Matplotlib/Seaborn code execution errors
- **What it fixes**:
  - Invalid column references
  - Type mismatches for plotting
  - Unsupported parameter values
  - Invalid method calls

**Example**:
```python
# User asks: "Create a scatter plot"
# LLM generates: ax.scatter(df['x'], df['y'])
# Error: KeyError - column 'y' doesn't exist
#
# LLM sees error and regenerates:
# ax.scatter(df['x'], df['y_value'])  # Uses correct column
# SUCCESS ✓
```

## Configuration

### Retry Attempts
Both agents retry up to **3 times** within their own error-aware loop:

```python
max_code_retries = 3

for attempt in range(max_code_retries):
    # Generate (or regenerate if failed)
    code = self._generate_analysis_code(...)  # or visualization
    
    # Execute
    result = self._execute_analysis(code, df)
    
    # If no error, break early
    if 'error' not in result:
        break
```

### Beyond Code Retries
If the code fails all 3 times, the error bubbles up to the **global retry mechanism** (2 retries with exponential backoff, 500ms-10s delays). This provides a second level of resilience.

### Total Resilience
- **Code generation retries**: 3 attempts (with error feedback)
- **Global agent retries**: 2 attempts (with exponential backoff, 500ms-10s)
- **Total possible attempts**: Up to 5+ tries with intelligent error fixing

Configure global retries in `.env`:
```env
AGENT_RETRY_COUNT=2           # Global retry count
AGENT_RETRY_DELAY_MS=500      # Initial delay
```

## Implementation Details

### Analysis Agent

**Method**: `_execute_impl()`
```python
for attempt in range(max_code_retries):
    if attempt == 0:
        code = self._generate_analysis_code(state.query, df)
    else:
        # Regenerate based on error
        code = self._regenerate_analysis_code(
            state.query, 
            df, 
            analysis_results['error'],      # Error message
            analysis_results['traceback']   # Full traceback
        )
    
    analysis_results = self._execute_analysis(code, df)
    
    if 'error' not in analysis_results:
        break  # Success!
```

**New method**: `_regenerate_analysis_code()`
- Takes the original query, DataFrame, error message, and traceback
- Includes error details in the LLM prompt
- LLM analyzes what went wrong and generates corrected code
- Returns fixed code ready for execution

### SQL Agent

**Method**: `_execute_impl()`
```python
for attempt in range(max_code_retries):
    if attempt == 0:
        query = self._generate_sql_query(state.user_query, db_schema)
    else:
        # Regenerate based on error + schema
        query = self._regenerate_sql_query(
            state.user_query,
            db_schema,
            failed_query,              # The query that failed
            execution_results['error'],  # Error message
            execution_results['traceback']  # Full traceback
        )
    
    execution_results = self._execute_query(query, db_connection)
    
    if 'error' not in execution_results:
        break  # Success!
```

**New method**: `_regenerate_sql_query()`
- Takes the original user request, DB schema, failed query, and error
- Includes database schema context in the LLM prompt
- LLM analyzes the error (missing table/column, syntax, etc.) and regenerates
- Returns corrected SQL ready for execution

### Visualization Agent

**Method**: `_execute_impl()`
- Same pattern as Analysis Agent
- Generates visualization code with error feedback

**New method**: `_regenerate_visualization_code()`
- Same error-aware regeneration logic
- Specialized for matplotlib/seaborn code

### Error Capture

**Method**: `_execute_analysis()` / `_execute_visualization()`
```python
def _execute_analysis(self, code: str, df: pd.DataFrame) -> Dict[str, Any]:
    try:
        exec(code, {...}, local_vars)
        return local_vars.get('results', {})  # Success
    except Exception as e:
        return {
            'error': str(e),              # Error message
            'traceback': traceback.format_exc(),  # Full traceback
            'code': code                  # Original code
        }
```

Returns error details instead of raising, allowing retry logic to analyze and fix.

## Error Examples and Fixes

### SQL Agent Errors

**Missing column name**
```
Error: no such column: 'revenue'
Prompt includes: Available columns in schema
Fix: Change 'revenue' → 'sales_amount' (correct column name)
```

**Missing table name**
```
Error: no such table: 'orders'
Prompt includes: Available tables in schema
Fix: Change 'orders' → 'order_details' (correct table name)
```

**Syntax error**
```
Error: near "SELEC": syntax error
Prompt includes: Schema context
Fix: Correct typo or invalid SQL syntax
```

**Type mismatch**
```
Error: TypeError in comparison
Prompt includes: Column data types from schema
Fix: Cast to appropriate type: CAST(col AS TEXT)
```

**Ambiguous column reference**
```
Error: ambiguous column name: 'id'
Prompt includes: Available tables with this column
Fix: Qualify with table: customer.id
```

### Analysis Agent Errors

**KeyError: Column doesn't exist**
```
Error: KeyError: 'revenue'
Prompt includes: "Column 'revenue' doesn't exist. Available: ['sales', 'amount', 'total']"
Fix: Change df['revenue'] → df['sales']
```

**TypeError: Incompatible types**
```
Error: TypeError: unsupported operand type(s)
Prompt includes: Exact error trace showing types involved
Fix: Add type conversion: float(df['col'].sum())
```

**ValueError: Invalid parameter**
```
Error: ValueError: 0.5 is not in range [0, 100]
Prompt includes: Expected range for the parameter
Fix: Adjust parameter to valid range
```

### Visualization Agent Errors

**KeyError in plotting**
```
Error: KeyError: 'category'
Prompt includes: Available columns in DataFrame
Fix: Use correct column name: df['group'] instead of df['category']
```

**Type error in plot**
```
Error: TypeError: Cannot convert X to numeric
Prompt includes: Column data types
Fix: Convert or select numeric columns for plotting
```

## Limitations

1. **Not all errors are fixable**: Some errors indicate fundamental issues (e.g., empty DataFrame)
2. **LLM quality**: Regenerated code quality depends on LLM understanding the error
3. **Complex logic errors**: Subtle logic bugs may not be caught by execution
4. **Infinite loops**: Code that hangs will timeout (no current timeout implemented)

## Debugging Failed Code

When code fails all 3 attempts:

1. **Check the error message** in logs:
   ```
   [Analysis Agent] Code failed with error: KeyError: 'column_x'
   [Analysis Agent] Regenerating code (attempt 2/3)
   [Analysis Agent] Code failed with error: KeyError: 'column_y'
   ...
   ```

2. **Verify DataFrame contents**:
   - Ask a simple query like "show me the columns" first
   - Confirm actual column names

3. **Simplify the request**:
   - Instead of complex multi-step analysis
   - Ask for single metrics first

4. **Check data types**:
   - Non-numeric columns can't be averaged
   - String columns need different handling

## Future Enhancements

- [ ] Timeout handling for infinite loops
- [ ] Caching of successful code patterns
- [ ] Learning from errors (feedback loop)
- [ ] Custom error handlers for specific error types
- [ ] Metrics on error-aware retry success rate

## Files Modified

- `src/agents/sql_agent.py` - Added `_execute_query()` and `_regenerate_sql_query()`
- `src/agents/analysis_agent.py` - Added `_regenerate_analysis_code()`
- `src/agents/visualization_agent.py` - Added `_regenerate_visualization_code()`
- `src/agents/base.py` - Unchanged (uses existing retry wrapper)

## Testing Error-Aware Retry

```python
# Test with invalid column name
query = "Analyze column that_doesnt_exist"
result = orchestrator.run(query)

# Should see:
# [Analysis Agent] Code failed with error: KeyError: 'that_doesnt_exist'
# [Analysis Agent] Regenerating code (attempt 2/3)
# [Analysis Agent] Successfully generated and executed analysis code ✓
```
