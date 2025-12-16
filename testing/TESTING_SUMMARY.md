# Testing Infrastructure Summary

Complete large-scale testing infrastructure for Agentic Analytics.

## 📦 What's Included

### 1. Data Generation (`generate_tpcds_data.sh`)
- Bash script to download and compile TPC-DS tools
- Generates 1GB, 10GB, or 100GB of test data
- Supports parallel data generation
- Auto-detects OS (macOS/Linux)
- ~30 minutes for 100GB with 4 cores

### 2. Database Setup (`setup_tpcds_duckdb.py`)
- Loads TPC-DS CSV data into DuckDB
- Creates all 24 tables with proper schemas
- Builds indexes on key columns
- Analyzes tables for query optimization
- Validates data integrity
- **~10 minutes for 100GB**

### 3. RAG Document Generator (`generate_rag_documents.py`)
- Generates comprehensive markdown documentation
- Schema overview with business context
- Individual table documentation
- Common query patterns
- Business glossary
- **Creates 25+ documents for RAG**

### 4. Performance Testing (`run_performance_tests.py`)
- Runs test queries across complexity levels
- Measures end-to-end performance
- Tests SQL generation, analysis, visualization
- Generates detailed metrics and reports
- Saves results to JSON

### 5. Documentation
- **README.md**: Complete setup and usage guide
- **QUICKSTART.md**: 5-minute getting started guide
- Both include troubleshooting and best practices

## 🎯 Test Coverage

### Test Query Types

**Basic (3 queries)**
- Simple SELECT queries
- Table counts
- Column listings

**Intermediate (4 queries)**
- Aggregations
- 2-table JOINs
- GROUP BY operations
- TOP N queries

**Advanced (4 queries)**
- Window functions
- Multi-table JOINs (5+ tables)
- Year-over-year calculations
- Complex analytics

**Visualization (3 queries)**
- Bar charts
- Line graphs
- Pie charts

**Multi-Channel (2 queries)**
- Cross-channel analysis
- Union queries
- Return rate analysis

**Total: 16 test queries** covering all capabilities

## 📊 TPC-DS Schema

### Fact Tables (7)
1. `store_sales` - Store transactions (~1.6B rows at 100GB)
2. `store_returns` - Store returns
3. `catalog_sales` - Catalog orders
4. `catalog_returns` - Catalog returns
5. `web_sales` - Website orders
6. `web_returns` - Web returns
7. `inventory` - Daily inventory levels

### Dimension Tables (17)
- `customer` - Customer master data
- `date_dim` - Date dimension (18 years)
- `time_dim` - Time of day
- `item` - Product catalog
- `store` - Store locations
- `warehouse` - Distribution centers
- `customer_demographics` - Demographics
- `customer_address` - Geographic data
- `household_demographics` - Household info
- `promotion` - Marketing promotions
- `reason` - Return reasons
- `ship_mode` - Shipping methods
- And 5 more...

**At 100GB scale:**
- ~2 billion total rows
- ~100GB raw CSV data
- ~20-30GB in DuckDB (5x compression)

## 💡 Key Features

### DuckDB Advantages
- ✅ Columnar storage (efficient compression)
- ✅ In-process (no server needed)
- ✅ OLAP-optimized (fast analytics)
- ✅ Handles 100GB on 16GB RAM
- ✅ Portable (single file database)
- ✅ SQL standard compliant

### RAG Document Quality
- ✅ Business context for every table
- ✅ Table relationships documented
- ✅ Common query patterns
- ✅ Metric definitions
- ✅ Sample SQL queries
- ✅ Markdown format (LLM-friendly)

### Performance Metrics
- ✅ Per-query timing
- ✅ Success/failure tracking
- ✅ Complexity-based analysis
- ✅ Feature coverage reporting
- ✅ JSON export for analysis

## 🚀 Usage Examples

### Quick Test (1GB)
```bash
cd testing
./generate_tpcds_data.sh 1
python setup_tpcds_duckdb.py --scale 1
python generate_rag_documents.py --db-path tpcds_1gb.duckdb
python run_performance_tests.py --db-path tpcds_1gb.duckdb --test basic
```
**Time: ~6 minutes**

### Full Test (100GB)
```bash
cd testing
./generate_tpcds_data.sh 100 4  # 4 parallel processes
python setup_tpcds_duckdb.py --scale 100
python generate_rag_documents.py --db-path tpcds_100gb.duckdb
python run_performance_tests.py --db-path tpcds_100gb.duckdb --test all
```
**Time: ~45 minutes**

### Custom Test
```bash
# Test specific query types
python run_performance_tests.py \
  --db-path tpcds_100gb.duckdb \
  --test advanced \
  --rag-enabled \
  --output results/advanced_test.json
```

## 📈 Expected Results

