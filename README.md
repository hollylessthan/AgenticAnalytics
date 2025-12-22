# Agentic Analytics

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

> A core framework for agent-assisted analytical workflows, with a reference user interface called **Data Copilot**.

**Agentic Analytics** is a core analytics framework that orchestrates specialized agents to support multi-step analytical workflows, including SQL execution, statistical analysis, predictive modeling, visualization, and human-readable summaries.

**Data Copilot** is the reference user interface built on top of Agentic Analytics. It provides an interactive experience for querying, validating, and exploring analytical data while the core framework handles planning, execution, and verification behind the scenes.

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
│  - Data profiling, preprocessing, modeling   │
│  - Analysis & visualization agents           │
│  - RAG-powered schema & method cards         │
│  - Result caching & security                 │
└──────────────────────────────────────────────┘
```

## Key Features

- **Multi-Agent Architecture**: Specialized agents for SQL, profiling, preprocessing, modeling, analysis, visualization, and communication
- **Hybrid Routing System**: 3-tier intelligent query classification (Regex -> Keywords -> LLM) for optimal performance
- **RAG Integration**: Schema indexing and 40+ curated method cards for intelligent statistical/ML recommendations
- **ML Pipeline Support**: Full workflow with profiling, preprocessing, and model training with error-aware retry
- **Human-in-the-Loop**: User confirmation for preprocessing decisions with transparent recommendations
- **Security First**: SQL injection prevention, safe DataFrame handling, query row limits
- **Smart Caching**: Result caching with configurable limits and concurrent read access
- **Real-time Visualization**: Inline charts and tables with automatic formatting
- **Stateful Conversations**: 10-turn conversation history with snapshot rollback capability
- **Streaming Transparency**: Real-time agent reasoning visibility with callback-based streaming
- **Flexible & Extensible**: Works with any database, LLM provider, and vector store — customize for your data

## Flexible Framework for Any Database

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
LanceDB (default)         FAISS (in-memory)      Weaviate
Chroma                    OpenSearch             Pinecone
Kendra                    Aurora pgvector        DynamoDB
Vertex AI                 Azure Cognitive Search
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

## Quick Demo

Watch a demo of Data Copilot in action:

https://github.com/user-attachments/assets/42e5ec63-d981-4aac-9908-539cc2d7ad2c

**In this demo:**
- Multi-agent SQL generation & execution
- Real-time visualization & analysis
- Stateful conversation memory
- Streaming agent reasoning visibility

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

## Core Framework Architecture

**Agentic Analytics** is built on a multi-agent orchestration pattern where specialized agents collaborate to execute analytical workflows:



## Documentation

Complete architecture and implementation details:

- [QUICKSTART.md](QUICKSTART.md) - Step-by-step setup and first use with Data Copilot
- [SETUP.md](SETUP.md) - Comprehensive environment setup guide
- [STREAMLIT_TESTING.md](STREAMLIT_TESTING.md) - Testing scenarios and validation guide
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - **Agentic Analytics core architecture and agent orchestration**
- [docs/PROVIDERS.md](docs/PROVIDERS.md) - LLM and database provider configuration
- [docs/METHOD_CARDS.md](docs/METHOD_CARDS.md) - Statistical methods and ML algorithm knowledge base
- [docs/RAG_SYSTEM.md](docs/RAG_SYSTEM.md) - RAG system architecture and vector stores
- [docs/HYBRID_ROUTING_IMPLEMENTATION.md](docs/HYBRID_ROUTING_IMPLEMENTATION.md) - Query routing deep dive
- [docs/HYBRID_ROUTING_QUICKREF.md](docs/HYBRID_ROUTING_QUICKREF.md) - Routing examples and usage
- [docs/ERROR_AWARE_RETRY.md](docs/ERROR_AWARE_RETRY.md) - Error-aware retry for code generation agents
- [docs/SQL_SECURITY.md](docs/SQL_SECURITY.md) - SQL injection prevention strategies
- [docs/CACHE_SYSTEM.md](docs/CACHE_SYSTEM.md) - Result caching design and policies
- [docs/STATEFUL_CONVERSATION.md](docs/STATEFUL_CONVERSATION.md) - Conversation history and snapshots
- [docs/STREAMING_STATUS.md](docs/STREAMING_STATUS.md) - Streaming agent reasoning visibility
- [docs/MULTI_TURN_CONTEXT.md](docs/MULTI_TURN_CONTEXT.md) - Multi-turn conversation context management
- [docs/CHANGELOG.md](docs/CHANGELOG.md) - Version history and updates
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) - Contributing guidelines

## Development

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
│   │   ├── profiling_agent.py     # Data profiling and quality assessment
│   │   ├── preprocessing_agent.py # Data preprocessing with error-aware retry
│   │   ├── modeling_agent.py      # ML model training with error-aware retry
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

## Security

The Agentic Analytics framework implements multiple security layers:

- **SQL Injection Prevention**: Parameterized queries and statement validation
- **Row Limits**: Configurable query result limits (default 1,000 rows)
- **DataFrame Safety**: Type validation and safe DataFrame operations
- **Concurrent Access**: Configurable concurrent read limits with queue management
- **Caching Policy**: Results exceeding limits are not cached
- **Query Validation**: Schema validation before execution

Data Copilot enforces these policies transparently to users.

See [docs/SQL_SECURITY.md](docs/SQL_SECURITY.md) for detailed security architecture.

## Contributing

Contributions are welcome! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the Apache License 2.0 - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: Report bugs on [GitHub Issues](https://github.com/hollylessthan/AgenticAnalytics/issues)
- **Discussions**: Ask questions on [GitHub Discussions](https://github.com/hollylessthan/AgenticAnalytics/discussions)
- **Documentation**: Check [docs/](docs/) folder for detailed guides

## Roadmap

**Agentic Analytics** future enhancements:
- [ ] Advanced modeling capabilities (AutoML, hyperparameter tuning, ensemble methods)
- [ ] Benchmarking and performance monitoring (execution time tracking, resource usage)
- [ ] Observability and instrumentation (OpenTelemetry integration, distributed tracing)
- [ ] LLM guardrails (input/output validation, prompt injection prevention, content filtering)
- [ ] Real-time query execution with WebSocket support
- [ ] Custom dashboard creation and saved analysis templates
- [ ] Multi-user collaboration with role-based access control
- [ ] Natural language to dashboard generation

**Data Copilot** roadmap:
- [ ] Collaborative analytics with shared workspaces
- [ ] Custom theming and white-label support
- [ ] Mobile app with offline capabilities
- [ ] Advanced data exploration workflows

---

**Made with ❤️ — Agentic Analytics framework + Data Copilot UI**
