# Large-Scale Testing Guide

Test Agentic Analytics with TPC-DS benchmark data (up to 100GB) using DuckDB locally.

## Why TPC-DS + DuckDB?

- **TPC-DS**: Industry-standard benchmark with realistic retail/e-commerce schema (24 tables)
- **DuckDB**: Fast analytical database, handles 100GB+ on laptop, zero setup, free
- **Local**: No cloud costs, full control, reproducible results

## Quick Start

```bash
# 1. Generate test data (takes ~30 min for 100GB)
cd testing
./generate_tpcds_data.sh 100  # 100GB scale

# 2. Load into DuckDB (takes ~10 min)
python setup_tpcds_duckdb.py

# 3. Generate RAG documents
python generate_rag_documents.py

# 4. Run performance tests
python run_performance_tests.py
```

## Detailed Setup

### Step 1: Install TPC-DS Tools

#### macOS
```bash
brew install gcc
git clone https://github.com/databricks/tpcds-kit.git
cd tpcds-kit/tools
make OS=MACOS
```

#### Linux
```bash
sudo apt-get install gcc make
git clone https://github.com/databricks/tpcds-kit.git
cd tpcds-kit/tools
make OS=LINUX
```

#### Windows (WSL recommended)
```bash
# Use WSL Ubuntu
sudo apt-get install gcc make
git clone https://github.com/databricks/tpcds-kit.git
cd tpcds-kit/tools
make OS=LINUX
```

### Step 2: Generate TPC-DS Data

```bash
cd tpcds-kit/tools

# Small test (1GB) - for quick validation
./dsdgen -scale 1 -dir ../../testing/data/tpcds

# Medium test (10GB) - for development
./dsdgen -scale 10 -dir ../../testing/data/tpcds

# Large test (100GB) - for production validation
./dsdgen -scale 100 -dir ../../testing/data/tpcds -parallel 4
```

**Time Estimates:**
- 1GB: ~2 minutes
- 10GB: ~15 minutes
- 100GB: ~30 minutes (with parallelization)

**Disk Space:**
- 1GB scale = ~1GB of CSV files
- 10GB scale = ~10GB of CSV files
- 100GB scale = ~100GB of CSV files

### Step 3: Load into DuckDB

```bash
cd testing
python setup_tpcds_duckdb.py --scale 100
```

This will:
- Create `tpcds_100gb.duckdb` database
- Load all 24 TPC-DS tables
- Create indexes for performance
- Validate data integrity
- Generate statistics

**DuckDB Benefits:**
- Columnar storage: ~5-10x compression
- In-process: No server setup
- Fast analytics: Optimized for OLAP queries
- Handles 100GB on 16GB RAM laptop

### Step 4: Generate RAG Documents

```bash
python generate_rag_documents.py
```

Creates comprehensive documentation:
- Schema overview (tables, columns, types)
- Table relationships (foreign keys)
- Business logic explanations
- Sample queries and use cases
- Data dictionary with descriptions

Output: `testing/rag_documents/` folder with markdown files

### Step 5: Run Tests

```bash
# Basic functionality test
python run_performance_tests.py --test basic

# Full performance test (99 TPC-DS queries)
python run_performance_tests.py --test full

# Custom test with specific queries
python run_performance_tests.py --test custom --queries "sales analysis,customer behavior"
```

## Test Scenarios

### 1. Simple Aggregation
**Query:** "What are the total sales by year?"
**Tests:** Basic SQL generation, aggregation

### 2. Multi-Table Join
**Query:** "Show top 10 customers by revenue with their demographics"
**Tests:** JOIN operations, RAG retrieval for schema understanding

### 3. Complex Analytics
**Query:** "Calculate year-over-year sales growth by category with moving averages"
**Tests:** Window functions, complex calculations, visualization

### 4. Time-Series Analysis
**Query:** "Show daily sales trends with seasonality analysis"
**Tests:** Date operations, statistical analysis, plotting

### 5. RAG-Assisted Query
**Query:** "Which products have declining sales but high return rates?"
**Tests:** RAG for business logic, multi-metric analysis

## Performance Benchmarks

### Expected Performance (100GB on M1 MacBook Pro)

