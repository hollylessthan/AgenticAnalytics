# Agent Retry Configuration & Implementation

## Overview

All agents now support automatic retry with exponential backoff when they fail. This improves robustness against transient errors, LLM API timeouts, and temporary database issues.

## Configuration

### Environment Variables

Add these to your `.env` file to customize retry behavior:

```env
# Default: 2 retries per agent
AGENT_RETRY_COUNT=2

# Default: 500ms initial delay between retries
AGENT_RETRY_DELAY_MS=500
```

### Examples

**Conservative (for production):**
```env
AGENT_RETRY_COUNT=3
AGENT_RETRY_DELAY_MS=1000
```

**Aggressive (for fast APIs):**
```env
AGENT_RETRY_COUNT=1
AGENT_RETRY_DELAY_MS=100
```

**Very Resilient (for unstable connections):**
```env
AGENT_RETRY_COUNT=5
AGENT_RETRY_DELAY_MS=2000
```

### Programmatic Configuration

```python
from src.config import Config

# Create custom config
config = Config(
    agent_retry_count=3,
    agent_retry_delay_ms=1000
)

# Orchestrator automatically uses these values
orchestrator = AgentOrchestrator(config=config)
```

## How It Works

### Retry Behavior

When an agent fails:

1. **Attempt 1**: Initial execution
2. **Wait**: agent_retry_delay_ms (500ms default)
3. **Attempt 2**: First retry
4. **Wait**: agent_retry_delay_ms × 2 (exponential backoff, 1000ms)
5. **Attempt 3**: Second retry
6. **Final**: If all retries fail, error is added to state.errors and execution continues

### Example Execution Flow

```
[SQL Agent] Attempt 1/3 failed: ConnectionError: Connection timeout
[SQL Agent] Retrying in 0.5s... (Attempt 1/2)
[SQL Agent] Attempt 2/3 failed: ConnectionError: Connection timeout
[SQL Agent] Retrying in 1.0s... (Attempt 2/2)
[SQL Agent] Attempt 3/3 succeeded! ✓
```

## Implementation Details

### Base Agent Class

All agents inherit from `BaseAgent` which provides:

```python
def execute_with_retry(
    self,
    state: AgentState,
    execute_func: Callable[[AgentState], AgentState],
    max_retries: int = None,
    initial_delay_ms: int = None
) -> AgentState:
    """Execute function with automatic retry on failure."""
```

### Agent Implementations

Each agent wraps their main logic in retry:

**Before:**
```python
def execute(self, state: AgentState) -> AgentState:
    # Try to do work, catch exceptions, add to errors, return state
    try:
        # Implementation
    except Exception as e:
        state.errors.append(str(e))
    return state
```

**After:**
```python
def execute(self, state: AgentState) -> AgentState:
    # Use retry wrapper
    return self.execute_with_retry(state, self._execute_impl)

def _execute_impl(self, state: AgentState) -> AgentState:
    # Implementation - exceptions are re-raised to retry handler
    # Implementation
    return state
```

## Agents with Retry Support

✅ **SQL Agent** - Retries on query generation/execution failures  
✅ **Analysis Agent** - Retries on code generation/execution failures  
✅ **Visualization Agent** - Retries on code generation/visualization failures  
✅ **Communication Agent** - Retries on LLM response generation failures  

## Error Handling Strategy

### Retryable Errors

These errors will trigger retries:
- API timeouts
- Temporary network issues
- LLM rate limits
- Database connection issues
- Transient memory errors

### Non-Retryable Errors

These fail immediately without retry:
- SQL syntax errors
- Security validation failures
- Missing columns/tables
- Empty result sets

### Example: SQL Agent Error Handling

```python
# This will retry: API timeout generating SQL
ConnectionError: Request timed out

# This will NOT retry: Invalid SQL syntax
ValueError: SQL Security Validation Failed

# This will retry: Database connection issue
psycopg2.OperationalError: Connection refused

# This will NOT retry: Column doesn't exist
KeyError: 'column_name' not found in results
```

## Monitoring Retries

### Console Output

Look for retry messages:
```
[sql_agent] Attempt 1/3 failed: ConnectionError: Connection timeout
[sql_agent] Retrying in 0.5s... (Attempt 1/2)
[sql_agent] Attempt 2/3 succeeded! ✓
```

### Logging

Enable debug logging to see detailed retry information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Best Practices

1. **Start Conservative**: Use default 2 retries, increase if needed
2. **Monitor Failures**: Watch agent logs to identify patterns
3. **Adjust Delays**: Match your API characteristics
   - Slow APIs: Increase AGENT_RETRY_DELAY_MS
   - Fast APIs: Decrease AGENT_RETRY_DELAY_MS
4. **Don't Retry Too Much**: >3 retries usually indicates a deeper issue
5. **Check State.Errors**: Even successful retries log non-fatal errors

## Troubleshooting

### Agent keeps failing after retries

Check state.errors for the actual error message:

```python
# In orchestrator
if state.errors:
    for error in state.errors:
        print(f"Agent Error: {error}")
```

### Retries taking too long

Reduce retry count or initial delay:

```env
AGENT_RETRY_COUNT=1
AGENT_RETRY_DELAY_MS=200
```

### Still failing despite retries

Likely a non-retryable error:
- Check SQL syntax
- Verify database connectivity
- Confirm column names exist
- Check API key/authentication

## Example: Custom Retry Policy per Agent

```python
# For SQL agent, be more aggressive
sql_agent.execute_with_retry(
    state,
    sql_agent._execute_impl,
    max_retries=3,
    initial_delay_ms=200
)

# For communication agent, be more conservative
comm_agent.execute_with_retry(
    state,
    comm_agent._execute_impl,
    max_retries=1,
    initial_delay_ms=500
)
```

## Files Modified

- `src/config.py` - Added retry configuration
- `src/agents/base.py` - Added execute_with_retry() method
- `src/agents/sql_agent.py` - Wrapped execute() with retry
- `src/agents/analysis_agent.py` - Wrapped execute() with retry
- `src/agents/visualization_agent.py` - Wrapped execute() with retry
- `src/agents/communication_agent.py` - Wrapped execute() with retry
- `src/utils/retry.py` - Retry utilities (decorator & config)

## Testing Retries

### Test with simulated failures:

```python
# Mock a transient failure
from unittest.mock import patch

# First call fails, second succeeds
with patch.object(db_manager, 'execute_query') as mock:
    mock.side_effect = [ConnectionError("Timeout"), [{"col": "val"}]]
    
    orchestrator = AgentOrchestrator(config)
    result = orchestrator.execute("Show me data")
    
    # Verify it retried (2 calls made)
    assert mock.call_count == 2
```

## Future Enhancements

- [ ] Circuit breaker pattern (fail fast if repeated failures)
- [ ] Adaptive backoff (learn optimal retry patterns)
- [ ] Jitter in delays (prevent thundering herd)
- [ ] Per-agent customization in config
- [ ] Metrics collection on retry success rate
