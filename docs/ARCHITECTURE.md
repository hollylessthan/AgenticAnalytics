# Architecture Documentation

## System Overview

Agentic Analytics is a multi-agent system that uses specialized AI agents coordinated through LangGraph to answer natural language questions about data.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (Streamlit)                │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Chat Input  │  │ Visualization│  │  SQL Display │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Orchestrator (LangGraph)                     │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │                  State Manager                     │      │
│  │  - Question                                        │      │
│  │  - Plan                                            │      │
│  │  - SQL Query                                       │      │
│  │  - Data                                            │      │
│  │  - Analysis                                        │      │
│  │  - Visualization                                   │      │
│  └───────────────────────────────────────────────────┘      │
│                         │                                     │
│         ┌───────────────┼───────────────┐                   │
│         ▼               ▼               ▼                   │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐               │
│   │ Planner │    │   SQL   │    │  Data   │               │
│   │  Agent  │───▶│  Agent  │───▶│  Agent  │               │
│   └─────────┘    └─────────┘    └─────────┘               │
│                                       │                      │
│                    ┌──────────────────┴────────┐           │
│                    ▼                           ▼           │
│              ┌──────────┐              ┌────────────┐      │
│              │ Analysis │              │Visualization│     │
│              │  Agent   │              │   Agent    │      │
│              └──────────┘              └────────────┘      │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   RAG System (Vector Store)                  │
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │    FAISS     │   OR    │   Weaviate   │                  │
│  │    Index     │         │    Client    │                  │
│  └──────────────┘         └──────────────┘                  │
│         │                         │                          │
│         └─────────┬───────────────┘                         │
│                   ▼                                          │
│         Schema Embeddings                                    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               External Services                              │
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │  OpenAI API  │         │   SQLite DB  │                  │
│  │  (GPT-4)     │         │              │                  │
│  └──────────────┘         └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. User Interface (Streamlit)

**File:** `app.py`

- Interactive chat interface
- Visualization rendering with Plotly
- Configuration management
- Real-time feedback and error handling

**Key Features:**
- Chat history
- Collapsible sections for SQL, data, and execution steps
- API key management
- System initialization

### 2. Orchestrator

**File:** `agentic_analytics/orchestrator.py`

The orchestrator coordinates all agents using LangGraph's state machine.

**Workflow:**
1. **Planning Phase**: Planner agent analyzes the question
2. **SQL Generation**: SQL agent converts to query
3. **Data Retrieval**: Data agent executes query
4. **Analysis/Visualization**: Based on plan, runs appropriate agents

**State Management:**
```python
class AgentState:
    question: str
    plan: List[Dict]
    sql_query: str
    data: DataFrame
    analysis: str
    figure: Figure
    messages: List[str]
    final_response: str
```

### 3. Agents

All agents inherit from `BaseAgent` and follow a consistent interface.

#### Planner Agent
**File:** `agentic_analytics/agents/planner_agent.py`

- Analyzes user questions
- Creates execution plans
- Determines which agents to use
- Sequences operations

#### SQL Agent
**File:** `agentic_analytics/agents/sql_agent.py`

- Converts natural language to SQL
- Uses schema information via RAG
- Handles complex queries with JOINs
- Validates SQL syntax

#### Data Agent
**File:** `agentic_analytics/agents/data_agent.py`

- Executes SQL queries
- Retrieves data from SQLite
- Returns pandas DataFrames
- Handles database errors

#### Analysis Agent
**File:** `agentic_analytics/agents/analysis_agent.py`

- Performs statistical analysis
- Generates insights
- Computes summary statistics
- Provides natural language explanations

#### Visualization Agent
**File:** `agentic_analytics/agents/visualization_agent.py`

- Creates Plotly visualizations
- Supports multiple chart types:
  - Bar charts
  - Line charts
  - Scatter plots
  - Histograms
  - Pie charts
- Intelligent chart selection based on data

### 4. RAG System

**File:** `agentic_analytics/rag/vector_store.py`

**Purpose:** Enhance SQL generation with relevant schema information

**Components:**
- **FAISS Index**: In-memory vector store
- **Weaviate Support**: Optional cloud vector store
- **OpenAI Embeddings**: text-embedding-3-small

**Workflow:**
1. Database schema is chunked by table
2. Each chunk is embedded
3. User questions are embedded
4. Similar schema chunks are retrieved
5. Relevant schema is passed to SQL agent

### 5. Configuration System

**File:** `agentic_analytics/config/settings.py`

- Environment variable management
- Pydantic-based validation
- Default values
- Runtime configuration updates

