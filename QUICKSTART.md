# Agentic Analytics - Quick Start Guide

Get started with Agentic Analytics in 5 minutes. This guide shows you how to connect your own database to Data Copilot.

## What is Agentic Analytics?

**Agentic Analytics** is a flexible framework that works with **your data**:
- Your database (PostgreSQL, MySQL, DuckDB, Snowflake, BigQuery, etc.)
- Your LLM provider (OpenAI, Claude, Gemini, Bedrock, etc.)
- Your vector store (FAISS, Weaviate, Pinecone, etc.)

**Data Copilot** is the reference interface that demonstrates Agentic Analytics in action.

## Prerequisites

- Python 3.9+
- API key for your chosen LLM provider (OpenAI, Anthropic, Google, AWS, or local)
- Access to a database with data you want to analyze
- Terminal/Command Line

## Step 1: Clone and Setup (1 min)

```bash
# Clone the repository
git clone https://github.com/hollylessthan/AgenticAnalytics.git
cd AgenticAnalytics

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Your Setup (2 min)

Copy the environment template and customize for your data:

```bash
cp .env.example .env
```

Edit `.env` with your database and LLM provider:

### Database Options

```bash
# PostgreSQL
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost:5432/your_database

# MySQL
DATABASE_TYPE=mysql
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/your_database

# DuckDB (local file)
DATABASE_TYPE=duckdb
DATABASE_URL=duckdb:////path/to/your/database.duckdb

# Snowflake
DATABASE_TYPE=snowflake
DATABASE_URL=snowflake://user:password@account.region/database/schema

# BigQuery
DATABASE_TYPE=bigquery
DATABASE_URL=bigquery://project-id/dataset

# Redshift
# Option 1: User/Password (Standard)
DATABASE_TYPE=redshift
DATABASE_URL=postgresql://user:password@cluster.region.redshift.amazonaws.com:5439/database

# Option 2: IAM Role (Recommended for production)
DATABASE_TYPE=redshift
DATABASE_URL=postgresql://awsuser@cluster.region.redshift.amazonaws.com:5439/database
REDSHIFT_CLUSTER_ID=your-cluster-id
REDSHIFT_IAM_ROLE=arn:aws:iam::123456789012:role/YourRedshiftRole
AWS_REGION=us-east-1
# Will automatically get temporary credentials from IAM

# SQLite
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:////path/to/database.db
```

### LLM Provider Options

```bash
# OpenAI (gpt-4o, gpt-4, gpt-3.5-turbo)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Anthropic Claude (claude-3-5-sonnet, claude-3-opus)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key-here

# Google Gemini
LLM_PROVIDER=google
GOOGLE_API_KEY=your-key-here

# AWS Bedrock (Claude, Llama, Mistral)
# Option 1: Explicit Credentials
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret

# Option 2: boto3 Profile (e.g., from ~/.aws/config)
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
AWS_PROFILE=my-profile
USE_BOTO3_SESSION=true

# Option 3: IAM Role (EC2/ECS/Lambda)
# Just set region - boto3 will auto-detect IAM role
LLM_PROVIDER=bedrock
AWS_REGION=us-east-1
USE_BOTO3_SESSION=true

# Local Model (Ollama)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2  # or any model you have installed
```

### Vector Store Options

```bash
# In-memory FAISS (default, no setup needed)
VECTOR_STORE_TYPE=faiss

# Weaviate (persistent, recommended for production)
VECTOR_STORE_TYPE=weaviate
WEAVIATE_URL=http://localhost:8080

# Pinecone (cloud-hosted)
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=your-key-here
PINECONE_INDEX_NAME=analytics

# Chroma (lightweight, local)
VECTOR_STORE_TYPE=chroma
CHROMA_PERSIST_DIRECTORY=./chroma_data

# Azure Cognitive Search (enterprise scale)
VECTOR_STORE_TYPE=azure_search
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
AZURE_SEARCH_KEY=your-admin-key
AZURE_SEARCH_INDEX_NAME=analytics

# AWS OpenSearch (enterprise scale, 10M+ documents)
VECTOR_STORE_TYPE=opensearch
OPENSEARCH_URL=https://your-domain.region.es.amazonaws.com
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your-password

