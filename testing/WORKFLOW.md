# Testing Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    TESTING WORKFLOW                              │
└─────────────────────────────────────────────────────────────────┘

Step 1: Generate Test Data (TPC-DS)
┌──────────────────────────┐
│  ./generate_tpcds_data.sh│ → Downloads & compiles TPC-DS tools
│  <scale_factor>          │ → Generates CSV files (1GB-100GB)
└────────────┬─────────────┘
             │ Output: data/tpcds/*.dat files
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  TPC-DS Data Files (~24 tables)                                 │
│  ├── store_sales.dat       (largest - ~60% of data)             │
│  ├── catalog_sales.dat                                          │
│  ├── web_sales.dat                                              │
│  ├── customer.dat                                               │
│  ├── item.dat                                                   │
│  └── ... (19 more tables)                                       │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
Step 2: Load into DuckDB
┌──────────────────────────┐
│ setup_tpcds_duckdb.py    │ → Creates DuckDB database
│ --scale <factor>         │ → Loads all tables
└────────────┬─────────────┘ → Creates indexes
             │                → Analyzes for optimization
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  tpcds_<scale>gb.duckdb                                         │
│  ├── 24 tables loaded                                           │
│  ├── Indexes created                                            │
│  ├── Statistics computed                                        │
│  └── ~5-10x compression vs CSV                                  │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
Step 3: Generate RAG Documents
┌──────────────────────────┐
│ generate_rag_documents.py│ → Analyzes schema
│ --db-path <path>         │ → Generates markdown docs
└────────────┬─────────────┘ → Adds business context
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  rag_documents/                                                 │
│  ├── schema_overview.md        (High-level schema description) │
│  ├── query_patterns.md         (Common SQL patterns)           │
│  ├── business_glossary.md      (Terminology & metrics)         │
│  └── tables/                   (Individual table docs)         │
│      ├── store_sales.md                                         │
│      ├── customer.md                                            │
│      └── ... (24 table docs)                                    │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
Step 4: Run Performance Tests
┌──────────────────────────┐
│ run_performance_tests.py │ → Runs test queries
│ --test <suite>           │ → Measures performance
│ --rag-enabled           │ → Validates functionality
└────────────┬─────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Test Execution Flow                                            │
│                                                                  │
│  For each test query:                                           │
│    1. Question → Orchestrator                                   │
│    2. RAG retrieves schema context                              │
│    3. SQL Agent generates query                                 │
│    4. Execute query on DuckDB                                   │
│    5. Analysis Agent interprets results                         │
│    6. Visualization Agent creates charts (if needed)            │
│    7. Record metrics (time, success, etc.)                      │
│                                                                  │
│  Test Suites:                                                   │
│    ├── basic (3 queries)                                        │
│    ├── intermediate (4 queries)                                 │
│    ├── advanced (4 queries)                                     │
│    ├── visualization (3 queries)                                │
│    └── all (16 queries)                                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Test Results (test_results.json)                               │
│  {                                                               │
│    "total_tests": 16,                                           │
│    "successful": 15,                                            │
│    "average_time": 12.5,                                        │
│    "results": [                                                 │
│      {                                                           │
│        "question": "...",                                       │
│        "success": true,                                         │
│        "total_time": 8.5,                                       │
│        "sql_generated": "SELECT ...",                           │
│        "analysis_provided": true,                               │
│        "visualization_created": true                            │
│      },                                                          │
│      ...                                                         │
│    ]                                                             │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    PARALLEL OPTION                               │
│  Alternative: Use with Main Application                          │
│                                                                  │
│  examples/tpcds_example.py --scale 10 --interactive             │
│                                                                  │
│  ┌──────────────┐                                               │
│  │ User Query   │                                               │
│  └──────┬───────┘                                               │
│         │                                                        │
│         ▼                                                        │
│  ┌──────────────────────┐                                       │
│  │ AgentOrchestrator    │                                       │
│  └──────┬───────────────┘                                       │
│         │                                                        │
│         ├──→ RAG System (rag_documents/)                        │
│         │                                                        │
│         ├──→ SQL Agent                                          │
│         │      │                                                 │
│         │      ▼                                                 │
│         │   DuckDB (tpcds_10gb.duckdb)                          │
│         │                                                        │
│         ├──→ Analysis Agent                                     │
│         │                                                        │
│         └──→ Visualization Agent                                │
│                                                                  │
│  Interactive testing with real-time feedback                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    TIME & COST SUMMARY                           │
│                                                                  │
│  Scale │ Setup Time │ Test Time │ Total │ LLM Cost │ Infra Cost│
│  ──────┼────────────┼───────────┼───────┼──────────┼───────────│
│  1GB   │ 6 min      │ 2-5 min   │ 8 min │ $0.50    │ $0        │
│  10GB  │ 20 min     │ 5-10 min  │ 30min │ $2.00    │ $0        │
│  100GB │ 45 min     │ 10-20 min │ 65min │ $5.00    │ $0        │
│                                                                  │
│  Total Infrastructure Cost: $0 (all local!)                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    WHAT YOU VALIDATE                             │
│                                                                  │
│  ✅ SQL Generation: Natural language → correct SQL              │
│  ✅ Large Data: Handles millions to billions of rows            │
│  ✅ Complex Queries: JOINs, aggregations, window functions      │
│  ✅ RAG Effectiveness: Schema understanding improves accuracy   │
│  ✅ Analysis Quality: Meaningful insights from data             │
│  ✅ Visualizations: Appropriate charts generated                │
│  ✅ Performance: Response times within acceptable ranges        │
│  ✅ Reliability: High success rate across query types           │
│  ✅ Scalability: Works at 1GB, 10GB, and 100GB                  │
│                                                                  │
│  = Production Ready! 🚀                                          │
└─────────────────────────────────────────────────────────────────┘
```
