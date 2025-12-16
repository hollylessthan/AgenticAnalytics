# AgenticAnalytics 🤖

A powerful multi-agent data analyst chatbot that answers natural language questions through intelligent agent orchestration.

## Features

- 🧠 **Multi-Agent System**: Specialized agents for different tasks
  - **Planner Agent**: Coordinates task execution
  - **SQL Agent**: Converts natural language to SQL queries
  - **Data Agent**: Executes queries and retrieves data
  - **Analysis Agent**: Performs statistical analysis
  - **Visualization Agent**: Creates charts and visualizations

- 🔍 **RAG Integration**: Uses FAISS or Weaviate for intelligent schema retrieval
- 🎯 **LangGraph Orchestration**: Sophisticated workflow management
- 💬 **Streamlit Frontend**: Beautiful, interactive chat interface
- 📊 **Rich Visualizations**: Powered by Plotly

## Architecture

```
User Question
     ↓
Planner Agent (Plans execution steps)
     ↓
SQL Agent (Generates SQL query)
     ↓
Data Agent (Executes query)
     ↓
   ┌─────────────┬──────────────┐
   ↓             ↓              ↓
Analysis Agent  Visualization  End
                Agent
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hollylessthan/AgenticAnalytics.git
cd AgenticAnalytics
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

## Usage

### Running the Streamlit App

```bash
streamlit run app.py
```

Then open your browser to `http://localhost:8501`

### Using the System

1. Enter your OpenAI API key in the sidebar
2. Click "Initialize System" to set up the database and agents
3. Ask questions in natural language:
   - "What are the total sales by product?"
   - "Show me the top 3 selling products"
   - "Create a bar chart of sales by product"
   - "Analyze the distribution of product prices"

### Programmatic Usage

```python
from agentic_analytics.orchestrator import AgenticOrchestrator
from agentic_analytics.utils.database import get_schema_info

# Initialize
db_path = "data/examples/sample.db"
schema = get_schema_info(db_path)
orchestrator = AgenticOrchestrator(db_path, schema)

# Ask a question
result = orchestrator.run("What are the total sales by product?")

print(result["analysis"])
print(result["data"])
```

## Project Structure

```
AgenticAnalytics/
├── agentic_analytics/          # Main package
│   ├── agents/                 # Agent implementations
│   │   ├── base.py            # Base agent class
│   │   ├── planner_agent.py   # Planning/coordination
│   │   ├── sql_agent.py       # SQL generation
│   │   ├── data_agent.py      # Data retrieval
│   │   ├── analysis_agent.py  # Data analysis
│   │   └── visualization_agent.py  # Visualizations
│   ├── rag/                   # RAG system
│   │   └── vector_store.py    # Vector store management
│   ├── config/                # Configuration
│   │   └── settings.py        # Settings management
│   ├── utils/                 # Utilities
│   │   └── database.py        # Database utilities
│   └── orchestrator.py        # Main orchestrator
├── data/                      # Data directory
│   └── examples/              # Example databases
├── app.py                     # Streamlit application
├── requirements.txt           # Dependencies
├── .env.example              # Example environment file
└── README.md                 # This file
```

## Configuration

Edit `.env` file to configure:

- `OPENAI_API_KEY`: Your OpenAI API key
- `LLM_MODEL`: Model to use (default: gpt-4)
- `VECTOR_STORE_TYPE`: Vector store type (faiss or weaviate)
- `DATABASE_PATH`: Path to SQLite database
- `TEMPERATURE`: LLM temperature (0.0 for deterministic)

## Technology Stack

- **LangChain**: Agent framework and LLM integration
- **LangGraph**: Agent orchestration and workflow management
- **Streamlit**: Web interface
- **FAISS**: Vector store for RAG
- **OpenAI**: GPT-4 for language understanding
- **Plotly**: Interactive visualizations
- **Pandas**: Data manipulation
- **SQLite**: Database

## Example Database

The system includes a sample database with:
- **Products**: Electronics and furniture items
- **Sales**: Transaction history
- **Customers**: Customer information

The sample database is automatically created on first run.

## Development

### Adding a New Agent

1. Create a new agent class in `agentic_analytics/agents/`
2. Inherit from `BaseAgent`
3. Implement the `execute` method
4. Add the agent to the orchestrator workflow

### Extending the Vector Store

Support for different vector stores can be added in `agentic_analytics/rag/vector_store.py`

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

See LICENSE file for details.

## Support

For issues and questions, please open an issue on GitHub.