### 100GB Performance Benchmarks

**Query Execution (DuckDB only):**
- Simple SELECT: <100ms
- Aggregation: 500ms-2s
- 2-table JOIN: 1-5s
- Complex JOIN (5+ tables): 5-30s

**Full Agent Flow (LLM + SQL + Analysis):**
- Basic queries: 5-15s
- Intermediate: 10-30s
- Advanced: 20-60s

**Bottlenecks:**
1. LLM API calls (1-3s)
2. Complex SQL queries (5-30s)
3. RAG retrieval (200-500ms)

## 🎓 What This Tests

### SQL Agent
- ✅ Schema understanding via RAG
- ✅ Natural language → SQL translation
- ✅ Complex query generation
- ✅ Multi-table JOINs
- ✅ Aggregations and window functions

### Analysis Agent
- ✅ Data interpretation
- ✅ Statistical analysis
- ✅ Insight generation
- ✅ Trend identification

### Visualization Agent
- ✅ Chart type selection
- ✅ Data preparation
- ✅ Visualization generation
- ✅ Multiple chart types

### RAG System
- ✅ Schema retrieval
- ✅ Query pattern matching
- ✅ Context augmentation
- ✅ Few-shot learning

### Database Integration
- ✅ DuckDB connectivity
- ✅ Large dataset handling
- ✅ Query performance
- ✅ Result processing

## 🔧 Configuration Options

### Scale Selection
```bash
# Small test (fast)
./generate_tpcds_data.sh 1

# Medium test (balanced)
./generate_tpcds_data.sh 10

# Large test (production)
./generate_tpcds_data.sh 100
```

### Parallel Generation
```bash
# Single process (default)
./generate_tpcds_data.sh 100

# 4 parallel processes (faster)
./generate_tpcds_data.sh 100 4
```

### Test Suites
```bash
# Basic tests only
python run_performance_tests.py --test basic

# Intermediate tests
python run_performance_tests.py --test intermediate

# Advanced tests
python run_performance_tests.py --test advanced

# All tests
python run_performance_tests.py --test all
```

### RAG Integration
```bash
# Without RAG
python run_performance_tests.py --db-path tpcds_100gb.duckdb

# With RAG
python run_performance_tests.py \
  --db-path tpcds_100gb.duckdb \
  --rag-enabled \
  --rag-docs rag_documents/
```

## 📦 File Structure

```
testing/
├── README.md                      # Complete guide
├── QUICKSTART.md                  # 5-minute guide
├── .gitignore                     # Ignore test data
├── generate_tpcds_data.sh         # Data generation script
├── setup_tpcds_duckdb.py          # Database loader
├── generate_rag_documents.py      # RAG doc generator
├── run_performance_tests.py       # Test runner
├── data/                          # Generated CSV files (gitignored)
│   └── tpcds/
├── rag_documents/                 # Generated docs (gitignored)
│   ├── schema_overview.md
│   ├── query_patterns.md
│   ├── business_glossary.md
│   └── tables/
│       ├── store_sales.md
│       ├── customer.md
│       └── ...
├── tpcds_1gb.duckdb              # 1GB database (gitignored)
├── tpcds_10gb.duckdb             # 10GB database (gitignored)
├── tpcds_100gb.duckdb            # 100GB database (gitignored)
└── test_results.json             # Test results (gitignored)
```

## 🎯 Benefits

### For Development
- ✅ Test with realistic data volumes
- ✅ Identify performance bottlenecks
- ✅ Validate query generation
- ✅ Test RAG effectiveness

### For Users
- ✅ Clear setup instructions
- ✅ Reproducible benchmarks
- ✅ No cloud costs (local)
- ✅ Industry-standard data

### For Documentation
- ✅ Real performance metrics
- ✅ Concrete examples
- ✅ Proven scalability
- ✅ Best practices

## 🔍 Troubleshooting Coverage

Documentation includes solutions for:
- TPC-DS tools installation
- Memory constraints
- Slow query performance
- RAG retrieval issues
- Data generation errors
- Database connection problems

## 🎉 Summary

**What you can do:**
1. ✅ Generate industry-standard test data (1-100GB)
2. ✅ Load into high-performance local database
3. ✅ Generate comprehensive RAG documents
4. ✅ Run automated performance tests
5. ✅ Benchmark all system capabilities
6. ✅ Export results for analysis

**Time investment:**
- Setup: 6 minutes (1GB) to 45 minutes (100GB)
- Testing: 5-30 minutes depending on scope
- **Total: Can validate full system in under 1 hour**

**Cost:**
- Data generation: Free
- DuckDB: Free
- Testing infrastructure: Free
- **Only LLM API calls have cost (~$2-5 for full test suite)**

---

**This provides production-grade testing capability at zero infrastructure cost!** 🚀
