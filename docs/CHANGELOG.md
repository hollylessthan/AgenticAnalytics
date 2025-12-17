# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Automated RAG Document Generation**: `generate_join_best_practices()` function for automatic JOIN pattern documentation
- **JOIN Best Practices Documentation**: Comprehensive guide on schema relationships and JOIN patterns with SQL examples
- **Data Format Conversions Documentation**: Automatic generation of data type conversion guides with real database values
- **Flexible Framework Branding**: Clear distinction between Agentic Analytics (core framework) and Data Copilot (reference UI)
- **Comprehensive Customization Guide**: QUICKSTART.md with examples for PostgreSQL, MySQL, DuckDB, Snowflake, BigQuery, Redshift, and SQLite
- **Multi-LLM Support Documentation**: Examples and setup guides for OpenAI, Anthropic Claude, Google Gemini, AWS Bedrock, and local Ollama
- **Vector Store Options Documentation**: Configuration examples for FAISS, Weaviate, Pinecone, Chroma, and Milvus
- **Architecture Documentation**: Detailed ARCHITECTURE.md with system design, agent orchestration, routing, RAG, security, and extensibility

### Changed
- **README Structure**: Reorganized to emphasize framework flexibility and customization capabilities
- **Project Identity**: Positioned Agentic Analytics as a flexible core framework rather than a monolithic application
- **RAG Document Generation**: Extended `generate_rag_documents.py` to auto-generate both data_format_conversions.md and join_best_practices.md
- **Author Metadata**: Updated setup.py with project author information

### Improved
- **Database Support Documentation**: Now explicitly lists 8 supported databases with connection examples
- **LLM Provider Flexibility**: Documented all supported LLM providers with configuration examples
- **Vector Store Flexibility**: Multiple vector store options documented with setup instructions
- **User Customization Path**: Clear guidance on using Agentic Analytics with any database without code changes

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