# AWS Kendra (enterprise document retrieval with ML)
VECTOR_STORE_TYPE=kendra
KENDRA_INDEX_ID=your-index-id
AWS_REGION=us-east-1

# AWS Aurora PostgreSQL with pgvector (hybrid queries)
VECTOR_STORE_TYPE=aurora_pgvector
AURORA_HOST=your-cluster.region.rds.amazonaws.com
AURORA_PORT=5432
AURORA_USER=postgres
AURORA_PASSWORD=your-password
AURORA_DB_NAME=analytics

# AWS DynamoDB (serverless, <100K documents)
VECTOR_STORE_TYPE=dynamodb
DYNAMODB_TABLE_NAME=documents
AWS_REGION=us-east-1

# Google Cloud Vertex AI Vector Search (managed, 1M+ documents)
VECTOR_STORE_TYPE=vertex_ai
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1
VERTEX_AI_INDEX_ID=your-index-id
VERTEX_AI_ENDPOINT=your-endpoint-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

## Example Configurations

### Quick Start (with sample data)
```bash
DATABASE_TYPE=duckdb
DATABASE_URL=duckdb:///./testing/tpcds_1gb.duckdb
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
VECTOR_STORE_TYPE=faiss
```

### PostgreSQL + Claude + Weaviate
```bash
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@localhost:5432/analytics
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-key
VECTOR_STORE_TYPE=weaviate
WEAVIATE_URL=http://localhost:8080
```

### Snowflake + Local Llama2
```bash
DATABASE_TYPE=snowflake
DATABASE_URL=snowflake://user:pass@account/database/schema
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
VECTOR_STORE_TYPE=faiss
```

## Step 3: Optional - Use Sample Data (Skip if using your own database)

If you want to test with sample data first:

```bash
# Generate 1GB TPC-DS benchmark data
cd testing
./generate_tpcds_data.sh 1

# Load into DuckDB
python setup_tpcds_duckdb.py --scale 1

# Generate and load RAG documents
python generate_rag_documents.py
python load_rag_documents.py

# Load method cards for ML/statistics recommendations
python load_method_cards.py

cd ..
```

This creates a realistic retail analytics database with:
- 24 tables (customers, orders, products, sales, etc.)
- ~10M rows of realistic data
- Industry-standard TPC-DS schema
- RAG-indexed schema for intelligent query generation
- 40+ method cards for statistical tests and ML models

## Step 4: Launch Data Copilot (1 min)

```bash
# Start the interactive UI
streamlit run src/app.py
```

Visit `http://localhost:8501` in your browser.

Data Copilot will automatically:
1. ✅ Connect to your database
2. ✅ Index your schema with the vector store
3. ✅ Load method cards for ML/statistics (if not already loaded)
4. ✅ Initialize the Agentic Analytics framework
5. ✅ Be ready for natural language queries

## Step 5: Start Querying!

Type natural language questions about your data:

- "Show me the top 10 customers by revenue"
- "What's the average order value by month?"
- "Create a bar chart of sales by product category"
- "Which customers have the highest lifetime value?"
- "Analyze the correlation between price and quantity sold"

Agentic Analytics will:
1. Understand your question
2. Automatically discover relevant tables and relationships
3. Generate optimized SQL for your database
4. Execute the query
5. Analyze results
6. Create visualizations
7. Provide insights

## Using Your Own Data

### Step-by-Step

1. **Update DATABASE_URL** in `.env` to point to your database
   ```bash
   DATABASE_URL=postgresql://user:pass@your-host:5432/your_db
   ```

2. **Choose your LLM provider** and add API key
   ```bash
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-...
   ```

3. **Choose your vector store** (optional, defaults to FAISS)
   ```bash
   VECTOR_STORE_TYPE=weaviate
   WEAVIATE_URL=http://localhost:8080
   ```

4. **Load method cards for ML/statistics** (one-time setup)
   ```bash
   cd testing
   python load_method_cards.py
   cd ..
   ```
   This indexes 40+ statistical tests and ML algorithms for intelligent recommendations during modeling.

