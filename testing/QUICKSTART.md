# Quick Testing Guide

Get started with large-scale testing in 5 minutes!

## Quick Start (1GB dataset)

```bash
# 1. Navigate to testing directory
cd testing

# 2. Generate small test data (1GB - takes ~2 minutes)
./generate_tpcds_data.sh 1

# 3. Load into DuckDB (takes ~1 minute)
python setup_tpcds_duckdb.py --scale 1

# 4. Generate RAG documents (takes ~30 seconds)
python generate_rag_documents.py --db-path tpcds_1gb.duckdb

# 5. Run basic tests (takes ~2 minutes)
python run_performance_tests.py --db-path tpcds_1gb.duckdb --test basic
```

**Total time: ~6 minutes** ⚡

## What You Get

After running the quick start, you'll have:

- ✅ **24 tables** with realistic retail data
- ✅ **~1 million rows** across all tables
- ✅ **20+ RAG documents** describing schema and business logic
- ✅ **Test results** showing query performance
- ✅ **Working examples** of SQL, analysis, and visualization

## Test Scales

| Scale | Data Size | Rows | Setup Time | Use Case |
|-------|-----------|------|------------|----------|
| 1GB   | ~1GB      | ~1M  | ~6 min     | Quick validation |
| 10GB  | ~10GB     | ~10M | ~20 min    | Development testing |
| 100GB | ~100GB    | ~2B  | ~45 min    | Production validation |

## Example Queries to Test

Once setup is complete, try these queries:

```bash
# Start the app
cd ..
streamlit run src/app.py
```

**Simple queries:**
- "How many customers do we have?"
- "What are the total sales?"
- "List all product categories"

**Analysis queries:**
- "Show me sales by year"
- "What are the top 10 products by revenue?"
- "Which stores have the highest sales?"

**Complex queries:**
- "Calculate year-over-year sales growth"
- "What products have the highest return rates?"
- "Show monthly trends with 3-month moving average"

**Visualization queries:**
- "Create a bar chart of sales by year"
- "Show a line graph of daily sales trends"
- "Make a pie chart of sales by category"

## Hardware Requirements

### For 1GB (Recommended to start)
- 8GB RAM
- 2 CPU cores
- 5GB free disk space

### For 100GB
- 16GB+ RAM (32GB recommended)
- 4+ CPU cores
- 150GB free disk space

## Configuration

Create `.env` file in the root directory:

```bash
# For local testing (free)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
OPENAI_API_KEY=your-key

DATABASE_TYPE=duckdb
DATABASE_PATH=testing/tpcds_1gb.duckdb

VECTOR_STORE_TYPE=faiss
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

RAG_ENABLED=true
```

## Troubleshooting

### "Command not found: dsdgen"
The script will auto-download and compile TPC-DS tools on first run.

### "Out of memory"
Start with 1GB scale, or close other applications.

### "Database not found"
Make sure you run `setup_tpcds_duckdb.py` after generating data.

### "Slow queries"
This is normal for first run. DuckDB caches data and becomes faster.

## Next Steps

1. ✅ Run quick start (1GB)
2. 🧪 Test with your own questions
3. 📈 Scale up to 10GB
4. 🎯 Benchmark with 100GB
5. 🚀 Deploy to production

## Performance Expectations

### Query Performance (1GB dataset)

| Query Type | Expected Time |
|------------|---------------|
| Simple SELECT | <100ms |
| Aggregation | 100-300ms |
| JOIN (2 tables) | 200-500ms |
| Complex (5+ tables) | 1-3s |
| Full agent flow | 5-15s |

### With 100GB dataset

| Query Type | Expected Time |
|------------|---------------|
| Simple SELECT | <100ms |
| Aggregation | 500ms-2s |
| JOIN (2 tables) | 1-5s |
| Complex (5+ tables) | 5-30s |
| Full agent flow | 10-60s |

## Cost Estimation

**Free setup (local only):**
- DuckDB: Free
- HuggingFace embeddings: Free
- FAISS: Free
- **Total: $0**

**With OpenAI API:**
- GPT-4 Turbo: ~$0.01-0.03 per query
- Embeddings: ~$0.001 per 1000 tokens
- **~100 test queries: ~$2-5**

## Additional Resources

- [Full Testing Guide](README.md) - Complete documentation
- [TPC-DS Specification](http://www.tpc.org/tpcds/) - Benchmark details
- [DuckDB Docs](https://duckdb.org/docs/) - Database documentation

---

**Need help?** Open an issue on [GitHub](https://github.com/hollylessthan/AgenticAnalytics/issues)
