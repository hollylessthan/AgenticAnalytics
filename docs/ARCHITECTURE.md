# Agentic Analytics Architecture

## Overview

**Agentic Analytics** is a multi-agent orchestration framework built with LangGraph and LangChain. The core framework decomposes complex data analysis tasks into specialized agent workflows that collaborate to provide comprehensive insights.

**Data Copilot** is a reference implementation that provides a Streamlit UI on top of Agentic Analytics, demonstrating how the framework can be deployed as an interactive chat interface.

This document describes the **Agentic Analytics core architecture**. The UI layer (Data Copilot) is thin and primarily handles user interaction while delegating all analytical work to the core framework.

## System Design

### Architectural Layers

```
┌─────────────────────────────────────────────────────┐
│           Data Copilot (UI Layer)                   │
│       Streamlit Chat Interface                      │
│   (User input, visualization display, chat hist)   │
└──────────────────┬──────────────────────────────────┘
                   │ (Delegates analytical work)
                   ▼
┌─────────────────────────────────────────────────────┐
│    Agentic Analytics (Core Framework)               │
│        Agent Orchestrator (LangGraph)               │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  1. Query Classification (Hybrid Router)    │   │
│  │     ├─ Regex Rules (Fast)                  │   │
│  │     ├─ Keyword Matching (Medium)           │   │
│  │     └─ LLM Classification (Accurate)       │   │
│  └─────────────────────────────────────────────┘   │
│                   │                                 │
│                   ▼                                 │
│  ┌─────────────────────────────────────────────┐   │
│  │  2. Agent Selection & Routing               │   │
│  │     ├─ SQL Agent                           │   │
│  │     ├─ Analysis Agent                      │   │
│  │     ├─ Visualization Agent                 │   │
│  │     └─ Communication Agent                 │   │
│  └─────────────────────────────────────────────┘   │
│                   │                                 │
│                   ▼                                 │
│  ┌─────────────────────────────────────────────┐   │
│  │  3. Agent Execution & Result Aggregation   │   │
│  │     ├─ Context passing                     │   │
│  │     ├─ Streaming callbacks                 │   │
│  │     └─ Error handling                      │   │
│  └─────────────────────────────────────────────┘   │
└──────────────┬───────────────────────────────────────┘
               │
   ┌───────────┼───────────┬────────────────┐
   │           │           │                │
   ▼           ▼           ▼                ▼
┌──────────┐ ┌──────────┐ ┌─────────┐ ┌─────────────┐
│  RAG     │ │Database  │ │LLM      │ │Cache        │
│System    │ │Manager   │ │Factory  │ │Manager      │
├──────────┤ ├──────────┤ ├─────────┤ ├─────────────┤
│-Vector   │ │-Schema   │ │-OpenAI  │ │-Query       │
│ Store    │ │-Queries  │ │-Claude  │ │ Results     │
│-Indexing │ │-Metadata │ │-Google  │ │-Policies    │
│-Retrieval│ │-Pooling  │ │-Bedrock │ │-Concurrency │
└──────────┘ └──────────┘ └─────────┘ └─────────────┘
   │           │
   │           ▼
   │       ┌──────────────────────────────┐
   │       │    Target Databases          │
   │       │ ├─ PostgreSQL                │
   │       │ ├─ MySQL                     │
   │       │ ├─ DuckDB                    │
   │       │ ├─ Snowflake                 │
   │       │ └─ BigQuery                  │
   │       └──────────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────┐
│          Vector Stores (FAISS / Weaviate)            │
│  - Database schema embeddings                        │
│  - Query example embeddings                          │
│  - Best practice documentation                       │
└──────────────────────────────────────────────────────┘
```

## Agent Orchestrator

The **Agent Orchestrator** (`src/agents/orchestrator.py`) is the core of Agentic Analytics. It coordinates specialized agents using a state machine pattern with LangGraph.

### Orchestrator Flow

