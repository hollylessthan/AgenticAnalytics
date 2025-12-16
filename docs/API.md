# API Documentation

## Overview

The Agentic Analytics system provides a programmatic API for building multi-agent data analysis applications.

## Core Components

### Orchestrator

The main entry point for the system.

```python
from agentic_analytics.orchestrator import AgenticOrchestrator
from agentic_analytics.utils.database import get_schema_info

# Initialize
db_path = "path/to/database.db"
schema = get_schema_info(db_path)
orchestrator = AgenticOrchestrator(db_path, schema)

# Run a query
result = orchestrator.run("What are the total sales by product?")
```

**AgenticOrchestrator Methods:**

- `__init__(database_path: str, schema: str)`: Initialize the orchestrator
- `run(question: str) -> Dict[str, Any]`: Process a natural language question

**Return Value Structure:**
```python
{
    "question": str,           # Original question
    "sql_query": str,         # Generated SQL query
    "data": pd.DataFrame,     # Retrieved data
    "analysis": str,          # Analysis text
    "figure": plotly.Figure,  # Visualization (if requested)
    "messages": List[str],    # Execution log
    "final_response": str     # Final answer
}
```

### Individual Agents

#### SQL Agent

Converts natural language to SQL queries.

```python
from agentic_analytics.agents.sql_agent import SQLAgent

sql_agent = SQLAgent()
result = sql_agent.execute(
    "What are the total sales?",
    {"schema": schema_info}
)
```

#### Data Agent

Executes SQL queries and retrieves data.

```python
from agentic_analytics.agents.data_agent import DataAgent

data_agent = DataAgent()
result = data_agent.execute(
    "SELECT * FROM products",
    {"database_path": "data.db"}
)
```

#### Analysis Agent

Performs statistical analysis on data.

```python
from agentic_analytics.agents.analysis_agent import AnalysisAgent

analysis_agent = AnalysisAgent()
result = analysis_agent.execute(
    "Analyze the sales trends",
    {"data": dataframe}
)
```

#### Visualization Agent

Creates visualizations from data.

```python
from agentic_analytics.agents.visualization_agent import VisualizationAgent

viz_agent = VisualizationAgent()
result = viz_agent.execute(
    "Create a bar chart",
    {"data": dataframe}
)
```

#### Planner Agent

Plans task execution.

```python
from agentic_analytics.agents.planner_agent import PlannerAgent

planner = PlannerAgent()
result = planner.execute(
    "Show sales by product and create a chart",
    {}
)
```

### Database Utilities

```python
from agentic_analytics.utils.database import (
    get_schema_info,
    create_sample_database
)

# Get database schema
schema = get_schema_info("database.db")

# Create sample database for testing
create_sample_database("sample.db")
```

### Vector Store

RAG-enabled vector store for schema retrieval.

```python
from agentic_analytics.rag.vector_store import VectorStore

# Initialize
vector_store = VectorStore(store_type="faiss")

# Add documents
vector_store.add_documents([
    {"text": "Table schema...", "metadata": {"type": "schema"}}
])

# Search
results = vector_store.search("find sales table", k=3)
```

### Configuration

```python
from agentic_analytics.config.settings import settings

# Access configuration
print(settings.llm_model)
print(settings.temperature)
print(settings.vector_store_type)

# Modify configuration
settings.llm_model = "gpt-4-turbo"
settings.temperature = 0.1
```

## Error Handling

All agents return results in this format:

```python
{
    "success": bool,
    "error": str,        # Only present if success is False
    "agent": str,        # Agent name
    # ... other result fields
}
```

Example error handling:

```python
result = orchestrator.run("What are the sales?")

if result.get("data") is not None:
    print("Success!")
    print(result["data"])
else:
    print(f"Error: {result.get('error', 'Unknown error')}")
```

## Examples

### Example 1: Simple Query

```python
orchestrator = AgenticOrchestrator(db_path, schema)
result = orchestrator.run("What products do we have?")
print(result["data"])
```

### Example 2: Analysis

```python
result = orchestrator.run("Analyze sales by category")
print(result["analysis"])
print(result["data"])
```

### Example 3: Visualization

```python
result = orchestrator.run("Create a bar chart of sales by product")
result["figure"].show()  # Display the chart
```

### Example 4: Complex Query

```python
result = orchestrator.run(
    "Show me the top 3 products by revenue and create a chart"
)
print(result["sql_query"])
print(result["data"])
result["figure"].show()
```

## Advanced Usage

### Custom Agents

Create custom agents by extending `BaseAgent`:

```python
from agentic_analytics.agents.base import BaseAgent
from typing import Any, Dict

class CustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Custom Agent",
            description="Does custom analysis"
        )
    
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        # Your implementation here
        return {
            "success": True,
            "result": "..."
        }
```

### Custom Workflows

Modify the orchestrator workflow:

```python
from langgraph.graph import StateGraph

# Access the workflow
workflow = orchestrator.workflow

# You can rebuild with custom logic
# See orchestrator.py for implementation details
```

## Configuration Options

Environment variables (set in `.env`):

- `OPENAI_API_KEY`: OpenAI API key (required)
- `LLM_MODEL`: Model name (default: "gpt-4")
- `EMBEDDING_MODEL`: Embedding model (default: "text-embedding-3-small")
- `TEMPERATURE`: LLM temperature (default: 0.0)
- `VECTOR_STORE_TYPE`: "faiss" or "weaviate" (default: "faiss")
- `WEAVIATE_URL`: Weaviate URL (default: "http://localhost:8080")
- `DATABASE_PATH`: Database path (default: "data/examples/sample.db")
- `MAX_ITERATIONS`: Max agent iterations (default: 10)
- `VERBOSE`: Enable verbose logging (default: true)

## Testing

Run the test suite:

```bash
python test_basic.py
```

Run example scripts:

```bash
python examples/basic_usage.py
```

## Troubleshooting

### "Module not found" errors
Install all dependencies:
```bash
pip install -r requirements.txt
```

### OpenAI API errors
Ensure your API key is set:
```bash
export OPENAI_API_KEY=your_key_here
```

### Database errors
The system will auto-create a sample database if needed. To use your own:
```python
settings.database_path = "path/to/your/database.db"
```
