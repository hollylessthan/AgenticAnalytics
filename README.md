# 🤖 Agentic Analytics









































































































    main()if __name__ == "__main__":            print(result.query_results.head())            print(f"\n📊 Results Preview:")        if result.query_results is not None:                print(result.sql_query)        print(f"\n✅ Generated SQL:")                result = orchestrator.run(query)        # Run with orchestrator                    print(f"\n{i}. {doc.page_content[:200]}...")        for i, doc in enumerate(context_docs, 1):        print("\nRetrieved Context:")        context_docs = rag_system.retrieve_context(query, k=2)        # Get relevant context                print('=' * 60)        print(f"Query: {query}")        print(f"\n{'=' * 60}")    for query in test_queries:    print("\n3. Testing RAG-enhanced queries...")        ]        "Average order value per country"        "Who are the top spending customers?",        "Show me sales by month",    test_queries = [    # Test queries        print("Examples indexed successfully!")    rag_system.save_index()    rag_system.index_query_examples(examples)        ]        }            """            ORDER BY avg_order_value DESC            GROUP BY c.country            WHERE o.status = 'completed'            JOIN orders o ON c.customer_id = o.customer_id            FROM customers c                COUNT(o.order_id) as num_orders                AVG(o.total_amount) as avg_order_value,                c.country,            SELECT             "sql": """            "question": "What's the average order value by country?",        {        },            """            LIMIT 10            ORDER BY total_spent DESC            GROUP BY c.customer_id, c.name            WHERE o.status = 'completed'            JOIN orders o ON c.customer_id = o.customer_id            FROM customers c                SUM(o.total_amount) as total_spent                c.name,                c.customer_id,            SELECT             "sql": """            "question": "Which customers have spent the most?",        {        },            """            ORDER BY month            GROUP BY month            WHERE status = 'completed'            FROM orders                SUM(total_amount) as total_sales                strftime('%Y-%m', order_date) as month,            SELECT             "sql": """            "question": "What are the total sales by month?",        {    examples = [    print("\n2. Adding example queries...")    # Add example queries for few-shot learning        rag_system.index_database_schema(schema)    schema = db.get_schema_info()    print("\n1. Indexing database schema...")    # Index database schema        db = DatabaseManager()    rag_system = RAGSystem()    orchestrator = AgentOrchestrator()    # Initialize        print("=" * 60)    print("RAG-Enhanced SQL Generation Example")        """Demonstrate RAG-enhanced SQL generation."""def main():from utils.database import DatabaseManagerfrom rag.rag_system import RAGSystemfrom agents.orchestrator import AgentOrchestratorA powerful multi-agent data analyst chatbot that can answer natural language questions through SQL query generation, data retrieval, Python analysis, and visualization creation. Built with LangGraph, LangChain, and Streamlit.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![LangChain](https://img.shields.io/badge/LangChain-latest-orange.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-latest-red.svg)

## ✨ Features

- **Multi-Agent Architecture**: Orchestrated agents using LangGraph for SQL, analysis, and visualization
- **Natural Language to SQL**: Converts plain English questions into SQL queries
- **Automated Data Analysis**: Performs statistical analysis using Python/pandas
- **Smart Visualizations**: Generates charts and graphs automatically
- **RAG Integration**: Uses FAISS or Weaviate for context-aware responses
- **Interactive UI**: Beautiful Streamlit interface for chat and results
- **Multi-LLM Support**: OpenAI, Anthropic (Claude), Google (Gemini), AWS Bedrock, Azure OpenAI
- **Database Agnostic**: SQLite, PostgreSQL, MySQL, DuckDB, Snowflake, Redshift, BigQuery

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Query                            │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              Agent Orchestrator (LangGraph)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│  │ Planner  │→ │  Router  │→ │ Agent Selection   │     │
│  └──────────┘  └──────────┘  └──────────────────┘     │
└───────────────────┬─────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
        ▼           ▼           ▼
┌──────────┐ ┌─────────────┐ ┌─────────────────┐
│   SQL    │ │  Analysis   │ │ Visualization   │
│  Agent   │ │   Agent     │ │     Agent       │
└──────────┘ └─────────────┘ └─────────────────┘
     │            │                  │
     └────────────┴──────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  RAG System    │
         │  (FAISS/       │
         │   Weaviate)    │
         └────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │   Database     │
         │  (PostgreSQL,  │
         │   MySQL, etc)  │
         └────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher (Python 3.12 recommended)
