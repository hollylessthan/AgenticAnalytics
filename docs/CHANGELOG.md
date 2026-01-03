# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

#### Profiling Agent
- Outlier detection method updated: Now uses Mean ± 3 * StdDev instead of IQR for numeric columns. After preprocessing, outlier flags are set to `False` and outlier details are cleared in the profile.
- Improved normality/skewness detection and reporting in the data profile.

#### Preprocessing Agent
- Outlier capping recommendations and code generation now use Mean ± 3 * StdDev method.
- RAG-powered method card retrieval for outlier handling, transformation, imputation, encoding, and scaling is now category-specific.
- Improved validation and error-aware retry logic for LLM-generated preprocessing code.
- Fallback hardcoded preprocessing code is now disabled; all code must be LLM-generated.

#### Modeling Agent
- Enhanced model selection: RAG retrieval now filters method cards by problem type (regression/classification).
- Improved logging and error handling for model selection and training.
- System prompt for code generation now clarifies that input DataFrame is fully preprocessed.

#### RAG System & Method Cards
- Added category-specific retrieval methods for outlier handling, transformation, imputation, encoding, and scaling.
- Vector store now indexes and filters by method card category.
- MethodCard schema extended with new categories and problem types.
- Added/updated method cards for outlier capping (Mean ± 3 * StdDev) and encoding (OneHotEncoder, LabelEncoder, OrdinalEncoder).

#### Testing & Utilities
- `load_method_cards.py` now removes existing LanceDB directory before re-indexing for a clean slate.
- Added scripts for telecom dataset generation and RAG documentation (`generate_telecom_rag_doc.py`, `setup_telecom_duckdb.py`).

#### New/Untracked Files
- `method_cards/encoding.yaml`, `method_cards/transformation.yaml`: New method card YAMLs for encoding and transformation/outlier handling.
- `testing/generate_telecom_rag_doc.py`, `testing/setup_telecom_duckdb.py`: Scripts for telecom dataset and documentation.

### Added
#### Knowledge Base Deduplication
- **Duplicate Knowledge Prevention**: Updated `testing/load_method_cards.py` and `testing/load_rag_documents.py` to avoid loading duplicate method cards and RAG documents into the vector store. Deduplication logic ensures only unique knowledge entries are indexed, improving retrieval quality and storage efficiency.
#### Profiling & Workflow Robustness
- **Data Profile Provenance**: Profiling agent now uses a robust `profile_provenance` field, which includes both a hash of the profiled DataFrame and the data source type (e.g., preprocessed, query_results, cached). This ensures that data profiles are only reused when both the data and the source match, preventing stale or mismatched profiles.
- **Automatic Re-Profiling After Preprocessing**: The orchestrator and profiling agent now guarantee that after any preprocessing step, the data is always re-profiled before modeling, ensuring modeling agents always receive a fresh, post-preprocessing profile.
- **Multiple Data Source Handling**: Provenance logic now supports multiple cached DataFrames and distinguishes between them, preventing accidental profile reuse across different data sources.
- **Workflow Graph & Routing Fixes**: Improved the orchestrator's workflow graph and routing logic to support correct transitions between profiling, preprocessing, and modeling agents, and to prevent infinite loops or dead-ends in the workflow.
- **Method Knowledge Base**: Curated knowledge base of 40+ statistical tests, ML algorithms, preprocessing techniques, and evaluation metrics
  - Created structured method card system with MethodCard schema and DataConditions for constraint-based retrieval
  - Added YAML method card definitions for imputation (SimpleImputer mean/median/mode), scaling (StandardScaler, MinMaxScaler, RobustScaler), normality tests (Shapiro-Wilk, Anderson-Darling, Kolmogorov-Smirnov), and regression models (OLS, Ridge, Lasso, Elastic Net, GLS)
  - Implemented LanceDB vector store integration for semantic method card search
  - Added `load_method_cards.py` to index method cards into LanceDB
  - Added `test_method_card_retrieval.py` with comprehensive test scenarios (basic retrieval, constraint-based filtering, regression methods, ANOVA tests, evaluation metrics)
- **Profiling Agent**: Comprehensive data quality assessment agent (read-only analysis)
  - Generates data profiles with missing values, outliers, normality tests, correlations, and distribution analysis
  - RAG-powered statistical test suggestions based on data characteristics
  - Caches data profiles for reuse across preprocessing and modeling workflows
