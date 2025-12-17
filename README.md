# Agentic Analytics

> A core framework for agent-assisted analytical workflows, with a reference user interface called **Data Copilot**.

**Agentic Analytics** is a core analytics framework that orchestrates role-based agents to support multi-step analytical workflows, including SQL execution, result analysis, visualization, and human-readable summaries.

**Data Copilot** is the reference user interface built on top of Agentic Analytics. It provides an interactive experience for querying, validating, and exploring analytical data while the core framework handles planning, execution, and verification behind the scenes.

**In short:** Agentic Analytics is the engine, and Data Copilot is the interface.

## Overview

```
┌─────────────────────────────────────┐
│       Data Copilot (UI Layer)       │
│  Interactive chat & visualizations  │
└────────────────┬────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────┐
│    Agentic Analytics (Core Framework)        │
│  - Multi-agent orchestration                 │
│  - Query classification & routing            │
│  - SQL generation & execution                │
│  - Analysis & visualization agents           │
│  - RAG-powered schema context                │
│  - Result caching & security                 │
└──────────────────────────────────────────────┘
```

## 📊 Data Copilot Features

Data Copilot is the reference UI that showcases the capabilities of Agentic Analytics:

## ✨ Key Features

- **🤖 Multi-Agent Architecture**: Specialized agents for SQL generation, analysis, visualization, and communication
- **🧠 Hybrid Routing System**: 3-tier intelligent query classification (Regex → Keywords → LLM) for optimal performance
- **📚 RAG Integration**: Automatic schema indexing and semantic search for context-aware responses
- **🔒 Security First**: SQL injection prevention, safe DataFrame handling, query row limits
- **💾 Smart Caching**: Result caching with configurable limits and concurrent read access
- **📊 Real-time Visualization**: Inline charts and tables with automatic formatting
- **🔄 Stateful Conversations**: 10-turn conversation history with snapshot rollback capability
- **🌊 Streaming Transparency**: Real-time agent reasoning visibility with callback-based streaming
- **🎯 Flexible & Extensible**: Works with any database, LLM provider, and vector store — customize for your data

## 🎯 Flexible Framework for Any Database

Agentic Analytics is built to work with **your data**, regardless of database type, LLM provider, or scale. Whether you have a PostgreSQL data warehouse, DuckDB analytics database, or Snowflake cluster, Agentic Analytics adapts to your setup.

### Supported Databases

```
PostgreSQL          MySQL              SQLite
DuckDB             Snowflake          Redshift
BigQuery           Athena             MongoDB (JSON)
```

### Supported LLM Providers

```
OpenAI            Anthropic Claude    Google Gemini
AWS Bedrock       Azure OpenAI        Local Models (Ollama)
```

### Supported Vector Stores

```
FAISS (in-memory)  Weaviate (persistent)  Pinecone
Chroma             Milvus
```

### Quick Customization

Point Agentic Analytics to your database and choose your preferred LLM and vector store — no code changes needed:

```bash
# .env configuration
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@your-host:5432/your_db

LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key

VECTOR_STORE_TYPE=weaviate
WEAVIATE_URL=http://your-host:8080
```

Then launch Data Copilot with your data:

```bash
streamlit run src/app.py
```

That's it! Agentic Analytics automatically discovers your schema and indexes it for intelligent query generation.

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/hollylessthan/AgenticAnalytics.git
cd AgenticAnalytics

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and database connection
```

See [SETUP.md](SETUP.md) for detailed environment setup instructions.

### Configuration

Set required environment variables in `.env`:

```bash
# LLM Provider
LLM_PROVIDER=openai  # or anthropic, google, etc.
OPENAI_API_KEY=your_key_here

# Database
DATABASE_TYPE=duckdb  # or postgresql, mysql, etc.
DATABASE_URL=path/to/database

# Vector Store
VECTOR_STORE_TYPE=faiss  # or weaviate

# Optional: Embedding provider
EMBEDDING_PROVIDER=openai
```

See [PROVIDERS.md](docs/PROVIDERS.md) for detailed configuration of all supported providers.

### Run Data Copilot (UI)

```bash
streamlit run src/app.py
```

The app will auto-initialize your database and RAG system on startup.

### Use Agentic Analytics Programmatically

```python
from src.agents.orchestrator import AgentOrchestrator
from src.rag.rag_system import RAGSystem

# Initialize core framework
orchestrator = AgentOrchestrator()
rag_system = RAGSystem()

# Index your database schema
from src.utils.database import DatabaseManager
db = DatabaseManager()
schema = db.get_schema_info()
rag_system.index_database_schema(schema)

# Run an analytical workflow
query = "What are the top 10 customers by revenue?"
result = orchestrator.run(query)