**Configuration Sources:**
1. Environment variables
2. `.env` file
3. Default values

### 6. Database Utilities

**File:** `agentic_analytics/utils/database.py`

**Functions:**
- `get_schema_info()`: Extract schema from SQLite
- `create_sample_database()`: Generate test data

## Data Flow

### Example: "What are the total sales by product?"

1. **User Input** → Streamlit UI
2. **Orchestrator** receives question
3. **Planner Agent** creates plan:
   - Use SQL Agent
   - Use Data Agent
   - Use Analysis Agent
4. **SQL Agent** queries RAG for relevant schema
5. **SQL Agent** generates:
   ```sql
   SELECT p.name, SUM(s.revenue) as total_sales
   FROM products p
   JOIN sales s ON p.id = s.product_id
   GROUP BY p.name
   ORDER BY total_sales DESC
   ```
6. **Data Agent** executes query → DataFrame
7. **Analysis Agent** analyzes results → Insights
8. **Response** returned to UI with:
   - SQL query
   - Data table
   - Analysis text

## Technology Stack

### Core Framework
- **LangChain**: Agent framework, LLM integration
- **LangGraph**: Workflow orchestration, state management
- **OpenAI**: GPT-4 for language understanding

### Frontend
- **Streamlit**: Web interface
- **Plotly**: Interactive visualizations

### Data & Storage
- **SQLite**: Database
- **Pandas**: Data manipulation
- **FAISS**: Vector store
- **Weaviate**: (Optional) Cloud vector store

### Utilities
- **Pydantic**: Configuration validation
- **python-dotenv**: Environment management

## Design Patterns

### 1. Agent Pattern
Each agent is a specialized component with a single responsibility.

### 2. State Machine Pattern
LangGraph manages state transitions between agents.

### 3. Strategy Pattern
Different visualization strategies based on data type.

### 4. RAG Pattern
Retrieval Augmented Generation for schema information.

## Scalability Considerations

### Current Implementation
- Single database support (SQLite)
- Synchronous execution
- In-memory vector store

### Future Enhancements
- Multiple database support (PostgreSQL, MySQL)
- Async execution for parallel agent calls
- Distributed vector store
- Caching layer for common queries
- Multi-user support

## Security

### Current Measures
- API key in environment variables
- SQL injection prevention via parameterized queries
- No direct code execution

### Recommendations
- Use secure key management (e.g., AWS Secrets Manager)
- Implement rate limiting
- Add authentication for multi-user deployments
- Audit logging for queries

## Performance

### Optimization Strategies
1. **Caching**: Cache common schema retrievals
2. **Batch Processing**: Group similar queries
3. **Lazy Loading**: Load agents on demand
4. **Connection Pooling**: Reuse database connections

### Benchmarks
- SQL Generation: ~2-3 seconds
- Data Retrieval: <1 second
- Analysis: ~2-4 seconds
- Visualization: <1 second
- **Total**: ~5-10 seconds per question

## Error Handling

### Error Types
1. **API Errors**: OpenAI rate limits, invalid keys
2. **Database Errors**: Invalid SQL, connection issues
3. **Data Errors**: Empty results, type mismatches
4. **Agent Errors**: Parsing failures, timeouts

### Recovery Strategies
- Fallback plans when agents fail
- Graceful degradation (skip visualization if analysis fails)
- User-friendly error messages
- Retry logic for transient failures

## Testing Strategy

### Unit Tests
- Individual agent functionality
- Database utilities
- Configuration management

### Integration Tests
- End-to-end workflows
- Agent coordination
- Error handling

### Manual Testing
- UI interaction
- Edge cases
- Performance testing

## Deployment

### Local Development
```bash
pip install -r requirements.txt
streamlit run app.py
```

### Docker (Future)
```dockerfile
FROM python:3.11
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "app.py"]
```

### Cloud Deployment
- AWS: Elastic Beanstalk, ECS
- GCP: App Engine, Cloud Run
- Azure: App Service

## Monitoring

### Metrics to Track
- Query success rate
- Average response time
- Agent execution times
- Error rates
- User satisfaction

### Logging
- Structured logging with context
- Agent execution traces
- Performance metrics
- Error stack traces

## Future Enhancements

1. **Multi-Database Support**: PostgreSQL, MySQL, MongoDB
2. **Advanced Analytics**: ML models, predictive analytics
3. **Custom Agents**: User-defined agents
4. **Collaboration**: Multi-user, shared queries
5. **Query History**: Save and replay queries
6. **Export**: PDF reports, Excel exports
7. **Streaming**: Real-time data updates
8. **Voice Input**: Speech-to-text integration
