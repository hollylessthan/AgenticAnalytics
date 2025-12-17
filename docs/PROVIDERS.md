# Provider Configuration Guide

This guide explains how to configure Agentic Analytics with different LLM providers and database systems.

## Table of Contents

- [LLM Providers](#llm-providers)
  - [OpenAI](#openai)
  - [Anthropic (Claude)](#anthropic-claude)
  - [Google (Gemini)](#google-gemini)
  - [AWS Bedrock](#aws-bedrock)
  - [Azure OpenAI](#azure-openai)
- [Database Systems](#database-systems)
  - [SQLite](#sqlite)
  - [PostgreSQL](#postgresql)
  - [MySQL](#mysql)
  - [DuckDB](#duckdb)
  - [Snowflake](#snowflake)
  - [Amazon Redshift](#amazon-redshift)
  - [Google BigQuery](#google-bigquery)

---

## LLM Providers

### OpenAI

**Installation:**
```bash
pip install langchain-openai
```

**Configuration (.env):**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-api-key-here
AGENT_MODEL=gpt-4-turbo-preview
# Options: gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo
```

**Usage:**
```python
from utils.llm_factory import get_llm

llm = get_llm(provider="openai", model="gpt-4")
```

---

### Anthropic (Claude)

**Installation:**
```bash
pip install langchain-anthropic
```

**Configuration (.env):**
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
AGENT_MODEL=claude-3-opus-20240229
# Options: claude-3-opus-20240229, claude-3-sonnet-20240229, claude-3-haiku-20240307
```

**Usage:**
```python
from utils.llm_factory import get_llm

llm = get_llm(provider="anthropic", model="claude-3-sonnet-20240229")
```

---

### Google (Gemini)

**Installation:**
```bash
pip install langchain-google-genai
```

**Configuration (.env):**
```bash
LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-api-key-here
AGENT_MODEL=gemini-pro
# Options: gemini-pro, gemini-1.5-pro
```

**Usage:**
```python
from utils.llm_factory import get_llm

llm = get_llm(provider="google", model="gemini-1.5-pro")
```

---

### AWS Bedrock

**Installation:**
```bash
pip install langchain-aws boto3
```

**Configuration (.env):**
```bash
LLM_PROVIDER=bedrock
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AGENT_MODEL=anthropic.claude-3-sonnet-20240229-v1:0
# Options: anthropic.claude-v2, anthropic.claude-3-sonnet-20240229-v1:0, 
#          anthropic.claude-3-haiku-20240307-v1:0
```

**Usage:**
```python
from utils.llm_factory import get_llm

llm = get_llm(provider="bedrock", model="anthropic.claude-3-sonnet-20240229-v1:0")
```

---

### Azure OpenAI

**Installation:**
```bash
pip install langchain-openai
```

**Configuration (.env):**
```bash
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-azure-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AGENT_MODEL=your-deployment-name
# Use your Azure deployment name as the model
```

**Usage:**
```python
from utils.llm_factory import get_llm

llm = get_llm(provider="azure", model="your-deployment-name")
```

---

## Database Systems

### SQLite

**Installation:**
```bash
# Built-in with Python - no additional packages needed
```

**Configuration (.env):**
```bash
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///./data/analytics.db
```

**Usage:**
```python
from utils.database import DatabaseManager

db = DatabaseManager()
```

**Pros:** Easy setup, no server required
**Cons:** Single user, limited scale

---

### PostgreSQL

**Installation:**
```bash
pip install psycopg2-binary
```

**Configuration (.env):**
```bash
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

**Connection String Format:**
```
postgresql://[user[:password]@][host][:port][/database]
```

**Pros:** Full-featured, ACID compliant, great for production
**Cons:** Requires server setup

---

### MySQL

**Installation:**
```bash
pip install pymysql
```

**Configuration (.env):**
```bash
DATABASE_TYPE=mysql
DATABASE_URL=mysql://user:password@localhost:3306/dbname
```

**Connection String Format:**
```
mysql://[user[:password]@][host][:port][/database]
```

**Pros:** Widely used, good documentation
**Cons:** Requires server setup

---

### DuckDB

**Installation:**
```bash
pip install duckdb duckdb-engine
```

**Configuration (.env):**
```bash
DATABASE_TYPE=duckdb
DATABASE_URL=duckdb:///./data/analytics.duckdb
```

**Usage:**
```python
from utils.database import DatabaseManager

db = DatabaseManager(database_type="duckdb")
```

**Pros:** Fast analytical queries, in-process, Parquet support
**Cons:** Newer, smaller ecosystem

---

### Snowflake

**Installation:**
```bash
pip install snowflake-sqlalchemy snowflake-connector-python
```

**Configuration (.env):**
```bash
DATABASE_TYPE=snowflake
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
SNOWFLAKE_DATABASE=your-database
SNOWFLAKE_SCHEMA=your-schema
SNOWFLAKE_WAREHOUSE=your-warehouse
```

**Or use connection URL:**
```bash
DATABASE_URL=snowflake://user:password@account/database/schema?warehouse=warehouse_name
```

**Pros:** Cloud-native, excellent for data warehousing, scalable
**Cons:** Cost, requires cloud setup

---

### Amazon Redshift

**Installation:**
```bash
pip install redshift-connector sqlalchemy-redshift
```

**Configuration (.env):**
```bash
DATABASE_TYPE=redshift
DATABASE_URL=redshift+psycopg2://user:password@cluster.region.redshift.amazonaws.com:5439/dbname
```

**Connection String Format:**
```
redshift+psycopg2://[user[:password]@][host][:port][/database]
```

**Pros:** AWS integration, good for large datasets
**Cons:** Cost, AWS-specific

---

### Google BigQuery

**Installation:**
```bash
pip install sqlalchemy-bigquery
```

**Configuration (.env):**
```bash
DATABASE_TYPE=bigquery
BIGQUERY_PROJECT=your-project-id
BIGQUERY_CREDENTIALS_PATH=/path/to/credentials.json
```

**Setup:**
1. Create a service account in GCP
2. Download credentials JSON
3. Set path in configuration

**Pros:** Serverless, handles massive datasets, pay-per-query
**Cons:** Different SQL dialect, GCP-specific

---

## Switching Providers

You can switch providers at runtime:

```python
# Switch LLM provider
from utils.llm_factory import get_llm

openai_llm = get_llm(provider="openai", model="gpt-4")
claude_llm = get_llm(provider="anthropic", model="claude-3-sonnet-20240229")

# Switch database
from utils.database import DatabaseManager

sqlite_db = DatabaseManager(database_type="sqlite")
postgres_db = DatabaseManager(database_type="postgresql")
```

## Cost Optimization Tips

### LLM Costs
- **Development:** Use `gpt-3.5-turbo` or `claude-3-haiku`
- **Production:** Use `gpt-4-turbo-preview` or `claude-3-sonnet`
- Set appropriate `AGENT_TEMPERATURE` (0.0 for deterministic)

### Database Costs
- **Small projects:** SQLite or DuckDB (free)
- **Medium projects:** PostgreSQL or MySQL (cheap VPS)
- **Large projects:** Snowflake/BigQuery (pay-per-use)

## Troubleshooting

### LLM Issues

**"API key not found"**
- Check `.env` file has correct key variable
- Verify key is valid and has credits

**"Model not found"**
- Check model name matches provider
- Verify you have access to the model

### Database Issues

**"Connection failed"**
- Verify connection string format
- Check credentials and permissions
- Ensure database server is running

**"Module not found"**
- Install required connector: `pip install <connector>`
- Check requirements.txt for correct package

## Support Matrix

| Provider | Status | Models Available |
|----------|--------|------------------|
| OpenAI | ✅ Supported | GPT-4, GPT-3.5 |
| Anthropic | ✅ Supported | Claude 3 (Opus, Sonnet, Haiku) |
| Google | ✅ Supported | Gemini Pro, 1.5 Pro |
| AWS Bedrock | ✅ Supported | Claude via Bedrock |
| Azure OpenAI | ✅ Supported | GPT models |

| Database | Status | Notes |
|----------|--------|-------|
| SQLite | ✅ Supported | Default, no setup |
| PostgreSQL | ✅ Supported | Recommended for production |
| MySQL | ✅ Supported | Widely supported |
| DuckDB | ✅ Supported | Fast analytics |
| Snowflake | ✅ Supported | Enterprise data warehouse |
| Redshift | ✅ Supported | AWS data warehouse |
| BigQuery | ✅ Supported | GCP serverless |

---

**Need help?** Open an issue on [GitHub](https://github.com/hollylessthan/AgenticAnalytics/issues)