print(result.final_answer)
print(result.sql_query)
print(result.query_results)
```

## 🏗️ Core Framework Architecture

**Agentic Analytics** is built on a multi-agent orchestration pattern where specialized agents collaborate to execute analytical workflows:



## 📚 Documentation

Complete architecture and implementation details:

- [QUICKSTART.md](QUICKSTART.md) - Step-by-step setup and first use with Data Copilot
- [SETUP.md](SETUP.md) - Comprehensive environment setup guide
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - **Agentic Analytics core architecture and agent orchestration**
- [docs/PROVIDERS.md](docs/PROVIDERS.md) - LLM and database provider configuration
- [docs/HYBRID_ROUTING_IMPLEMENTATION.md](docs/HYBRID_ROUTING_IMPLEMENTATION.md) - Query routing deep dive
- [docs/HYBRID_ROUTING_QUICKREF.md](docs/HYBRID_ROUTING_QUICKREF.md) - Routing examples and usage
- [docs/SQL_SECURITY.md](docs/SQL_SECURITY.md) - SQL injection prevention strategies
- [docs/CACHE_SYSTEM.md](docs/CACHE_SYSTEM.md) - Result caching design and policies
- [docs/STATEFUL_CONVERSATION.md](docs/STATEFUL_CONVERSATION.md) - Conversation history and snapshots
- [docs/STREAMING_STATUS.md](docs/STREAMING_STATUS.md) - Streaming agent reasoning visibility
- [docs/VECTOR_STORES.md](docs/VECTOR_STORES.md) - RAG vector store configuration
- [docs/MULTI_TURN_CONTEXT.md](docs/MULTI_TURN_CONTEXT.md) - Multi-turn conversation context management
- [docs/CHANGELOG.md](docs/CHANGELOG.md) - Version history and updates
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) - Contributing guidelines

## 🛠️ Development

### Project Structure

```
AgenticAnalytics/
├── src/
│   ├── app.py                     # Data Copilot UI (Streamlit)
│   ├── config.py                  # Configuration management
│   ├── styles.css                 # Theme and styling (light/dark modes)
│   ├── agents/                    # Agentic Analytics core agents
│   │   ├── orchestrator.py        # Multi-agent coordinator
│   │   ├── query_classifier.py    # Hybrid query routing (3-tier)
│   │   ├── sql_agent.py           # SQL generation with JOIN intelligence
│   │   ├── analysis_agent.py      # Statistical analysis agent
│   │   ├── visualization_agent.py # Chart and visualization agent
│   │   ├── communication_agent.py # Response formatting agent
│   │   └── base.py                # Base agent class
│   ├── rag/                       # RAG system for schema context
│   │   ├── rag_system.py          # RAG coordinator
│   │   └── vector_store.py        # Vector store implementations
│   └── utils/
│       ├── database.py            # Database connections and queries
│       ├── cache_manager.py       # Result caching system
│       ├── llm_factory.py         # LLM provider factory
│       ├── embedding_factory.py   # Embedding provider factory
│       ├── database_factory.py    # Database factory
│       ├── helpers.py             # Utility functions
│       ├── memory.py              # Session memory management
│       └── session_tables.py      # Session table utilities
├── tests/                         # Test suite for Agentic Analytics
│   ├── conftest.py                # Test configuration
│   ├── test_agents.py             # Agent tests
│   ├── test_database.py           # Database tests
│   └── test_rag.py                # RAG tests
├── examples/                      # Example usage of Agentic Analytics
│   ├── basic_usage.py             # Basic framework usage
│   ├── multi_provider_example.py  # Multi-provider demo
│   ├── vector_store_example.py    # Vector store setup
│   └── test_*.py                  # Various test scripts
├── docs/                          # Detailed documentation
├── data/                          # Sample session data
├── testing/                       # Performance benchmarks & TPC-DS
└── tpcds-kit/                     # TPC-DS benchmark tools
```

**Note:** Agentic Analytics is the core framework (src/agents, src/rag, src/utils). Data Copilot is the reference UI that uses this framework (src/app.py).

### Testing

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_agents.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Building Docker

```bash
docker build -t data-copilot .
docker run -p 8501:8501 data-copilot
```

See [docker-compose.yml](docker-compose.yml) for full stack deployment.

## 🔐 Security

The Agentic Analytics framework implements multiple security layers:

- **SQL Injection Prevention**: Parameterized queries and statement validation
- **Row Limits**: Configurable query result limits (default 1,000 rows)
- **DataFrame Safety**: Type validation and safe DataFrame operations
- **Concurrent Access**: Configurable concurrent read limits with queue management
- **Caching Policy**: Results exceeding limits are not cached
- **Query Validation**: Schema validation before execution

Data Copilot enforces these policies transparently to users.

See [docs/SQL_SECURITY.md](docs/SQL_SECURITY.md) for detailed security architecture.

## 🤝 Contributing

Contributions are welcome! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 🙋 Support

- **Issues**: Report bugs on [GitHub Issues](https://github.com/hollylessthan/AgenticAnalytics/issues)
- **Discussions**: Ask questions on [GitHub Discussions](https://github.com/hollylessthan/AgenticAnalytics/discussions)
- **Documentation**: Check [docs/](docs/) folder for detailed guides

## 📊 Performance Benchmarks

The Agentic Analytics hybrid routing system delivers exceptional performance:

| Query Type | Hybrid Routing | Direct LLM | Speedup |
|---|---|---|---|
| Simple SELECT | 2ms (Regex) | 1200ms | **600x** |
| COUNT/GROUP BY | 5ms (Keywords) | 1150ms | **230x** |
| Complex JOINs | 80ms (LLM) | 1180ms | **15x** |
| **Average** | **28ms** | **1177ms** | **42x** |

The hybrid routing system dramatically improves performance by using fast pattern matching for most queries and only invoking the LLM for complex cases requiring semantic understanding.

Data Copilot users benefit from these performance improvements transparently through faster response times.

See [docs/HYBRID_ROUTING_IMPLEMENTATION.md](docs/HYBRID_ROUTING_IMPLEMENTATION.md) for architecture details.

## 🎯 Roadmap

**Agentic Analytics** future enhancements:
- [ ] Real-time query execution with WebSocket support
- [ ] Advanced anomaly detection with statistical models
- [ ] Custom dashboard creation and saved analysis templates
- [ ] Multi-user collaboration with role-based access control
- [ ] Query optimization suggestions and performance profiling
- [ ] Natural language to dashboard generation

**Data Copilot** roadmap:
- [ ] Collaborative analytics with shared workspaces
- [ ] Custom theming and white-label support
- [ ] Mobile app with offline capabilities
- [ ] Advanced data exploration workflows

---

**Made with ❤️ — Agentic Analytics framework + Data Copilot UI**









































































































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
