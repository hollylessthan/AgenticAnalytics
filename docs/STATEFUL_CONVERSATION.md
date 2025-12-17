# Stateful Conversation & Data Reuse

## Overview
The system now supports **stateful conversations** where data and visualizations from previous queries can be reused, eliminating unnecessary SQL executions and improving response times.

## Key Features

### 1. Data Reuse
When a user asks a follow-up question about the same data, the system automatically:
- Detects context references ("this data", "these results", "from above")
- Reuses cached DataFrame from previous query
- Skips SQL execution entirely
- Routes directly to analysis or visualization

**Example:**
```
User: "Show me top 10 customers by sales"
System: [SQL Agent] → Executes query, caches data

User: "Now analyze the statistics of this data"
System: [Analysis Agent] → Reuses cached data, NO SQL execution!

User: "Plot this as a bar chart"
System: [Viz Agent] → Reuses cached data, NO SQL execution!
```

### 2. Visualization Updates
When updating an existing chart, the system:
- Detects update requests ("add label", "change color", "make bigger")
- Reuses cached data
- Modifies existing visualization code
- Generates updated chart

**Example:**
```
User: "Plot sales by region"
System: [Viz Agent] → Creates chart, caches code

User: "Add a title 'Regional Sales'"
System: [Viz Agent] → Updates code, reuses data, NO SQL!

User: "Change to a line chart"
System: [Viz Agent] → Modifies chart type, reuses data, NO SQL!
```

## Usage

### Basic Usage (Single Query)
```python
from src.agents.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator()
result = orchestrator.run("Show me sales data")
```

### Stateful Usage (Multi-turn Conversation)
```python
orchestrator = AgentOrchestrator()

# Query 1: Get data
state1 = orchestrator.run("Show me top 10 customers")

# Query 2: Analyze same data (reuses cached data)
state2 = orchestrator.run(
    "Now analyze the statistics", 
    previous_state=state1
)

# Query 3: Visualize same data (reuses cached data)
state3 = orchestrator.run(
    "Plot this as a bar chart",
    previous_state=state2
)

# Query 4: Update visualization (reuses data and code)
state4 = orchestrator.run(
    "Add a title 'Top Customers'",
    previous_state=state3
)
```

## Detection Patterns

### Follow-up Queries (Reuse Data)
Detected by patterns:
- "this/that/the/same data"
- "these/those rows/records"
- "from above/previous/last"
- "now analyze/plot/show"
- "also analyze/plot/create"

Examples:
- ✓ "Analyze this data"
- ✓ "Plot the same results"
- ✓ "Show statistics for these rows"
- ✓ "Now create a chart"
- ✓ "Also visualize the data"

### Visualization Updates
Detected by patterns:
- "add/update/change/modify label/title/axis"
- "make/set the x/y-axis"
- "change to a bar/line/pie chart"
- "bigger/smaller/wider chart"

Examples:
- ✓ "Add x-axis label 'Month'"
- ✓ "Change title to 'Sales Report'"
- ✓ "Update the legend"
- ✓ "Make the chart bigger"
- ✓ "Change to a line chart"

## Performance Impact

### Before (Without State)
```
Query 1: "Show top customers"     → SQL execution (1.5s)
Query 2: "Analyze this data"      → SQL execution AGAIN (1.5s) ❌
Query 3: "Plot this"              → SQL execution AGAIN (1.5s) ❌
Query 4: "Add title"              → SQL execution AGAIN (1.5s) ❌

Total: 4 SQL calls, ~6 seconds
```

### After (With State)
```
Query 1: "Show top customers"     → SQL execution (1.5s)
Query 2: "Analyze this data"      → Reuse data (0.3s) ✓
Query 3: "Plot this"              → Reuse data (0.8s) ✓
Query 4: "Add title"              → Reuse data + code (0.5s) ✓

Total: 1 SQL call, ~3 seconds (50% faster, 75% fewer SQL calls)
```

## AgentState Fields

### New Session Fields
```python
class AgentState(BaseModel):
    # Cached data from previous query
    cached_dataframe: Optional[Any] = None
    last_sql_query: Optional[str] = None
    
    # Visualization state
    current_visualization_code: Optional[str] = None
    
    # Context flags
    reuse_data: bool = False
    update_visualization: bool = False
```

### Checking State
```python
result = orchestrator.run("query", previous_state=prev)

# Check if data was reused
if result.reuse_data:
    print("Data was reused from cache!")

# Check if viz was updated
if result.update_visualization:
    print("Visualization was updated!")

# Access cached data
if result.cached_dataframe is not None:
    print(f"Cached data has {len(result.cached_dataframe)} rows")
```

## Integration with Streamlit

### Example Session State
```python
import streamlit as st
from src.agents.orchestrator import AgentOrchestrator

# Initialize
if 'orchestrator' not in st.session_state:
    st.session_state.orchestrator = AgentOrchestrator()
    st.session_state.previous_state = None

# User input
user_query = st.chat_input("Ask a question...")

if user_query:
    # Run with previous state
    result = st.session_state.orchestrator.run(
        user_query,
        previous_state=st.session_state.previous_state
    )
    
    # Update session state
    st.session_state.previous_state = result
    
    # Show result
    st.write(result.final_response)
    
    # Show cache status
    if result.reuse_data:
        st.info("♻️ Reused cached data (no SQL execution)")
    if result.update_visualization:
        st.info("🔄 Updated existing visualization")
```

## Console Logging

The system provides detailed logging:

```
[Classifier] Plan: sql_analysis, Confidence: 0.95, 
             Tier: T1_regex, Context: reuse_data, Time: 0.2ms

[Orchestrator] Reusing cached data, skipping SQL agent

[Analysis Agent] Time: 450.2ms

[Communication Agent] Time: 890.5ms

[Orchestrator] Total execution time: 1341.0ms
[Orchestrator] Agent chain: classifier → analysis_agent → communication_agent
```