- **Preprocessing Agent**: RAG-guided data transformation agent with human-in-the-loop confirmation
  - Uses RAG to select appropriate transformations (imputation, encoding, scaling) based on data profile
  - Three modes: Confirm (pause for user approval), Auto (apply all), Manual (skip unless requested)
  - Error-aware retry mechanism (3 attempts) to fix code generation errors automatically
  - Preprocessing confirmation dialog with data preview table showing top 5 rows
  - Generates preprocessing recommendations with impact assessment and priority ranking
- **Modeling Agent**: Intelligent ML model selection and training with error-aware retry
  - RAG-powered model selection based on problem type (classification/regression) and data characteristics
  - Automatic intent detection (identifies target variable, problem type, feature columns)
  - Error-aware code generation with automatic retry (fixes f-string errors, OneHotEncoder API issues, categorical encoding problems)
  - Generates formatted model summary output (like statsmodels/sklearn summary) with metrics, feature importance, and interpretation guides
  - Cross-validation and comprehensive evaluation metrics
- **Documentation Updates**:
  - Updated QUICKSTART.md with method card loading instructions for both sample data and production setup
  - Added comprehensive "Method Knowledge Base" section to ARCHITECTURE.md with coverage lists, retrieval workflow, and agent integration details
  - Updated README.md to consolidate method card mentions and remove awkward standalone section
  - Integrated preprocessing/modeling/profiling agents into framework description

### Fixed
- **Cached Data Workflow**: Fixed visualization, analysis, and communication agents to properly access cached data from previous queries
  - Added missing `visualization_agent` and `analysis_agent` to classifier's conditional edges in orchestrator
  - Implemented cached_dataframe fallback logic in all data-consuming agents to handle LangGraph state persistence limitation
  - Added missing `import pandas as pd` in sql_agent.py
  - Updated error display in UI to show actual exception messages instead of hardcoded generic errors
- **Graph Routing**: Resolved `KeyError: 'visualization_agent'` by enabling direct routing from classifier to visualization and analysis agents
- **Preprocessing Data Inheritance**: Fixed logic to only reuse preprocessed data for modeling follow-ups, not unrelated queries
- **State Error Handling**: Fixed `state.error` vs `state.errors` bug in orchestrator (line 556)
- **UI State Management**: Removed "I couldn't process your request" message when preprocessing confirmation is pending

### Changed
- **Error-Aware Retry**: Extended to preprocessing and modeling agents (previously only SQL, analysis, visualization)
  - Preprocessing Agent: Regenerates code based on f-string errors, column mismatches, type errors
  - Modeling Agent: Regenerates code for categorical encoding issues, API compatibility errors, stratification errors
  - Maximum 3 retry attempts per agent with progressive error feedback to LLM
- **Method Card Integration**: RAG system now supports specialized retrieval methods:
  - `retrieve_methods_for_preprocessing()` - filters by preprocessing categories
  - `retrieve_methods_for_modeling()` - filters by model categories
  - `retrieve_methods_for_statistics()` - filters by statistical test categories
- **Data Profile Reuse**: Profiling Agent caches data profiles to avoid redundant analysis across agents
- **Human-in-the-Loop Enhancements**: Preprocessing confirmation includes data preview and reuse detection for existing preprocessed data

### Removed
- **Obsolete Files**: Removed `testing/scrape_ml_docs.py`, `testing/evaluate_rag.py`, `docs/RAG_ENHANCEMENTS.md`, `docs/RAG_INTEGRATION_SUMMARY.md`
- **Documentation Consolidation**: Merged RAG documentation into single comprehensive `RAG_SYSTEM.md`