```
Input Query
    ↓
┌─────────────────────────────────┐
│ STATE: Initialize               │
│ - Store query                   │
│ - Fetch conversation context    │
│ - Load RAG schema info          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ STATE: Classify Query           │
│ - Run hybrid router             │
│ - Determine query type          │
│ - Select appropriate agent(s)   │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ STATE: Execute Agents           │
│ ├─ SQL Agent (if needed)        │
│ │  ├─ Retrieve schema context   │
│ │  ├─ Generate SQL              │
│ │  └─ Execute & limit results   │
│ │                               │
│ ├─ Analysis Agent (if needed)   │
│ │  ├─ Compute statistics        │
│ │  ├─ Detect trends             │
│ │  └─ Generate insights         │
│ │                               │
│ ├─ Visualization Agent (opt)    │
│ │  ├─ Select chart type         │
│ │  ├─ Create visualization      │
│ │  └─ Format for display        │
│ │                               │
│ └─ Communication Agent          │
│    ├─ Format response           │
│    ├─ Add context               │
│    └─ Prepare for streaming     │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ STATE: Cache Results            │
│ - Evaluate caching eligibility  │
│ - Store if eligible             │
│ - Return to user                │
└─────────────────────────────────┘
    ↓
Output with inline visualizations
```

### State Management

The orchestrator maintains state throughout execution:

```python
class OrchestrationState(TypedDict):
    """State passed between agents."""
    query: str                          # Original user query
    query_type: str                     # Classified type (sql, analysis, etc)
    schema_context: str                 # Relevant schema info
    sql_query: Optional[str]            # Generated SQL
    query_results: Optional[pd.DataFrame]  # Query execution results
    analysis: Optional[str]             # Statistical analysis
    visualization: Optional[str]        # Chart/visualization data
    intermediate_steps: List[str]       # Execution log
    error: Optional[str]                # Error message if any
    final_answer: str                   # Formatted response
    metadata: Dict                      # Additional context
```

## Query Classifier (Hybrid Router)

The **Query Classifier** (`src/agents/query_classifier.py`) uses a 3-tier approach to determine optimal query handling:

### Tier 1: Regex Rules (Fast)

Fast pattern matching for common simple queries:

```
Pattern Examples:
- COUNT(*), SUM(...), AVG(...) → Aggregation
- SELECT * FROM ... → Simple select
- WHERE clause with simple conditions → Filter
```

**Performance**: ~2ms  
**Coverage**: ~40% of typical queries

### Tier 2: Keyword Matching (Medium)

Keyword-based classification for known query patterns:

```
Keywords:
- "top", "highest", "best" → Ranking/TopN
- "trend", "over time", "monthly" → Time series
- "compare", "vs", "versus" → Comparison
- "group by", "breakdown" → Grouping
```

**Performance**: ~5ms  
**Coverage**: ~50% of queries

### Tier 3: LLM Classification (Accurate)

For complex queries needing semantic understanding:

```
Uses LLM to understand:
- Business logic and context
- Complex joins needed
- Advanced analysis required
- Custom aggregations
```

**Performance**: ~80ms  
**Coverage**: ~10% of queries (but most critical)

### Router Decision Logic

```python
def classify_query(query: str) -> QueryType:
    # Try fast regex patterns first
    if matches_simple_pattern(query):
        return QueryType.SIMPLE_SELECT  # 2ms
    
    # Try keyword matching
    if has_aggregation_keywords(query):
        return QueryType.AGGREGATION    # 5ms
    
    # Fall back to LLM
    return llm_classify(query)          # 80ms
```

## Specialized Agents

### SQL Agent

**Purpose**: Translate natural language to SQL queries with intelligence

**Workflow**:
1. Receive user query and schema context
2. Retrieve relevant schema via RAG
3. Identify tables and JOINs needed
4. Generate SQL with parameterized queries
5. Apply row limits and validate
6. Execute on database
7. Return results and execution metadata

**Key Features**:
- **Automatic JOIN Intelligence**: Uses RAG to discover relationships
- **Schema Validation**: Ensures columns/tables exist
- **Query Optimization**: Suggests better queries if needed
- **Row Limiting**: Enforces safety limits
- **Error Recovery**: Handles invalid queries gracefully