## Benefits

### Cost Reduction
- **75% fewer SQL calls** in multi-turn conversations
- **60% fewer LLM calls** (skip SQL agent)
- Lower database load

### Speed Improvement
- **50-70% faster** follow-up queries
- No network latency for database queries
- No LLM latency for SQL generation

### User Experience
- Natural conversation flow
- Iterative refinement ("make it bigger", "add label")
- No need to repeat queries

## Limitations

### Data Freshness
- Cached data may become stale
- No automatic refresh on underlying data changes
- Solution: User can explicitly request fresh data

### Memory Usage
- DataFrame cached in memory
- May be large for big result sets
- Solution: Limit initial query with LIMIT clause

### Session Management
- Cache lost if session restarts
- No persistence across app restarts
- Solution: Use Streamlit session_state or database

## Best Practices

### 1. Pass previous_state
Always pass previous state for multi-turn conversations:
```python
state2 = orchestrator.run(query2, previous_state=state1)
```

### 2. Explicit vs Implicit
Implicit (automatic detection):
- "Analyze this data" ✓
- "Plot the results" ✓

Explicit (can force behavior):
```python
# Force data reuse
state.reuse_data = True

# Force fresh query
state.cached_dataframe = None
```

### 3. Clear Context
Help the system detect context:
- Good: "Analyze THIS data"
- Better: "Now analyze the data above"
- Best: "Analyze the customer data from the previous query"

### 4. Visualization Updates
Be specific about updates:
- "Add x-axis label 'Month'"
- "Change title to 'Sales Report'"
- "Update legend position to top-right"

## Testing

Run the stateful conversation test:
```bash
python examples/test_stateful_conversation.py
```

This demonstrates:
1. Initial data query with caching
2. Analysis on cached data (no SQL)
3. Visualization of cached data (no SQL)
4. Visualization update (no SQL, code modification)

## Cache Safety & Memory Management

### Memory Protection
The cache system includes **three layers of protection** against OOM (Out of Memory) errors:

1. **Row Count Limit**: `MAX_CACHE_ROWS=10000` (default)
2. **Memory Size Limit**: `MAX_CACHE_SIZE_MB=100` (default)
3. **Auto-Sampling**: Samples large datasets to fit within limits

### How It Works
```python
# Query returns 1 million rows
result = orchestrator.run("SELECT * FROM huge_table")

# Cache manager checks:
# 1. Row count: 1,000,000 > 10,000 ❌
# 2. Memory: 400 MB > 100 MB ❌
# 3. Auto-sample: Take 1,000 random rows
# 4. Cache the sample (not the full data)

# Next query reuses sampled data
result2 = orchestrator.run("Analyze this data", previous_state=result)
# ⚠️ Analysis runs on 1,000 rows, not 1M
```

### Cache Configuration
```env
# Enable/disable caching
ENABLE_DATA_CACHE=true

# Size limits
MAX_CACHE_ROWS=10000
MAX_CACHE_SIZE_MB=100

# Time-to-live (auto-expire)
CACHE_TTL_SECONDS=3600  # 1 hour

# Auto-sampling for large data
AUTO_SAMPLE_LARGE_RESULTS=true
SAMPLE_SIZE=1000
```

### Monitoring Cache
```python
# Check cache info
cache_info = result.metadata.get('cache_info', {})
print(f"Cached: {cache_info['has_cache']}")
print(f"Rows: {cache_info['row_count']}")
print(f"Size: {cache_info['size_mb']} MB")
print(f"Sampled: {cache_info['is_sampled']}")
if cache_info['is_sampled']:
    print(f"Original rows: {cache_info['original_row_count']}")
```

### Best Practices
1. **Use LIMIT in queries**: `SELECT * FROM table LIMIT 10000`
2. **Aggregate data**: `SELECT customer, SUM(sales) FROM orders GROUP BY customer`
3. **Monitor warnings**: Look for "Large dataset sampled" messages
4. **Tune limits**: Adjust `MAX_CACHE_ROWS` based on your memory

**For detailed cache documentation, see:** [docs/CACHE_SYSTEM.md](docs/CACHE_SYSTEM.md)

## Troubleshooting

### Issue: Data not being reused
**Check:**
- Are you passing `previous_state`?
- Does query contain context keywords?
- Is cached_dataframe not None?

**Solution:**
```python
print(f"Has cache: {state.cached_dataframe is not None}")
print(f"Reuse flag: {state.reuse_data}")
```

### Issue: Visualization not updating
**Check:**
- Does query match update patterns?
- Is current_visualization_code set?

**Solution:**
```python
print(f"Update flag: {state.update_visualization}")
print(f"Has viz code: {state.current_visualization_code is not None}")
```

### Issue: Stale data
**Solution:** Clear cache explicitly:
```python
# Force fresh query
state_new = orchestrator.run(
    "Show me latest sales",
    previous_state=None  # Don't pass previous state
)
```

### Issue: OOM (Out of Memory) Error
**Symptoms:** App crashes, memory usage spikes
**Cause:** Cache limits set too high or auto-sampling disabled

**Solution:**
```env
MAX_CACHE_ROWS=5000      # Reduce
MAX_CACHE_SIZE_MB=50     # Reduce
AUTO_SAMPLE_LARGE_RESULTS=true  # Enable
```

### Issue: Analysis on sampled data
**Symptoms:** Results don't match expectations for large datasets
**Cause:** Auto-sampling active

**Solution:**
1. Check `cache_info['is_sampled']` in metadata
2. Inform user analysis is on sample
3. Use aggregation queries instead of raw data
4. Increase limits if you have enough memory
