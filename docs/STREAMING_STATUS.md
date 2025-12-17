# Streaming Agent Reasoning

## Overview

The system now provides **real-time streaming updates** showing what each agent is doing during query processing. This gives users immediate visibility into the multi-agent workflow without waiting for the final result.

## Features

### Live Agent Status
- **Classifier**: Shows query analysis and execution plan
- **SQL Agent**: Displays SQL generation, execution, and row count
- **Analysis Agent**: Shows when statistical analysis is running
- **Visualization Agent**: Indicates chart generation progress
- **Communication Agent**: Shows response preparation

### Status Indicators
- **🔍 Classifier**: Analyzing query type
- **💾 SQL Agent**: Generating and executing SQL
- **📊 Analysis Agent**: Running statistical analysis
- **📈 Visualization Agent**: Creating visualization
- **💬 Communication Agent**: Preparing response

### Visual Feedback
- **Yellow** (⚠️): Agent currently running
- **Green** (✓): Agent completed successfully
- Updates appear in real-time as agents execute

## Implementation

### Callback System

**Orchestrator** (`src/agents/orchestrator.py`):
```python
def __init__(self, status_callback=None):
    """
    Args:
        status_callback: Optional function(agent_name, message, status)
            - agent_name: str (e.g., "sql_agent")
            - message: str (e.g., "✓ Retrieved 1,000 rows")
            - status: str ("running" or "complete")
    """
```

**Agent Execution Examples**:
```python
# Start of agent
if self.status_callback:
    self.status_callback("sql_agent", "💾 Generating and executing SQL query...", "running")

# After completion
if self.status_callback:
    self.status_callback("sql_agent", f"✓ Retrieved {row_count:,} rows", "complete")
```

### Streamlit Integration

**App** (`src/app.py`):
```python
# Create status placeholder
status_placeholder = st.empty()
status_messages = []

def update_status(agent_name: str, message: str, status: str):
    """Update streaming status display."""
    # Track messages for each agent
    # Build colored HTML display
    # Update placeholder in real-time
    status_placeholder.markdown(status_html, unsafe_allow_html=True)

# Initialize orchestrator with callback
orchestrator = AgentOrchestrator(
    smart_limit=True,
    smart_limit_rows=1000,
    status_callback=update_status  # <-- Enables streaming
)
```

## Example Flow

**User Query**: "Show me top 10 customers by sales"

**Streaming Output**:
```
🔍 Analyzing query type...
🔍 ✓ Plan: sql_viz (confidence: 95%)
💾 Generating and executing SQL query...
💾 ✓ Retrieved 10 rows
📈 Creating visualization...
📈 ✓ Chart generated
💬 Preparing response...
💬 ✓ Response ready
```

**User Query**: "Analyze sales trends by region and create a chart"

**Streaming Output**:
```
🔍 Analyzing query type...
🔍 ✓ Plan: sql_analysis_viz (confidence: 98%)
💾 Generating and executing SQL query...
💾 ✓ Retrieved 1,247 rows
📊 Running statistical analysis...
📊 ✓ Analysis complete
📈 Creating visualization...
📈 ✓ Chart generated
💬 Preparing response...
💬 ✓ Response ready
```

## Benefits

### For Users
- **Transparency**: See exactly what the system is doing
- **Progress indication**: Know which stage is executing
- **Confidence**: Understand the workflow (not a black box)
- **Debugging**: Identify which agent is slow or failing

### For Developers
- **Monitoring**: Track agent execution in production
- **Performance**: Identify bottlenecks (which agent is slow?)
- **Error handling**: Know where failures occur
- **User experience**: Reduce perceived wait time

## Configuration

### Enable/Disable Streaming

**With streaming** (default now):
```python
orchestrator = AgentOrchestrator(
    status_callback=update_status  # Enables streaming
)
```

**Without streaming** (silent execution):
```python
orchestrator = AgentOrchestrator(
    status_callback=None  # No streaming
)
```

### Customize Messages

Edit status messages in `src/agents/orchestrator.py`:
```python
# Current messages
"💾 Generating and executing SQL query..."
"✓ Retrieved {row_count:,} rows"

# Can be customized to:
"💾 Querying database..."
"✓ Found {row_count:,} records"
```

### Customize Styling

Edit status display in `src/app.py`:
```python
def update_status(agent_name, message, status):
    color = "#28a745" if status == "complete" else "#ffc107"  # Green/Yellow
    # Change colors, fonts, icons as needed
```

## Performance Impact

- **Minimal overhead**: Callback adds ~0.1ms per agent
- **No blocking**: Status updates don't slow down agents
- **Streamlit-optimized**: Uses `st.empty()` placeholder (efficient)

## Future Enhancements

1. **Progress bars**: Add percentage completion for long-running agents
2. **Time estimates**: "SQL Agent: ~2s remaining"
3. **Error states**: Red color for failed agents with error details
4. **Collapsible history**: Show full execution trace for debugging
5. **Agent metrics**: Display execution times inline
6. **Retry controls**: Allow users to retry failed agents
7. **Parallel visualization**: Show multiple agents running concurrently
8. **Export logs**: Download execution trace for troubleshooting

## Testing

Test with various query types:

```python
# Simple query (SQL only)
"show me 10 customers"
→ Classifier → SQL Agent → Communication Agent

# Analysis query
"what are the statistics for sales data?"
→ Classifier → SQL Agent → Analysis Agent → Communication Agent

# Visualization query
"create a chart of sales by region"
→ Classifier → SQL Agent → Visualization Agent → Communication Agent

# Full pipeline
"analyze customer trends and visualize"
→ Classifier → SQL Agent → Analysis Agent → Visualization Agent → Communication Agent
```

## Troubleshooting

**Status not updating?**
- Ensure `status_callback` is passed to orchestrator
- Check that `update_status()` is defined before orchestrator init
- Verify `status_placeholder` exists

**Status shows but doesn't clear?**
- Ensure `status_placeholder.empty()` is called after completion
- Check for exceptions preventing cleanup

**Duplicate status messages?**
- Check if orchestrator is re-initialized on every query (expected behavior)
- Messages should clear between queries

## Code References

- **Orchestrator callbacks**: `src/agents/orchestrator.py` lines 20, 216, 227, 238, 249, 260
- **App integration**: `src/app.py` lines 483-510
- **Status styling**: `src/app.py` lines 495-507