- LLM API key (OpenAI, Anthropic, Google, or AWS Bedrock)
- Database (SQLite, PostgreSQL, MySQL, DuckDB, Snowflake, Redshift, or BigQuery)

> **📘 Need help with setup?** See [SETUP.md](SETUP.md) for comprehensive environment setup guide including Python installation, virtual environments, and troubleshooting.

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/hollylessthan/AgenticAnalytics.git
cd AgenticAnalytics
```

2. **Create virtual environment**
```bash
# Using Python 3.12 (recommended)
python3.12 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Or use default Python (3.9+)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
# Upgrade pip first
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:
- `LLM_PROVIDER`: Choose your LLM provider (openai, anthropic, google, bedrock, azure)
- `[PROVIDER]_API_KEY`: API key for your chosen provider
- `DATABASE_TYPE`: Database type (sqlite, postgresql, mysql, duckdb, etc.)
- `DATABASE_URL`: Database connection string
- `VECTOR_STORE_TYPE`: Choose `faiss` or `weaviate`

See [PROVIDERS.md](PROVIDERS.md) for detailed configuration instructions.

5. **Setup test database with TPC-DS data**
```bash
# Generate 1GB TPC-DS benchmark data (or use 100 for 100GB)
cd testing
./generate_tpcds_data.sh 1

# Load into DuckDB
python setup_tpcds_duckdb.py --scale 1

# Generate RAG documents
python generate_rag_documents.py
cd ..
```

### Running the Application

**Streamlit UI:**
```bash
streamlit run src/app.py
```

**Command Line:**
```bash
python examples/basic_usage.py
```

## 📖 Usage

### Basic Example

```python
from agents.orchestrator import AgentOrchestrator
from rag.rag_system import RAGSystem
from utils.memory import MemoryManager

# Initialize systems
orchestrator = AgentOrchestrator()
rag_system = RAGSystem()
memory = MemoryManager(session_id="demo_session")

# Index your database schema
from utils.database import DatabaseManager
db = DatabaseManager()
schema = db.get_schema_info()
rag_system.index_database_schema(schema)

# Run a query with memory
query = "What are the top 10 customers by revenue?"
result = orchestrator.run(query)

# Save to memory
memory.add_exchange(
    user_message=query,
    assistant_message=result.final_answer,
    result_summary="Retrieved top customers",
    success=True
)

print(result.final_answer)
print(result.sql_query)
print(result.query_results)
```

### Memory Example

```python
from utils.memory import MemoryManager

# Create memory manager
memory = MemoryManager(session_id="user_123", max_conversation_messages=10)

# Add conversation
memory.add_exchange(
    user_message="Show me sales by month",
    assistant_message="Here are monthly sales: Jan: $100K, Feb: $120K...",
    result_summary="Generated monthly sales report",
    success=True
)

# Set preferences
memory.session_memory.set_preference("default_chart", "bar")

# Get context for LLM
context = memory.get_context_for_llm()

# Save session
memory.save_session()

# Later, load the same session
memory2 = MemoryManager(session_id="user_123")
# All history and preferences are restored!
```

### Streamlit Interface

1. Start the app: `streamlit run src/app.py`
2. Click "Initialize Systems" in the sidebar
3. Index your database schema
4. Start asking questions in natural language!

Example queries:
- "Show me total sales by month"
- "Which products have the highest profit margin?"
- "Create a bar chart of revenue by category"
- "Analyze the correlation between price and quantity sold"

## 🧩 Components

### Agents

- **SQL Agent**: Converts natural language to SQL queries
- **Analysis Agent**: Performs data analysis with Python/pandas
- **Visualization Agent**: Creates charts using matplotlib/seaborn
- **Orchestrator**: Coordinates agents using LangGraph

### RAG System

- **Vector Store**: FAISS (in-memory) or Weaviate (persistent)
- **Embeddings**: OpenAI embeddings for semantic search
- **Context Retrieval**: Schema info and example queries

### Database Support

- PostgreSQL
- MySQL
- SQLite
- DuckDB
- Snowflake
- Redshift
- BigQuery

### Memory Management

