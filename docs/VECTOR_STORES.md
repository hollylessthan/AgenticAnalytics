# Vector Store & Embedding Configuration Guide

Complete guide for configuring vector stores and embedding models in Agentic Analytics.

## Table of Contents

- [Embedding Models](#embedding-models)
- [Vector Stores](#vector-stores)
- [Configuration Examples](#configuration-examples)
- [Cost Comparison](#cost-comparison)
- [Performance Benchmarks](#performance-benchmarks)

---

## Embedding Models

### Overview

Embedding models convert text into numerical vectors for semantic search. Choose based on:
- **Cost**: Free (local) vs paid (API)
- **Quality**: Accuracy of semantic understanding
- **Speed**: Latency and throughput
- **Language**: Multilingual support

### Supported Providers

#### 1. OpenAI Embeddings

**Best for:** Production applications, high quality

**Installation:**
```bash
pip install langchain-openai
```

**Configuration (.env):**
```bash
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-ada-002
OPENAI_API_KEY=sk-your-key
```

**Models:**
- `text-embedding-ada-002` - Most cost-effective, good quality
- `text-embedding-3-small` - Faster, cheaper
- `text-embedding-3-large` - Highest quality

**Pros:** High quality, reliable, easy to use
**Cons:** Paid API, requires internet

---

#### 2. HuggingFace Embeddings

**Best for:** Development, local deployment, cost-sensitive

**Installation:**
```bash
pip install langchain-huggingface sentence-transformers
```

**Configuration (.env):**
```bash
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

**Popular Models:**
- `sentence-transformers/all-MiniLM-L6-v2` - Fast, lightweight
- `sentence-transformers/all-mpnet-base-v2` - Better quality
- `BAAI/bge-large-en` - State-of-the-art
- `BAAI/bge-m3` - Multilingual

**Pros:** Free, runs locally, no API calls
**Cons:** Slower on CPU, requires model download

---

#### 3. Cohere Embeddings

**Best for:** Multilingual applications, enterprise

**Installation:**
```bash
pip install langchain-cohere
```

**Configuration (.env):**
```bash
EMBEDDING_PROVIDER=cohere
EMBEDDING_MODEL=embed-english-v3.0
COHERE_API_KEY=your-cohere-key
```

**Models:**
- `embed-english-v3.0` - English optimized
- `embed-multilingual-v3.0` - 100+ languages
- `embed-english-light-v3.0` - Faster, cheaper

**Pros:** Excellent multilingual, competitive pricing
**Cons:** Paid API

---

#### 4. AWS Bedrock Embeddings

**Best for:** AWS infrastructure, enterprise

**Installation:**
```bash
pip install langchain-aws boto3
```

**Configuration (.env):**
```bash
EMBEDDING_PROVIDER=bedrock
EMBEDDING_MODEL=amazon.titan-embed-text-v1
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

**Models:**
- `amazon.titan-embed-text-v1` - AWS native
- `cohere.embed-english-v3` - Cohere via Bedrock
- `cohere.embed-multilingual-v3` - Multilingual

**Pros:** AWS integration, no egress fees
**Cons:** AWS-specific, setup complexity

---

#### 5. Vertex AI Embeddings

**Best for:** Google Cloud infrastructure

**Installation:**
```bash
pip install langchain-google-vertexai
```

**Configuration (.env):**
```bash
EMBEDDING_PROVIDER=vertex_ai
EMBEDDING_MODEL=textembedding-gecko
GOOGLE_API_KEY=your-key
```

**Models:**
- `textembedding-gecko` - General purpose
- `textembedding-gecko-multilingual` - Multilingual

**Pros:** GCP integration, good quality
**Cons:** GCP-specific

---

## Vector Stores

### Overview

Vector stores enable fast similarity search over embeddings. Choose based on:
- **Scale**: Number of documents
- **Infrastructure**: Local vs cloud
- **Features**: Filtering, hybrid search
- **Cost**: Self-hosted vs managed

### Supported Vector Stores

#### 1. FAISS (Default)

**Best for:** Development, prototyping, small datasets

**Installation:**
```bash
pip install faiss-cpu
```

**Configuration (.env):**
```bash
VECTOR_STORE_TYPE=faiss
```

**Features:**
- ✅ Free and open source
- ✅ Fast similarity search
- ✅ Works offline
- ✅ Easy setup
- ❌ In-memory only
- ❌ No built-in filtering
- ❌ Single machine

**Usage:**
```python
from rag.vector_store import get_vector_store

vector_store = get_vector_store(vector_store_type="faiss")
```

---

#### 2. Chroma

**Best for:** Local development, small to medium datasets

**Installation:**
```bash
pip install chromadb langchain-chroma
```

**Configuration (.env):**
```bash
VECTOR_STORE_TYPE=chroma
CHROMA_HOST=localhost  # Optional for remote
CHROMA_PORT=8000
```

**Features:**
- ✅ Free and open source
- ✅ Persistent storage
- ✅ Metadata filtering
- ✅ Easy to use
- ✅ Can run remotely
- ❌ Limited scale

**Usage:**
```python
vector_store = get_vector_store(vector_store_type="chroma")
```

---

#### 3. Pinecone

**Best for:** Production, large scale, serverless

**Installation:**
```bash
pip install pinecone-client langchain-pinecone
```

**Configuration (.env):**
```bash
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=analytics
```

**Features:**
- ✅ Fully managed
- ✅ Highly scalable
- ✅ Low latency
- ✅ Metadata filtering
- ✅ Hybrid search
- ❌ Paid service
- ❌ Vendor lock-in

**Usage:**
```python
vector_store = get_vector_store(vector_store_type="pinecone")
```

---

#### 4. Weaviate

**Best for:** Production, self-hosted or cloud, GraphQL API

**Installation:**
```bash
pip install weaviate-client
```

**Configuration (.env):**
```bash
VECTOR_STORE_TYPE=weaviate
WEAVIATE_URL=http://localhost:8080
WEAVIATE_API_KEY=your-api-key  # Optional
```

**Features:**
- ✅ Open source
- ✅ Self-hosted or cloud
- ✅ GraphQL API
- ✅ Hybrid search
- ✅ Multi-tenancy
- ❌ More complex setup

**Docker Setup:**
```bash
docker run -p 8080:8080 semitechnologies/weaviate:latest
```

---

#### 5. OpenSearch

**Best for:** AWS infrastructure, large scale

**Installation:**
```bash
pip install opensearch-py
```

**Configuration (.env):**
```bash
VECTOR_STORE_TYPE=opensearch
OPENSEARCH_URL=https://your-domain.region.es.amazonaws.com
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=your-password
```

**Features:**
- ✅ Open source
- ✅ Highly scalable
- ✅ Full-text + vector search
- ✅ AWS managed option
- ✅ Advanced analytics
- ❌ Complex setup
- ❌ Higher resource usage

---

#### 6. Azure Cognitive Search

**Best for:** Azure infrastructure, enterprise

**Installation:**
```bash
pip install azure-search-documents
```

**Configuration (.env):**
```bash
VECTOR_STORE_TYPE=azure_search
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
AZURE_SEARCH_KEY=your-key
AZURE_SEARCH_INDEX_NAME=analytics-index
```

**Features:**
- ✅ Fully managed
- ✅ Azure integration
- ✅ Hybrid search
- ✅ AI enrichment
- ✅ Enterprise features
- ❌ Azure-specific
- ❌ Can be expensive

---

## Configuration Examples

### Local Development (Free)

```bash
# .env
EMBEDDING_PROVIDER=huggingface
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
VECTOR_STORE_TYPE=faiss
```

**Pros:** Completely free, works offline
**Cons:** Slower, limited scale

---

### Production (Cost-Effective)

```bash
# .env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
VECTOR_STORE_TYPE=chroma
```

**Pros:** Good quality, reasonable cost, persistent
**Cons:** Limited scale

---

### Production (Scalable)

```bash
# .env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=your-key
PINECONE_ENVIRONMENT=us-west1-gcp
```

**Pros:** Fully managed, highly scalable
**Cons:** Higher cost

---

### Enterprise (AWS)

```bash
# .env
EMBEDDING_PROVIDER=bedrock
EMBEDDING_MODEL=amazon.titan-embed-text-v1
VECTOR_STORE_TYPE=opensearch
OPENSEARCH_URL=https://your-domain.region.es.amazonaws.com
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
```

**Pros:** Full AWS integration, scalable
**Cons:** AWS-specific, complex

---

### Enterprise (Azure)

```bash
# .env
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-ada-002
VECTOR_STORE_TYPE=azure_search
AZURE_SEARCH_ENDPOINT=https://your-service.search.windows.net
AZURE_SEARCH_KEY=your-key
```

**Pros:** Azure integration, enterprise features
**Cons:** Azure-specific, cost

---

## Cost Comparison

### Embedding Models (per 1M tokens)

| Provider | Model | Cost | Quality |
|----------|-------|------|---------|
| HuggingFace | all-MiniLM-L6-v2 | Free | Good |
| OpenAI | text-embedding-3-small | $0.02 | Good |
| OpenAI | text-embedding-ada-002 | $0.10 | Very Good |
| OpenAI | text-embedding-3-large | $0.13 | Excellent |
| Cohere | embed-english-light-v3.0 | $0.10 | Good |
| Cohere | embed-english-v3.0 | $0.10 | Very Good |
| AWS Bedrock | amazon.titan-embed | $0.10 | Good |

### Vector Stores (monthly, ~100K docs)

| Provider | Type | Cost Estimate |
|----------|------|---------------|
| FAISS | Self-hosted | Free (compute only) |
| Chroma | Self-hosted | Free (compute only) |
| Weaviate | Self-hosted | Free (compute only) |
| Weaviate | Cloud | ~$25-100/month |
| Pinecone | Managed | ~$70/month |
| OpenSearch | AWS Managed | ~$100-200/month |
| Azure Search | Managed | ~$75-250/month |

---

## Performance Benchmarks

### Embedding Speed (docs/second)

| Provider | Speed | Hardware |
|----------|-------|----------|
| HuggingFace (CPU) | ~50 | 8-core CPU |
| HuggingFace (GPU) | ~500 | T4 GPU |
| OpenAI API | ~1000 | Cloud API |
| Cohere API | ~800 | Cloud API |

### Search Latency (p95)

| Vector Store | Latency | Scale |
|--------------|---------|-------|
| FAISS | <10ms | 100K docs |
| Chroma | <20ms | 100K docs |
| Pinecone | <50ms | 10M+ docs |
| Weaviate | <30ms | 1M+ docs |
| OpenSearch | <100ms | 10M+ docs |

---

## Recommendations

### By Use Case

**Personal Project / Learning:**
- Embedding: HuggingFace (free)
- Vector Store: FAISS (free)

**Startup / MVP:**
- Embedding: OpenAI text-embedding-3-small ($)
- Vector Store: Chroma (free)

**Growing Business:**
- Embedding: OpenAI text-embedding-ada-002 ($$)
- Vector Store: Pinecone or Weaviate Cloud ($$$)

**Enterprise:**
- Embedding: Cohere or Bedrock ($$)
- Vector Store: OpenSearch or Azure Search ($$$)

### By Scale

**< 10K documents:**
- FAISS or Chroma with any embeddings

**10K - 100K documents:**
- Chroma or Weaviate with OpenAI/Cohere

**100K - 1M documents:**
- Pinecone or Weaviate with OpenAI/Cohere

**1M+ documents:**
- Pinecone, OpenSearch, or Azure Search with Cohere/Bedrock

---

## Troubleshooting

### Embedding Issues

**"API key not found"**
- Check `.env` file has correct key variable
- Verify key is valid

**"Model not found"**
- Check model name is correct for provider
- Some models require special access

**"Out of memory"**
- Reduce batch size
- Use smaller model
- Use API-based embeddings

### Vector Store Issues

**"Connection failed"**
- Check service is running
- Verify credentials
- Check network/firewall

**"Index not found"**
- Create index first
- Check index name matches config

**"Slow search"**
- Reduce number of documents
- Use better hardware
- Consider managed service

---

**Need help?** Open an issue on [GitHub](https://github.com/hollylessthan/AgenticAnalytics/issues)
