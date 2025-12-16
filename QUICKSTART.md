# Agentic Analytics - Quick Start Guide

This guide will help you get started with Agentic Analytics in 5 minutes.

## Prerequisites

- Python 3.9+
- OpenAI API Key
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

## Step 2: Configure (1 min)

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

**Note**: The default configuration uses:
- Database: `duckdb:///./testing/tpcds_1gb.duckdb` (TPC-DS test data)
- Model: `gpt-4.1`
- Vector Store: `faiss` (will be created on first use)

## Step 3: Setup Test Database (2 min)

```bash
# Generate 1GB TPC-DS benchmark data
cd testing
./generate_tpcds_data.sh 1

# Load into DuckDB
python setup_tpcds_duckdb.py --scale 1

# Generate RAG documents
python generate_rag_documents.py
cd ..
```

This creates a DuckDB database with industry-standard TPC-DS retail data:
- 24 tables (customers, orders, products, sales, etc.)
- Realistic retail analytics schema
- 1GB of data (~10M rows)

## Step 4: Run the App (1 min)

```bash
# Make sure you're in the project root directory
streamlit run src/app.py
```

The app will open in your browser at `http://localhost:8501`

## Step 5: Try It Out! (1 min)

1. Click **"Initialize/Reinitialize Systems"** in the sidebar
2. Click **"Index Database Schema"** to enable SQL generation
3. Try these queries:

### Easy Queries
```
Show me all customers
What products do we have?
How many orders were placed?
```

### Analysis Queries
```
What are the top 10 customers by total spending?
Show me monthly sales trends
What's the average order value by country?
```

### Visualization Queries
```
Create a bar chart of sales by product category
Show me a line chart of revenue over time
Plot the distribution of order amounts
```

## Example Workflow

**Query:** "What are the top 5 products by revenue and show me a bar chart"

The system will:
1. 🔍 Understand your intent
2. 📝 Generate SQL query
3. 📊 Retrieve the data
4. 📈 Create visualization
5. 💬 Give you a summary

## Command Line Usage

If you prefer command line:

```bash
python examples/basic_usage.py
```

## Troubleshooting

### Error: "model does not exist" (e.g., gpt-4-turbo-preview)
- Update `AGENT_MODEL` in `.env` to a current model like `gpt-4o` or `gpt-4`
- Available models: OpenAI (gpt-4o, gpt-4, gpt-3.5-turbo), Claude (claude-3-5-sonnet-20241022)

### Warning: "Could not load FAISS index: No such file or directory"
- **This is completely normal on first run!** The FAISS index doesn't exist yet.
- The index will be automatically created when you:
  1. Click **"Index Database Schema"** in the sidebar
  2. The warning will disappear after indexing
- You can safely ignore this warning until you index your schema

### Error: "Failed to initialize systems"
- Check your `.env` file has `OPENAI_API_KEY`
- Verify your OpenAI API key is valid
- Make sure you activated the virtual environment: `source venv/bin/activate`

### Error: "attempted relative import beyond top-level package"
- **Make sure you're running from the project root directory** (AgenticAnalytics/)
- Check your current directory: `pwd` should show `.../AgenticAnalytics`
- If you're in the wrong directory, run: `cd /path/to/AgenticAnalytics`
- Then run: `streamlit run src/app.py`

### Error: "Can't load plugin: sqlalchemy.dialects:duckdb"
- Install the DuckDB SQLAlchemy driver: `pip install duckdb-engine`
- This package is required to use DuckDB with SQLAlchemy

### Error: Database connection failed
- Make sure you ran the TPC-DS setup in Step 3
- Check `DATABASE_URL` in `.env` points to `duckdb:///./testing/tpcds_1gb.duckdb`
- Verify the database file exists: `ls -lh testing/tpcds_1gb.duckdb`

### Streamlit won't start
- Make sure port 8501 is available
- Try: `streamlit run src/app.py --server.port 8502`

## Next Steps

- **Use Your Own Database**: Update `DATABASE_URL` in `.env`
- **Customize Agents**: Modify agents in `src/agents/`
- **Add Examples**: Index query examples for better SQL generation
- **Deploy**: Use Docker or deploy to cloud

## Common Questions

**Q: Can I use my own database?**
A: Yes! Update `DATABASE_URL` in `.env` with your connection string.

**Q: Does it work with PostgreSQL/MySQL?**
A: Yes! The system supports any SQLAlchemy-compatible database.

**Q: How do I improve SQL generation?**
A: Index your database schema and add example queries using the RAG system.

**Q: Can I add custom agents?**
A: Yes! Inherit from `BaseAgent` and add to the orchestrator.

## Need Help?

- 📖 Read the full [README.md](README.md)
- 🐛 Report issues on [GitHub](https://github.com/hollylessthan/AgenticAnalytics/issues)
- 💡 Check [examples/](examples/) for more code samples

---

**Happy Analyzing! 🎉**