5. **Run Data Copilot**
   ```bash
   streamlit run src/app.py
   ```

6. **Agentic Analytics automatically**:
   - Discovers all your tables and columns
   - Indexes schema for intelligent query generation
   - Loads method cards for ML recommendations
   - Ready to answer questions about your data

### Agentic Analytics Supports

✅ **Any database** with SQLAlchemy drivers  
✅ **Any LLM** from OpenAI, Anthropic, Google, AWS, or local  
✅ **Multiple vector stores** (FAISS, Weaviate, Pinecone, Chroma)  
✅ **Billions of rows** with smart caching and limits  
✅ **Complex schemas** with automatic JOIN discovery  
✅ **Real-time queries** with streaming results  

## Programmatic Usage

You can also use Agentic Analytics as a library:

```python
from src.agents.orchestrator import AgentOrchestrator
from src.rag.rag_system import RAGSystem
from src.utils.database import DatabaseManager

# Initialize
orchestrator = AgentOrchestrator()
rag_system = RAGSystem()
db = DatabaseManager()

# Index your schema
schema = db.get_schema_info()
rag_system.index_database_schema(schema)

# Run a query
result = orchestrator.run("What are the top 10 customers?")

print(result.final_answer)
print(result.sql_query)
print(result.query_results)
```

## Troubleshooting

### Error: "model does not exist"
- Update `LLM_PROVIDER` and API key in `.env`
- Available models:
  - OpenAI: `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`
  - Anthropic: `claude-3-5-sonnet`, `claude-3-opus`
  - Google: `gemini-2.0-flash`, `gemini-1.5-pro`

### Warning: "Could not load FAISS index"
- **This is normal on first run!** The index is created automatically
- The warning disappears after Data Copilot initializes

### Error: "Failed to initialize systems"
- Check `.env` has correct database connection string
- Verify LLM API key is valid
- Make sure virtual environment is activated

### Error: Database connection failed
- Verify `DATABASE_URL` in `.env` is correct
- Check database is running and accessible
- Test connection: `python -c "from sqlalchemy import create_engine; create_engine('YOUR_DATABASE_URL').connect()"`

### Streamlit won't start
- Make sure port 8501 is available
- Try different port: `streamlit run src/app.py --server.port 8502`

## Next Steps

- **Setup Weaviate for production**: `docker run -d -p 8080:8080 semitechnologies/weaviate:latest`
- **Add example queries**: Index your domain-specific queries for better SQL generation
- **Customize agents**: Modify `src/agents/` for your specific use cases
- **Deploy to cloud**: Use Docker or deploy to Heroku, AWS, GCP, etc.

## Common Questions

**Q: Can I use my own database?**  
A: Yes! Update `DATABASE_URL` in `.env` with your connection string. Agentic Analytics supports any SQLAlchemy-compatible database.

**Q: Which LLM should I use?**  
A: Start with OpenAI's `gpt-4o` for best results. Claude and Gemini also work well. Use local Ollama to avoid API costs.

**Q: Does it work with my data volume?**  
A: Yes! Agentic Analytics includes query result caching, row limits, and smart indexing for databases from 1GB to 100GB+.

**Q: How do I improve SQL generation?**  
A: Index your database schema (automatic) and add example queries to the RAG system. See [docs/VECTOR_STORES.md](docs/VECTOR_STORES.md).

**Q: Can I customize the agents?**  
A: Yes! Agentic Analytics is fully extensible. Create new agents inheriting from `BaseAgent` and add to the orchestrator.

**Q: How do I deploy this?**  
A: Use Docker or deploy to cloud platforms. See [Dockerfile](Dockerfile) and [docker-compose.yml](docker-compose.yml).

## Need Help?

- 📖 Read [README.md](README.md) for full documentation
- 🏗️ See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design
- 📚 Check [docs/PROVIDERS.md](docs/PROVIDERS.md) for detailed provider setup
- 🐛 Report issues on [GitHub](https://github.com/hollylessthan/AgenticAnalytics/issues)
- 💡 See [examples/](examples/) for code samples

---

**Ready to analyze your data with Agentic Analytics? 🚀**