| Query Type | DuckDB Time | Expected |
|------------|-------------|----------|
| Simple SELECT | <100ms | ✅ Fast |
| Aggregation | 200-500ms | ✅ Fast |
| 2-table JOIN | 500ms-2s | ✅ Good |
| Complex JOIN (5+ tables) | 2-10s | ✅ Acceptable |
| Window Functions | 1-5s | ✅ Good |
| Full Table Scan | 5-30s | ✅ Acceptable |

### Agent Performance

| Component | Expected Time |
|-----------|---------------|
| RAG Retrieval | 200-500ms |
| SQL Generation | 1-3s |
| Query Execution | Varies (see above) |
| Analysis | 2-5s |
| Visualization | 1-3s |
| **Total** | **5-40s** |

## Hardware Requirements

### Minimum (1GB-10GB scale)
- 8GB RAM
- 2 CPU cores
- 20GB free disk space

### Recommended (100GB scale)
- 16GB RAM
- 4+ CPU cores
- 150GB free disk space (100GB data + 50GB DuckDB)

### Optimal (100GB scale)
- 32GB RAM
- 8+ CPU cores
- 200GB SSD

## TPC-DS Schema Overview

### Fact Tables (7)
- `store_sales` - Store sales transactions (largest table)
- `store_returns` - Product returns
- `catalog_sales` - Catalog/online sales
- `catalog_returns` - Catalog returns
- `web_sales` - Website sales
- `web_returns` - Web returns
- `inventory` - Daily inventory levels

### Dimension Tables (17)
- `customer` - Customer information
- `customer_demographics` - Demographics
- `customer_address` - Addresses
- `date_dim` - Date dimension
- `item` - Product catalog
- `store` - Store locations
- `warehouse` - Warehouses
- `promotion` - Promotions
- `time_dim` - Time of day
- And 8 more...

**Total rows at 100GB scale:** ~2 billion rows

## Configuration

### .env for Testing

```bash
# Database
DATABASE_TYPE=duckdb
DATABASE_PATH=testing/tpcds_100gb.duckdb

# LLM (use fast model for testing)
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# Vector Store (local for testing)
VECTOR_STORE_TYPE=faiss
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# RAG
RAG_ENABLED=true
VECTOR_STORE_PATH=testing/vector_store
```

## Troubleshooting

### "Out of memory" error
- Reduce scale (try 10GB instead of 100GB)
- Close other applications
- Use DuckDB's external sorting: `SET temp_directory='/path/to/fast/disk'`

### "Slow query execution"
- Check if indexes exist: `PRAGMA show_tables;`
- Analyze tables: `ANALYZE;`
- Monitor: `PRAGMA enable_profiling;`

### "RAG returns irrelevant results"
- Regenerate embeddings with better model
- Increase chunk size in document generation
- Add more context to RAG documents

### "Agent generates incorrect SQL"
- Check RAG documents contain schema info
- Verify LLM model supports function calling
- Add more examples to RAG documents

## Cost Estimation

### Free (Local Setup)
- DuckDB: Free
- HuggingFace embeddings: Free
- FAISS vector store: Free
- **Cost:** $0

### With API Services (OpenAI + Pinecone)
- OpenAI GPT-4: ~$0.01-0.03 per query
- OpenAI embeddings: ~$0.001 per 1000 tokens
- Pinecone: Free tier (100K vectors)
- **Cost:** ~$5-10 for 500 test queries

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Large Scale Tests
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest-16core
    steps:
      - uses: actions/checkout@v2
      - name: Setup TPC-DS
        run: |
          cd testing
          ./generate_tpcds_data.sh 1  # 1GB for CI
          python setup_tpcds_duckdb.py --scale 1
      - name: Run Tests
        run: python testing/run_performance_tests.py --test basic
```

## Next Steps

1. **Start Small:** Test with 1GB scale first
2. **Validate:** Ensure all queries work correctly
3. **Scale Up:** Move to 10GB, then 100GB
4. **Benchmark:** Record performance metrics
5. **Optimize:** Tune based on results

## Resources

- [TPC-DS Specification](http://www.tpc.org/tpcds/)
- [DuckDB Documentation](https://duckdb.org/docs/)
- [TPC-DS GitHub](https://github.com/databricks/tpcds-kit)

---

**Need help?** Open an issue with your hardware specs and error logs.