**Example**:
```
User: "Show me top 10 customers by revenue"
    ↓
SQL Agent:
  1. Schema retrieval: Found customers, orders tables
  2. JOIN detection: orders has customer_id foreign key
  3. SQL generation: SELECT c.id, c.name, SUM(o.amount) ...
  4. Execution: Query with LIMIT 10 applied
  5. Results: DataFrame with results
```

### Analysis Agent

**Purpose**: Derive insights and statistics from data

**Capabilities**:
- **Descriptive Statistics**: Mean, median, std dev, quantiles
- **Trend Analysis**: Growth rates, momentum
- **Anomaly Detection**: Outlier identification
- **Correlation Analysis**: Relationships between variables
- **Business Insights**: Context-aware interpretation

**Example**:
```
Input: Sales data for 12 months
    ↓
Analysis:
  - Mean monthly sales: $150K
  - Trend: +5% month-over-month
  - Anomaly: October spike (+25%)
  - Insight: Seasonal pattern detected
```

### Visualization Agent

**Purpose**: Create appropriate visual representations

**Capabilities**:
- **Chart Type Selection**: Auto-selects best chart type
- **Interactive Plots**: Plotly-based interactive visualizations
- **Table Formatting**: Responsive, readable tables
- **Color Schemes**: Theme-aware color palettes
- **Mobile Responsive**: Displays well on all devices

**Chart Selection Logic**:
```
1 numeric column     → Histogram/Distribution
2 numeric columns   → Scatter/Line chart
1 categorical, 1 numeric → Bar/Column chart
Time series data     → Line chart with trend
Multiple categories  → Grouped bar chart
Proportions         → Pie/Donut chart
```

### Communication Agent

**Purpose**: Format responses for user consumption

**Responsibilities**:
- Compose final response text
- Structure multiple result types
- Add context and explanations
- Prepare for streaming output
- Handle error messaging

## RAG System

The **RAG System** (`src/rag/rag_system.py`) provides schema context to agents.

### Components

**Vector Store** (`src/rag/vector_store.py`):
- Supports FAISS (in-memory) and Weaviate (persistent)
- Stores embeddings for:
  - Table schemas
  - Column descriptions
  - Example queries
  - Best practices

**Indexing Process**:
```
1. Extract schema metadata
   └─ Table names, columns, types, constraints
2. Create embeddings
   └─ Vector representation of schema
3. Store in vector database
   └─ FAISS or Weaviate
4. Make retrievable
   └─ Semantic search ready
```

**Retrieval Process**:
```
User Query: "Show top 10 customers"
    ↓
Embedding: Vector representation
    ↓
Semantic Search: Find relevant schema
    ↓
Retrieved Context:
  - Table: customers
  - Table: orders
  - Relationship: customers.id = orders.customer_id
  - Column relevance scores
    ↓
Passed to SQL Agent
```

## Security Architecture

### SQL Injection Prevention

- **Parameterized Queries**: All user input via parameters
- **Query Validation**: Schema validation before execution
- **Statement Parsing**: AST analysis of generated SQL
- **Keyword Filtering**: Dangerous operations blocked

### Row Limiting

- **Configurable Limits**: Default 1,000 rows
- **LIMIT Enforcement**: Added to all queries
- **Intelligent Caching**: Large results not cached
- **User Visibility**: Informs users of limits

### DataFrame Safety

- **Type Validation**: Ensures safe operations
- **Column Checking**: Validates column existence
- **Safe Operations**: Whitelist of allowed pandas operations
- **Error Handling**: Graceful degradation

### Concurrent Access Control

- **Connection Pooling**: Limits simultaneous connections
- **Queue Management**: Manages concurrent requests
- **Timeout Handling**: Prevents hanging queries
- **Resource Cleanup**: Proper cleanup on completion

## Memory & Session Management

### Conversation Memory

- **Short-term**: Last 10 turns in current session
- **Context Sliding Window**: Maintains relevant context
- **Snapshot History**: Save/restore conversation states
- **Rollback Capability**: Revert to previous snapshots

### Session Storage

```
Session Data:
├── Conversation history
├── User preferences
├── Query history with results
├── Cached analysis results
├── Schema snapshots
└── Performance metrics
```

## Caching Strategy

### Cache Eligibility