- **Short-term Memory**: Conversation context with sliding window
- **Long-term Memory**: Persistent session storage across restarts
- **User Preferences**: Remember user settings and preferences
- **Query History**: Track all queries with success/failure status
- **Insights**: Automatically collect behavioral insights
- **Context Generation**: Smart context summarization for LLMs

## 📁 Project Structure

```
AgenticAnalytics/
├── src/
│   ├── agents/
│   │   ├── base.py              # Base agent classes
│   │   ├── orchestrator.py      # LangGraph orchestrator
│   │   ├── sql_agent.py         # SQL generation agent
│   │   ├── analysis_agent.py    # Data analysis agent
│   │   └── visualization_agent.py # Visualization agent
│   ├── rag/
│   │   ├── vector_store.py      # Vector store implementations
│   │   └── rag_system.py        # RAG system
│   ├── utils/
│   │   ├── database.py          # Database utilities
│   │   ├── memory.py            # Memory management system
│   │   ├── helpers.py           # Helper functions
│   │   ├── llm_factory.py       # LLM provider factory
│   │   ├── database_factory.py  # Database factory
│   │   └── embedding_factory.py # Embeddings factory
│   ├── config.py                # Configuration management
│   └── app.py                   # Streamlit application
├── tests/
│   ├── test_agents.py
│   ├── test_database.py
│   └── test_rag.py
├── examples/
│   ├── basic_usage.py           # Basic usage example
│   ├── create_sample_db.py      # Sample database creator
│   ├── memory_example.py        # Memory system demo
│   ├── multi_provider_example.py # Multi-provider demo
│   └── vector_store_example.py  # Vector store examples
├── requirements.txt
├── setup.py
├── .env.example
└── README.md
```

## 🔧 Configuration

Edit `.env` file:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
# or sqlite:///./data/analytics.db

# Vector Store
VECTOR_STORE_TYPE=faiss  # or weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=

# Agent Settings
AGENT_MODEL=gpt-4-turbo-preview
AGENT_TEMPERATURE=0.0
MAX_ITERATIONS=10
```

## 🧪 Testing

Run tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## 🛠️ Development

### Adding New Agents

1. Create agent class inheriting from `BaseAgent`
2. Implement `execute()` method
3. Add to orchestrator workflow
4. Update routing logic

Example:
```python
from agents.base import BaseAgent, AgentState

class CustomAgent(BaseAgent):
    def __init__(self, llm):
        super().__init__("custom_agent", "Description")
        self.llm = llm
    
    def execute(self, state: AgentState) -> AgentState:
        # Your logic here
        return state
```

### Adding New Vector Stores

1. Implement `VectorStoreBase` interface
2. Add to `get_vector_store()` factory
3. Update configuration options

## 📊 Example Use Cases

1. **Sales Analysis**: "Show me monthly revenue trends with a line chart"
2. **Customer Insights**: "Which customers have the highest lifetime value?"
3. **Product Performance**: "Create a bar chart of top 10 products by sales"
4. **Trend Analysis**: "What's the correlation between marketing spend and revenue?"
5. **Data Exploration**: "Summarize the order data with statistics"

## 🧪 Large-Scale Testing

Test the system with **TPC-DS benchmark data (up to 100GB)** using DuckDB locally:

```bash
cd testing

# Generate 100GB test data (or start with 1GB for quick tests)
./generate_tpcds_data.sh 100

# Load into DuckDB
python setup_tpcds_duckdb.py --scale 100

# Generate RAG documents
python generate_rag_documents.py

# Run performance tests
python run_performance_tests.py --test all
```

**Features:**
- ✅ Industry-standard TPC-DS retail schema (24 tables, ~2B rows at 100GB)
- ✅ DuckDB for efficient local analytics (handles 100GB on 16GB RAM)
- ✅ Automated RAG document generation from schema
- ✅ Comprehensive test suite (basic → advanced queries)
- ✅ Performance benchmarking and metrics
- ✅ Multi-channel analysis (store, catalog, web sales)

See [testing/README.md](testing/README.md) for complete guide.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - LLM framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Agent orchestration
- [Streamlit](https://streamlit.io/) - UI framework
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [Weaviate](https://weaviate.io/) - Vector database

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Built with ❤️ using LangGraph, LangChain, and Streamlit**
