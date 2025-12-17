# Quick Reference: Hybrid Routing System

## Query Classification

### Plan Types
- `SQL_ONLY` - Simple data retrieval, metadata queries
- `SQL_ANALYSIS` - Data retrieval + statistical analysis
- `SQL_VIZ` - Data retrieval + visualization
- `SQL_ANALYSIS_VIZ` - Data retrieval + analysis + visualization

### Routing Tiers
1. **Tier 1 (Regex)** - <1ms, 95% queries
   - Pattern: "show tables", "list columns", "plot", "analyze"
   
2. **Tier 2 (Keywords)** - <10ms, 4% queries
   - Weighted scoring of keywords
   - Threshold: 0.85 confidence
   
3. **Tier 3 (LLM)** - ~500ms, 1% queries
   - Ambiguous queries
   - Structured Pydantic output

## Agent Responsibilities

### SQL Agent
✓ Generate SQL queries  
✓ Execute queries  
✓ Return results  
✗ No analysis  
✗ No visualization  
✗ No routing decisions  

### Analysis Agent
✓ Statistical analysis  
✓ Correlations, trends, patterns  
✓ Return formatted results  
✗ No visualizations  
✗ No routing decisions  

### Visualization Agent
✓ Create charts/graphs  
✓ Save to outputs/visualizations/  
✓ Return file paths  
✗ No analysis  
✗ No routing decisions  

### Communication Agent
✓ Synthesize responses  
✓ Explain findings  
✓ Safe DataFrame handling  
✓ Suggest next steps  

## Usage Examples

### Basic Query
```python
from src.agents.orchestrator import AgentOrchestrator
from src.config import Config

config = Config()
orchestrator = AgentOrchestrator(config)
result = orchestrator.run("show me all tables")

print(result.final_response)
print(result.agent_chain)  # ['classifier', 'sql_agent', 'communication_agent']
```

### Check Classification
```python
from src.agents.query_classifier import classify_query
from src.config import Config

plan_type, confidence = classify_query("plot sales by region", Config())
print(f"{plan_type.value} (confidence: {confidence})")
# Output: sql_viz (confidence: 0.95)
```

### Get Metrics
```python
orchestrator = AgentOrchestrator()
orchestrator.run("query 1")
orchestrator.run("query 2")
orchestrator.run("query 3")

metrics = orchestrator.get_metrics()
print(f"Total: {metrics['total_queries']}")
print(f"Tier 1: {metrics['tier_percentages']['tier1']:.1f}%")
print(f"Latencies: {metrics['agent_latencies']}")
```

## Debugging

### Enable Console Logs
All agents automatically log:
```
[Classifier] Plan: sql_only, Confidence: 1.00, Tier: T1_regex, Time: 0.5ms
[SQL Agent] Generated query: SELECT...
[SQL Agent] Time: 1234.5ms
[Communication Agent] Time: 567.8ms
[Orchestrator] Total: 1802.3ms
[Orchestrator] Chain: classifier → sql_agent → communication_agent
```

### Check Errors
```python
result = orchestrator.run("your query")
if result.errors:
    print("Errors:", result.errors)
```

### Inspect State
```python
result = orchestrator.run("your query")
print(f"Plan: {result.plan_type}")
print(f"Confidence: {result.confidence_score}")
print(f"SQL: {result.sql_query}")
print(f"Chain: {result.agent_chain}")
print(f"Tier: {result.metadata['routing_tier']}")
```

## Performance Tips

1. **Simple queries** - Use direct language ("show tables", "list X")
2. **Analysis** - Include "analyze", "correlation", "statistics"
3. **Visualization** - Include "plot", "chart", "graph", "visualize"
4. **Combined** - Be explicit: "analyze X and create a chart"

## Common Patterns

### Metadata Queries (Tier 1, SQL_ONLY)
- "show me all tables"
- "list columns in customers"
- "describe the orders table"
- "what tables exist?"

### Analysis Queries (Tier 1/2, SQL_ANALYSIS)
- "analyze sales trends"
- "calculate correlation between X and Y"
- "show me statistics for revenue"
- "find patterns in customer behavior"

### Visualization Queries (Tier 1/2, SQL_VIZ)
- "plot sales over time"
- "create a bar chart of top products"
- "visualize customer distribution"
- "show me a trend graph"

### Combined Queries (Tier 2, SQL_ANALYSIS_VIZ)
- "analyze revenue by region and plot it"
- "compare sales trends and visualize"
- "show correlation heatmap with statistics"

## Troubleshooting

### Issue: Query goes to wrong tier
**Solution**: Check query wording, use explicit keywords

### Issue: Unnecessary agents called
**Solution**: Verify plan_type classification, check routing logic

### Issue: DataFrame ambiguity error
**Solution**: Fixed in new system - communication agent handles safely

### Issue: Slow response
**Solution**: Check metrics, verify Tier 1/2 being used for simple queries

### Issue: Wrong visualization type
**Solution**: Be explicit: "create a LINE chart" vs "create a BAR chart"

## Testing

Run the test script:
```bash
python examples/test_hybrid_routing.py
```

Test specific queries:
```python
from examples.test_hybrid_routing import test_classifier
test_classifier()
```

## Migration Checklist

- [ ] Update agent initialization to use Config
- [ ] Change `user_query` to `query` (or use alias)
- [ ] Use `final_response` instead of `final_answer`
- [ ] Check `agent_chain` for execution path
- [ ] Use `plan_type` for classification result
- [ ] Handle `query_results` as Any, not DataFrame
- [ ] Test with simple metadata query
- [ ] Verify metrics tracking works
- [ ] Check console logs for routing tier
- [ ] Ensure no DataFrame ambiguity errors