Results cached if:
- Query results < row limit
- Query is deterministic (no RANDOM, NOW, etc)
- Database hasn't changed (schema validation)
- Not already cached

Results NOT cached if:
- Results > row limit
- Contains volatile functions
- User explicitly disables
- Real-time data required

### Cache Operations

```
Query Execution:
1. Check cache key (normalized query)
2. If hit: Return cached result
3. If miss:
   a. Execute query
   b. Evaluate caching eligibility
   c. Store if eligible
   d. Return result
```

## Streaming Architecture

Real-time visibility into agent reasoning:

### Callback System

```python
class StreamingCallback:
    def on_agent_start(self, tool, input):
        """Called when agent starts"""
        
    def on_agent_end(self, output):
        """Called when agent completes"""
        
    def on_tool_start(self, tool_input):
        """Called when tool starts"""
        
    def on_tool_end(self, output):
        """Called when tool completes"""
```

### User Experience

```
User: "Show top 5 products"
    ↓
[Streaming] Classifying query... ✓ SQL Query
[Streaming] Retrieving schema context...
[Streaming] Generating SQL...
    Generated: SELECT product_id, SUM(quantity) ...
[Streaming] Executing query...
[Streaming] Creating visualization...
[Streaming] Formatting response...
    ↓
Final Result with inline chart
```

## Configuration & Extensibility

### Adding New Agents

1. **Inherit from BaseAgent**:
```python
from agents.base import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__("custom", "Description")
        self.llm = llm
    
    def execute(self, state: OrchestrationState) -> OrchestrationState:
        # Your logic here
        return state
```

2. **Register in Orchestrator**:
```python
self.agents = {
    "custom": CustomAgent(self.llm),
    # ... other agents
}
```

3. **Update Router Logic**:
```python
if query_type == "custom_type":
    return self.agents["custom"].execute(state)
```

### Adding New Vector Stores

Implement the `VectorStoreBase` interface and register in factory:

```python
class CustomVectorStore(VectorStoreBase):
    def index(self, documents):
        # Index documents
        
    def search(self, query, k=5):
        # Return top-k results
```

## Performance Optimization

### Query Caching

Results cached at multiple levels:
- LLM response caching (same SQL generated)
- Query result caching (identical queries)
- Embedding caching (schema embeddings)

### Lazy Loading

- Schema loaded on demand
- RAG index lazy initialized
- Database connections pooled
- LLM calls cached when possible

### Parallelization

- Multiple agents can run in parallel if independent
- Vector search parallelized across dimensions
- Visualization generation async

## Error Handling & Recovery

### Error Hierarchy

```
OrchestrationError (base)
├── QueryClassificationError
├── SQLGenerationError
├── QueryExecutionError
├── AnalysisError
├── VisualizationError
└── CommunicationError
```

### Recovery Strategies

```
SQL Error:
  1. Try simplified query
  2. Retrieve schema again
  3. Regenerate with constraints
  4. Return helpful error message

LLM Error:
  1. Retry with different prompt
  2. Fall back to simpler approach
  3. Return cached result if available
  4. Inform user of limitation

Database Error:
  1. Check connection
  2. Retry with backoff
  3. Fall back to cache
  4. Report to user
```

## Monitoring & Observability

### Metrics Collected

- Query classification type distribution
- Agent execution times
- Query performance (from database)
- Cache hit/miss rates
- Error rates and types
- User interaction patterns

### Logging

- Query execution logs
- Agent step logs
- Cache operations
- Error logs with full context
- Performance metrics

## Deployment Considerations

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install -r requirements.txt

# Expose Streamlit port
EXPOSE 8501

# Run app
CMD ["streamlit", "run", "src/app.py"]
```

### Scaling Strategies

- **Horizontal**: Multiple app instances behind load balancer
- **Vertical**: Larger machine for database/cache
- **Vector Store**: Managed Weaviate for large-scale
- **Database**: Connection pooling and read replicas

---

See [HYBRID_ROUTING_IMPLEMENTATION.md](HYBRID_ROUTING_IMPLEMENTATION.md) for query routing details and [SQL_SECURITY.md](SQL_SECURITY.md) for security implementation.