### Added (Previous Updates)
- **Inline Code Display**: Added expandable sections in UI to display generated SQL queries, analysis code, and visualization code
- **Google Vertex AI Vector Search**: Managed vector search service for GCP with support for 1M+ documents
- **AWS Vector Store Implementations**: Added Kendra, Aurora pgvector, and DynamoDB vector store support for AWS-native deployments
- **AWS Kendra Integration**: Enterprise document retrieval with ML-powered relevance scoring and batch document operations
- **Aurora pgvector Support**: PostgreSQL with native vector extensions, connection pooling, and HNSW/IVFFlat indexing
- **DynamoDB Vector Store**: Serverless vector storage with in-memory cosine similarity scoring
- **AWS Integration Examples**: Comprehensive `aws_vector_stores_example.py` with setup guides for OpenSearch, Kendra, Aurora, and DynamoDB
- **Automated RAG Document Generation**: `generate_join_best_practices()` function for automatic JOIN pattern documentation
- **JOIN Best Practices Documentation**: Comprehensive guide on schema relationships and JOIN patterns with SQL examples
- **Data Format Conversions Documentation**: Automatic generation of data type conversion guides with real database values
- **Flexible Framework Branding**: Clear distinction between Agentic Analytics (core framework) and Data Copilot (reference UI)
- **Comprehensive Customization Guide**: QUICKSTART.md with examples for PostgreSQL, MySQL, DuckDB, Snowflake, BigQuery, Redshift, and SQLite
- **Multi-LLM Support Documentation**: Examples and setup guides for OpenAI, Anthropic Claude, Google Gemini, AWS Bedrock, and local Ollama
- **Vector Store Options Documentation**: Configuration examples for FAISS, Weaviate, Pinecone, Chroma, OpenSearch, Kendra, Aurora pgvector, DynamoDB, Azure Cognitive Search, and Vertex AI Vector Search
- **Architecture Documentation**: Detailed ARCHITECTURE.md with system design, agent orchestration, routing, RAG, security, and extensibility
- **Error-Aware Retry Mechanism**: Intelligent retry logic for SQL Agent, Analysis Agent, and Visualization Agent with LLM-based error recovery

### Changed
- **README Structure**: Reorganized to emphasize framework flexibility and customization capabilities
- **Project Identity**: Positioned Agentic Analytics as a flexible core framework rather than a monolithic application
- **Vector Store Factory**: Enhanced factory pattern to support AWS native services (Kendra, Aurora pgvector, DynamoDB) and GCP Vertex AI Vector Search
- **Configuration System**: Extended config.py to include AWS and GCP-specific credentials and endpoints
- **RAG Document Generation**: Extended `generate_rag_documents.py` to auto-generate both data_format_conversions.md and join_best_practices.md
- **Author Metadata**: Updated setup.py with project author information
- **Documentation Format**: Removed emojis from documentation files for better compatibility and consistency

### Improved
- **Database Support Documentation**: Now explicitly lists 8 supported databases with connection examples
- **LLM Provider Flexibility**: Documented all supported LLM providers with configuration examples
- **Vector Store Flexibility**: Multiple vector store options documented with setup instructions (now 10 supported providers)
- **AWS Service Integration**: Complete support for AWS ecosystem with Bedrock, OpenSearch, Kendra, Aurora, and DynamoDB
- **Azure Service Integration**: Full support for Azure ecosystem with Azure Cognitive Search and Azure OpenAI
- **GCP Service Integration**: Full support for Google Cloud with Vertex AI embeddings and Vertex AI Vector Search
- **User Customization Path**: Clear guidance on using Agentic Analytics with any database without code changes
- **Cost Optimization**: Guidance on selecting appropriate vector stores based on scale and budget

## [0.1.0] - 2025-12-15

### Added
- Initial release of Agentic Analytics
- Multi-agent architecture with LangGraph orchestration
- SQL Agent for natural language to SQL conversion
- Analysis Agent for Python-based data analysis
- Visualization Agent for automated chart generation
- RAG system with FAISS and Weaviate support
- Streamlit web interface (Data Copilot reference UI)
- Database utilities with SQLAlchemy
- Support for PostgreSQL, MySQL, SQLite, DuckDB, Snowflake, BigQuery, Redshift, and Athena
- Hybrid routing system (3-tier query classification)
- Result caching with concurrent access
- Stateful conversation with 10-turn history and rollback
- Streaming transparency with real-time agent reasoning
- Example scripts and sample database generator
- Comprehensive test suite
- Documentation and README

### Features
- Natural language query processing
- Automated SQL generation with schema awareness
- Statistical analysis capabilities
- Automatic visualization creation
- Context-aware responses with RAG
- Interactive chat interface
- Multi-database support
- SQL injection prevention and security enforcement
- Query result row limiting

### Developer Tools
- Configuration management
- Extensible agent framework
- Vector store abstraction
- Helper utilities
- Example implementations

[0.1.0]: https://github.com/hollylessthan/AgenticAnalytics/releases/tag/v0.1.0
