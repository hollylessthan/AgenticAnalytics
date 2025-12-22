"""Vector store implementations for RAG."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from ..config import config
from ..utils.embedding_factory import get_embeddings


class VectorStoreBase(ABC):
    """Base class for vector stores."""
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to the vector store."""
        pass
    
    @abstractmethod
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    def save(self, path: str) -> None:
        """Save the vector store."""
        pass
    
    @abstractmethod
    def load(self, path: str) -> None:
        """Load the vector store."""
        pass


class FAISSVectorStore(VectorStoreBase):
    """FAISS-based vector store implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize FAISS vector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        from langchain_community.vectorstores import FAISS
        
        self.embeddings = embeddings or get_embeddings()
        self.vectorstore: Optional[FAISS] = None
        self._faiss_module = FAISS
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to FAISS index.
        
        Args:
            documents: List of documents to add
        """
        if self.vectorstore is None:
            self.vectorstore = self._faiss_module.from_documents(documents, self.embeddings)
        else:
            self.vectorstore.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        if self.vectorstore is None:
            return []
        
        return self.vectorstore.similarity_search(query, k=k)
    
    def save(self, path: str = "faiss_index") -> None:
        """Save FAISS index to disk.
        
        Args:
            path: Directory path to save index
        """
        if self.vectorstore is not None:
            self.vectorstore.save_local(path)
    
    def load(self, path: str = "faiss_index") -> None:
        """Load FAISS index from disk.
        
        Args:
            path: Directory path to load index from
        """
        try:
            self.vectorstore = self._faiss_module.load_local(
                path, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
        except Exception as e:
            print(f"Could not load FAISS index: {e}")
            self.vectorstore = None


class WeaviateVectorStore(VectorStoreBase):
    """Weaviate-based vector store implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize Weaviate vector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        import weaviate
        from langchain_community.vectorstores import Weaviate
        
        self.embeddings = embeddings or get_embeddings()
        
        # Initialize Weaviate client
        auth_config = None
        if config.weaviate_api_key:
            auth_config = weaviate.AuthApiKey(api_key=config.weaviate_api_key)
        
        self.client = weaviate.Client(
            url=config.weaviate_url or "http://localhost:8080",
            auth_client_secret=auth_config
        )
        
        self.index_name = "AnalyticsDocuments"
        self._ensure_schema()
    
    def _ensure_schema(self) -> None:
        """Ensure Weaviate schema exists."""
        try:
            self.client.schema.get(self.index_name)
        except:
            schema = {
                "class": self.index_name,
                "description": "Documents for analytics RAG",
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                        "description": "Document content",
                    },
                    {
                        "name": "metadata",
                        "dataType": ["text"],
                        "description": "Document metadata as JSON string",
                    }
                ]
            }
            self.client.schema.create_class(schema)
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Weaviate.
        
        Args:
            documents: List of documents to add
        """
        vectorstore = Weaviate(
            client=self.client,
            index_name=self.index_name,
            text_key="content",
            embedding=self.embeddings
        )
        vectorstore.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        from langchain_community.vectorstores import Weaviate
        
        vectorstore = Weaviate(
            client=self.client,
            index_name=self.index_name,
            text_key="content",
            embedding=self.embeddings
        )
        return vectorstore.similarity_search(query, k=k)
    
    def save(self, path: str = None) -> None:
        """Weaviate persists data automatically."""
        pass
    
    def load(self, path: str = None) -> None:
        """Weaviate loads data automatically."""
        pass


class OpenSearchVectorStore(VectorStoreBase):
    """OpenSearch-based vector store implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize OpenSearch vector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        from langchain_community.vectorstores import OpenSearchVectorSearch
        
        self.embeddings = embeddings or get_embeddings()
        
        if not config.opensearch_url:
            raise ValueError("OPENSEARCH_URL not set in configuration")
        
        # Initialize OpenSearch connection
        opensearch_params = {
            "opensearch_url": config.opensearch_url,
            "index_name": "analytics_docs",
            "embedding_function": self.embeddings
        }
        
        if config.opensearch_username and config.opensearch_password:
            opensearch_params["http_auth"] = (
                config.opensearch_username,
                config.opensearch_password
            )
        
        self.vectorstore = None
        self.opensearch_params = opensearch_params
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to OpenSearch index."""
        from langchain_community.vectorstores import OpenSearchVectorSearch
        
        if self.vectorstore is None:
            self.vectorstore = OpenSearchVectorSearch.from_documents(
                documents,
                self.embeddings,
                **self.opensearch_params
            )
        else:
            self.vectorstore.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents."""
        if self.vectorstore is None:
            return []
        return self.vectorstore.similarity_search(query, k=k)
    
    def save(self, path: str = None) -> None:
        """OpenSearch persists data automatically."""
        pass
    
    def load(self, path: str = None) -> None:
        """OpenSearch loads data automatically."""
        pass


class PineconeVectorStore(VectorStoreBase):
    """Pinecone-based vector store implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize Pinecone vector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        from langchain_pinecone import PineconeVectorStore as PineconeVS
        import pinecone
        
        self.embeddings = embeddings or get_embeddings()
        
        if not config.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY not set in configuration")
        
        # Initialize Pinecone
        pinecone.init(
            api_key=config.pinecone_api_key,
            environment=config.pinecone_environment or "us-west1-gcp"
        )
        
        self.index_name = config.pinecone_index_name or "analytics"
        self.vectorstore = None
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Pinecone index."""
        from langchain_pinecone import PineconeVectorStore as PineconeVS
        
        if self.vectorstore is None:
            self.vectorstore = PineconeVS.from_documents(
                documents,
                self.embeddings,
                index_name=self.index_name
            )
        else:
            self.vectorstore.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents."""
        if self.vectorstore is None:
            return []
        return self.vectorstore.similarity_search(query, k=k)
    
    def save(self, path: str = None) -> None:
        """Pinecone persists data automatically."""
        pass
    
    def load(self, path: str = None) -> None:
        """Pinecone loads data automatically."""
        pass


class ChromaVectorStore(VectorStoreBase):
    """Chroma-based vector store implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize Chroma vector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        from langchain_chroma import Chroma
        
        self.embeddings = embeddings or get_embeddings()
        
        # Configure Chroma client
        client_settings = None
        if config.chroma_host:
            import chromadb
            client_settings = chromadb.config.Settings(
                chroma_api_impl="rest",
                chroma_server_host=config.chroma_host,
                chroma_server_http_port=config.chroma_port
            )
        
        self.vectorstore = None
        self.client_settings = client_settings
        self.collection_name = "analytics_docs"
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Chroma collection."""
        from langchain_chroma import Chroma
        
        if self.vectorstore is None:
            self.vectorstore = Chroma.from_documents(
                documents,
                self.embeddings,
                collection_name=self.collection_name,
                client_settings=self.client_settings
            )
        else:
            self.vectorstore.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents."""
        if self.vectorstore is None:
            return []
        return self.vectorstore.similarity_search(query, k=k)
    
    def save(self, path: str = "chroma_db") -> None:
        """Chroma persists data automatically to disk."""
        pass
    
    def load(self, path: str = "chroma_db") -> None:
        """Chroma loads data automatically from disk."""
        from langchain_chroma import Chroma
        
        try:
            self.vectorstore = Chroma(
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
                persist_directory=path
            )
        except Exception as e:
            print(f"Could not load Chroma collection: {e}")
            self.vectorstore = None


class AzureSearchVectorStore(VectorStoreBase):
    """Azure Cognitive Search vector store implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize Azure Search vector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        from langchain_community.vectorstores.azuresearch import AzureSearch
        
        self.embeddings = embeddings or get_embeddings()
        
        if not config.azure_search_endpoint or not config.azure_search_key:
            raise ValueError("Azure Search credentials not set in configuration")
        
        self.vectorstore = AzureSearch(
            azure_search_endpoint=config.azure_search_endpoint,
            azure_search_key=config.azure_search_key,
            index_name=config.azure_search_index_name or "analytics-index",
            embedding_function=self.embeddings.embed_query
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Azure Search index."""
        self.vectorstore.add_documents(documents)
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents."""
        return self.vectorstore.similarity_search(query, k=k)
    
    def save(self, path: str = None) -> None:
        """Azure Search persists data automatically."""
        pass
    
    def load(self, path: str = None) -> None:
        """Azure Search loads data automatically."""
        pass


class KendraVectorStore(VectorStoreBase):
    """AWS Kendra-based vector store implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize AWS Kendra vector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        import boto3
        
        self.embeddings = embeddings or get_embeddings()
        
        if not config.kendra_index_id:
            raise ValueError("KENDRA_INDEX_ID not set in configuration")
        
        # Initialize Kendra client with AWS region
        self.kendra_client = boto3.client(
            'kendra',
            region_name=config.aws_region or 'us-east-1'
        )
        self.index_id = config.kendra_index_id
        self.document_ids = {}  # Track document IDs for management
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Kendra index.
        
        Args:
            documents: List of documents to add
        """
        batch_documents = []
        
        for idx, doc in enumerate(documents):
            doc_id = str(idx)
            self.document_ids[doc.metadata.get('source', f'doc_{idx}')] = doc_id
            
            batch_documents.append({
                'Id': doc_id,
                'Title': doc.metadata.get('source', f'Document {idx}'),
                'Blob': doc.page_content.encode('utf-8'),
                'ContentType': 'PLAIN_TEXT',
                'Attributes': {
                    '_source': doc.metadata.get('source', ''),
                }
            })
        
        # Batch upload documents to Kendra
        if batch_documents:
            self.kendra_client.batch_put_document(
                IndexId=self.index_id,
                Documents=batch_documents
            )
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents using Kendra Query API.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        try:
            response = self.kendra_client.query(
                IndexId=self.index_id,
                QueryText=query,
                PageSize=k,
                QueryResultTypeFilter='DOCUMENT'
            )
            
            documents = []
            for result in response.get('ResultItems', []):
                doc = Document(
                    page_content=result.get('DocumentExcerpt', {}).get('Text', ''),
                    metadata={
                        'source': result.get('DocumentTitle', ''),
                        'score': result.get('ScoreAttributes', {}).get('ScoreConfidence', 'VERY_HIGH'),
                        'document_id': result.get('DocumentId', '')
                    }
                )
                documents.append(doc)
            
            return documents
        except Exception as e:
            print(f"Kendra query error: {e}")
            return []
    
    def save(self, path: str = None) -> None:
        """Kendra persists data automatically."""
        pass
    
    def load(self, path: str = None) -> None:
        """Kendra loads data automatically."""
        pass


class AuroraPgvectorStore(VectorStoreBase):
    """Aurora PostgreSQL with pgvector extension vector store implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize Aurora pgvector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        import psycopg2
        from psycopg2 import pool
        
        self.embeddings = embeddings or get_embeddings()
        
        # Validate configuration
        if not config.aurora_host or not config.aurora_user or not config.aurora_password:
            raise ValueError("Aurora credentials not set: AURORA_HOST, AURORA_USER, AURORA_PASSWORD required")
        
        # Create connection pool for efficient resource management
        self.connection_pool = pool.SimpleConnectionPool(
            1, 5,
            host=config.aurora_host,
            port=config.aurora_port or 5432,
            database=config.aurora_db_name or 'analytics',
            user=config.aurora_user,
            password=config.aurora_password
        )
        
        self.table_name = 'documents'
        self._create_table()
    
    def _create_table(self):
        """Create documents table with pgvector support."""
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                
                # Create documents table with vector column
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.table_name} (
                        id SERIAL PRIMARY KEY,
                        source TEXT,
                        content TEXT NOT NULL,
                        embedding vector(1536),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create index for faster similarity search
                cur.execute(f"""
                    CREATE INDEX IF NOT EXISTS {self.table_name}_embedding_idx 
                    ON {self.table_name} USING ivfflat (embedding vector_cosine_ops)
                """)
                
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error creating table: {e}")
        finally:
            self.connection_pool.putconn(conn)
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Aurora pgvector.
        
        Args:
            documents: List of documents to add
        """
        conn = self.connection_pool.getconn()
        try:
            with conn.cursor() as cur:
                for doc in documents:
                    # Generate embedding
                    embedding = self.embeddings.embed_query(doc.page_content)
                    
                    cur.execute(
                        f"INSERT INTO {self.table_name} (source, content, embedding) VALUES (%s, %s, %s)",
                        (
                            doc.metadata.get('source', ''),
                            doc.page_content,
                            str(embedding)  # pgvector format
                        )
                    )
                
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Error adding documents: {e}")
        finally:
            self.connection_pool.putconn(conn)
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents using pgvector similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        conn = self.connection_pool.getconn()
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            with conn.cursor() as cur:
                # Query using cosine similarity
                cur.execute(
                    f"""
                    SELECT source, content, 1 - (embedding <=> %s) as similarity
                    FROM {self.table_name}
                    ORDER BY embedding <=> %s
                    LIMIT %s
                    """,
                    (str(query_embedding), str(query_embedding), k)
                )
                
                documents = []
                for row in cur.fetchall():
                    doc = Document(
                        page_content=row[1],
                        metadata={
                            'source': row[0],
                            'similarity_score': float(row[2])
                        }
                    )
                    documents.append(doc)
                
                return documents
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
        finally:
            self.connection_pool.putconn(conn)
    
    def save(self, path: str = None) -> None:
        """Aurora persists data automatically."""
        pass
    
    def load(self, path: str = None) -> None:
        """Aurora loads data automatically."""
        pass


class DynamoDBVectorStore(VectorStoreBase):
    """AWS DynamoDB vector store implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize DynamoDB vector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        import boto3
        
        self.embeddings = embeddings or get_embeddings()
        
        if not config.dynamodb_table_name:
            raise ValueError("DYNAMODB_TABLE_NAME not set in configuration")
        
        # Initialize DynamoDB resource
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=config.aws_region or 'us-east-1'
        )
        
        self.table_name = config.dynamodb_table_name
        self.table = self.dynamodb.Table(self.table_name)
        self.document_count = 0
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to DynamoDB.
        
        Args:
            documents: List of documents to add
        """
        with self.table.batch_writer(batch_size=25) as batch:
            for idx, doc in enumerate(documents):
                # Generate embedding
                embedding = self.embeddings.embed_query(doc.page_content)
                
                item = {
                    'id': f"{doc.metadata.get('source', f'doc_{idx}')}#{idx}",
                    'source': doc.metadata.get('source', ''),
                    'content': doc.page_content,
                    'embedding': embedding,
                    'timestamp': int(__import__('time').time())
                }
                
                batch.put_item(Item=item)
                self.document_count += 1
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents using DynamoDB scan with embedding similarity.
        
        Note: DynamoDB doesn't have native vector similarity search like pgvector.
        This implementation uses scan and calculates similarity in-memory.
        For production, consider using DynamoDB with external vector service or
        transitioning to a dedicated vector database.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Scan table (expensive operation - consider using GSI in production)
            response = self.table.scan()
            
            # Calculate similarity for each document
            import numpy as np
            
            similarities = []
            for item in response.get('Items', []):
                if 'embedding' in item:
                    doc_embedding = np.array(item['embedding'], dtype=float)
                    query_emb = np.array(query_embedding, dtype=float)
                    
                    # Cosine similarity
                    similarity = np.dot(doc_embedding, query_emb) / (
                        np.linalg.norm(doc_embedding) * np.linalg.norm(query_emb) + 1e-8
                    )
                    
                    similarities.append({
                        'item': item,
                        'similarity': float(similarity)
                    })
            
            # Sort by similarity and return top k
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            documents = []
            for result in similarities[:k]:
                item = result['item']
                doc = Document(
                    page_content=item.get('content', ''),
                    metadata={
                        'source': item.get('source', ''),
                        'similarity_score': result['similarity']
                    }
                )
                documents.append(doc)
            
            return documents
        except Exception as e:
            print(f"DynamoDB search error: {e}")
            return []
    
    def save(self, path: str = None) -> None:
        """DynamoDB persists data automatically."""
        pass
    
    def load(self, path: str = None) -> None:
        """DynamoDB loads data automatically."""
        pass


class VertexAIVectorStore(VectorStoreBase):
    """Google Cloud Vertex AI Vector Search implementation."""
    
    def __init__(self, embeddings: Optional[Embeddings] = None):
        """Initialize Vertex AI Vector Search.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        from google.cloud import aiplatform
        
        self.embeddings = embeddings or get_embeddings()
        
        # Validate configuration
        if not config.gcp_project_id or not config.vertex_ai_index_id or not config.vertex_ai_endpoint:
            raise ValueError(
                "Vertex AI credentials not set. Required: GCP_PROJECT_ID, VERTEX_AI_INDEX_ID, VERTEX_AI_ENDPOINT"
            )
        
        # Initialize Vertex AI
        aiplatform.init(
            project=config.gcp_project_id,
            location=config.gcp_region or "us-central1"
        )
        
        self.index_id = config.vertex_ai_index_id
        self.endpoint_id = config.vertex_ai_endpoint
        self.project_id = config.gcp_project_id
        self.region = config.gcp_region or "us-central1"
        
        # Initialize Vector Search Index client
        self.index_client = aiplatform.MatchingEngineIndexEndpoint(
            self.endpoint_id
        )
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to Vertex AI Vector Search index.
        
        Args:
            documents: List of documents to add
        """
        try:
            from google.cloud import aiplatform
            
            # Prepare data points for batch upload
            data_points = []
            
            for idx, doc in enumerate(documents):
                # Generate embedding
                embedding = self.embeddings.embed_query(doc.page_content)
                
                # Create data point with ID, embedding, and restricted metadata
                data_point = aiplatform.MatchingEngineIndexDatapoint(
                    datapoint_id=f"{doc.metadata.get('source', f'doc_{idx}')}#{idx}",
                    feature_vector=embedding,
                    crowding_tag=doc.metadata.get('source', ''),
                    restricts=[
                        aiplatform.MatchingEngineIndexDatapointRestriction(
                            namespace=key,
                            allow_list=[str(value)]
                        )
                        for key, value in doc.metadata.items()
                        if key != 'source'
                    ]
                )
                data_points.append(data_point)
            
            # Upsert data points to index
            if data_points:
                self.index_client.upsert_datapoints(data_points)
                
        except Exception as e:
            print(f"Error adding documents to Vertex AI: {e}")
    
    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Search for similar documents using Vertex AI Vector Search.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            
            # Search using Vector Search index
            response = self.index_client.find_neighbors(
                deployed_index_id=self.endpoint_id,
                queries=[query_embedding],
                num_neighbors=k
            )
            
            documents = []
            
            # Process neighbors from response
            if response and len(response) > 0:
                for neighbor in response[0].neighbors:
                    doc = Document(
                        page_content=neighbor.datapoint.datapoint_id,
                        metadata={
                            'distance': neighbor.distance,
                            'datapoint_id': neighbor.datapoint.datapoint_id
                        }
                    )
                    documents.append(doc)
            
            return documents
            
        except Exception as e:
            print(f"Vertex AI search error: {e}")
            return []
    
    def save(self, path: str = None) -> None:
        """Vertex AI persists data automatically."""
        pass
    
    def load(self, path: str = None) -> None:
        """Vertex AI loads data automatically."""
        pass


class LanceDBVectorStore(VectorStoreBase):
    """LanceDB-based vector store with metadata filtering support.
    
    Supports filtering by:
    - source: 'database_schema', 'sklearn', 'scipy', 'pandas', 'ml_guide'
    - topic: 'preprocessing', 'modeling', 'statistics', 'data_quality'
    - doc_type: 'schema', 'ml_guide', 'stats_guide', 'api_reference'
    """
    
    def __init__(self, embeddings: Optional[Embeddings] = None, db_path: str = "./lancedb", table_name: str = "analytics_rag"):
        """Initialize LanceDB vector store.
        
        Args:
            embeddings: Optional embeddings instance (uses factory if not provided)
            db_path: Path to LanceDB database directory
            table_name: Name of the table to use (default: "analytics_rag")
        """
        import lancedb
        
        self.embeddings = embeddings or get_embeddings()
        self.db_path = db_path
        self.table_name = table_name
        
        # Connect to LanceDB
        self.db = lancedb.connect(db_path)
        self.table = None
        
        # Try to open existing table (silently fail if doesn't exist)
        try:
            self.table = self.db.open_table(self.table_name)
            print(f"[LanceDB] Opened existing table: {self.table_name}")
        except:
            # Table will be created when first document is added
            pass
    
    def add_documents(self, documents: List[Document]) -> None:
        """Add documents to LanceDB with metadata.
        
        Args:
            documents: List of documents with metadata to add
        """
        if not documents:
            return
        
        import json
        
        # Prepare data with embeddings and metadata
        data = []
        for doc in documents:
            # Generate embedding
            embedding = self.embeddings.embed_query(doc.page_content)
            
            # Extract metadata fields
            metadata = doc.metadata or {}
            
            data.append({
                "content": doc.page_content,
                "vector": embedding,
                "source": metadata.get("source", "unknown"),
                "topic": metadata.get("topic", "general"),
                "doc_type": metadata.get("doc_type", "general"),
                "file_path": metadata.get("file_path", ""),
                "chunk_id": metadata.get("chunk_id", 0),
                # Store full metadata as JSON string for flexibility
                "metadata_json": json.dumps(metadata)
            })
        
        # Create or append to table
        if self.table is None:
            self.table = self.db.create_table(self.table_name, data)
            print(f"[LanceDB] Created table '{self.table_name}' with {len(data)} documents")
        else:
            self.table.add(data)
            print(f"[LanceDB] Added {len(data)} documents to '{self.table_name}'")
    
    def similarity_search(
        self, 
        query: str, 
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search for similar documents with optional metadata filtering.
        
        Args:
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filters, e.g.:
                {"source": "sklearn"}
                {"topic": "preprocessing"}
                {"doc_type": "ml_guide", "source": "sklearn"}
        
        Returns:
            List of similar documents
        """
        if self.table is None:
            return []
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(query)
        
        # Build search query
        search = self.table.search(query_embedding).limit(k)
        
        # Apply metadata filters if provided
        if filter_dict:
            filter_conditions = []
            for key, value in filter_dict.items():
                if key in ["source", "topic", "doc_type"]:
                    filter_conditions.append(f"{key} = '{value}'")
            
            if filter_conditions:
                filter_str = " AND ".join(filter_conditions)
                search = search.where(filter_str)
        
        # Execute search
        results = search.to_list()
        
        # Convert to LangChain documents
        documents = []
        for result in results:
            metadata = {
                "source": result.get("source", "unknown"),
                "topic": result.get("topic", "general"),
                "doc_type": result.get("doc_type", "general"),
                "file_path": result.get("file_path", ""),
                "chunk_id": result.get("chunk_id", 0),
                "score": result.get("_distance", 0.0)
            }
            
            # Include metadata_json if present (for method cards)
            if "metadata_json" in result:
                metadata["metadata_json"] = result["metadata_json"]
            
            documents.append(Document(
                page_content=result["content"],
                metadata=metadata
            ))
        
        return documents
    
    def similarity_search_with_rerank(
        self,
        query: str,
        k: int = 5,
        initial_k: int = 20,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Search with reranking for better relevance.
        
        Retrieves more candidates (initial_k), then reranks using keyword matching
        and returns top k results.
        
        Args:
            query: Search query
            k: Number of final results to return
            initial_k: Number of initial candidates to retrieve
            filter_dict: Optional metadata filters
        
        Returns:
            Reranked list of documents
        """
        # Get more candidates than needed
        candidates = self.similarity_search(query, k=initial_k, filter_dict=filter_dict)
        
        if not candidates:
            return []
        
        # Keyword-based reranking with dynamic relevance scoring
        query_terms = set(query.lower().split())
        
        scored_docs = []
        for doc in candidates:
            content_lower = doc.page_content.lower()
            
            # Count keyword matches in content
            keyword_score = sum(1 for term in query_terms if term in content_lower)
            
            # Boost for keyword matches in topic metadata (more specific)
            topic = doc.metadata.get("topic", "").lower()
            topic_match_score = sum(1 for term in query_terms if term in topic) * 2
            
            # Combine with vector similarity (from metadata)
            vector_score = 1.0 - doc.metadata.get("score", 0.5)  # Lower distance = higher score
            
            # Weighted combination with topic boosting
            # 50% semantic, 30% keyword, 20% topic metadata
            combined_score = (
                (0.5 * vector_score) + 
                (0.3 * (keyword_score / max(len(query_terms), 1))) +
                (0.2 * (topic_match_score / max(len(query_terms), 1)))
            )
            
            scored_docs.append((combined_score, doc))
        
        # Sort by combined score (descending)
        scored_docs.sort(reverse=True, key=lambda x: x[0])
        
        # Return top k with updated scores
        reranked = []
        for score, doc in scored_docs[:k]:
            doc.metadata["rerank_score"] = score
            reranked.append(doc)
        
        return reranked
    
    def similarity_search_by_source(
        self,
        query: str,
        source: str,
        k: int = 5
    ) -> List[Document]:
        """Search within a specific source (convenience method).
        
        Args:
            query: Search query
            source: Source filter (e.g., 'sklearn', 'database_schema')
            k: Number of results
        
        Returns:
            Filtered documents
        """
        return self.similarity_search(query, k=k, filter_dict={"source": source})
    
    def similarity_search_by_topic(
        self,
        query: str,
        topic: str,
        k: int = 5
    ) -> List[Document]:
        """Search within a specific topic (convenience method).
        
        Args:
            query: Search query
            topic: Topic filter (e.g., 'preprocessing', 'modeling')
            k: Number of results
        
        Returns:
            Filtered documents
        """
        return self.similarity_search(query, k=k, filter_dict={"topic": topic})
    
    def get_sources(self) -> List[str]:
        """Get all unique sources in the database.
        
        Returns:
            List of unique source values
        """
        if self.table is None:
            return []
        
        try:
            # Query distinct sources
            result = self.table.to_pandas()["source"].unique().tolist()
            return result
        except:
            return []
    
    def get_topics(self) -> List[str]:
        """Get all unique topics in the database.
        
        Returns:
            List of unique topic values
        """
        if self.table is None:
            return []
        
        try:
            result = self.table.to_pandas()["topic"].unique().tolist()
            return result
        except:
            return []
    
    def save(self, path: str = None) -> None:
        """LanceDB persists data automatically to db_path."""
        print(f"[LanceDB] Data automatically persisted to {self.db_path}")
    
    def load(self, path: str = None) -> None:
        """Load existing LanceDB table."""
        try:
            self.table = self.db.open_table(self.table_name)
            print(f"[LanceDB] Loaded table '{self.table_name}'")
        except Exception as e:
            print(f"[LanceDB] Could not load table: {e}")
            self.table = None


def get_vector_store(
    vector_store_type: Optional[str] = None,
    embeddings: Optional[Embeddings] = None
) -> VectorStoreBase:
    """Get the configured vector store.
    
    Args:
        vector_store_type: Type of vector store (uses config if not provided)
        embeddings: Optional embeddings instance (uses factory if not provided)
    
    Returns:
        Vector store instance
        
    Raises:
        ValueError: If vector store type is not supported
    """
    store_type = vector_store_type or config.vector_store_type
    
    if store_type == "faiss":
        return FAISSVectorStore(embeddings)
    elif store_type == "lancedb":
        return LanceDBVectorStore(embeddings)
    elif store_type == "weaviate":
        return WeaviateVectorStore(embeddings)
    elif store_type == "opensearch":
        return OpenSearchVectorStore(embeddings)
    elif store_type == "pinecone":
        return PineconeVectorStore(embeddings)
    elif store_type == "chroma":
        return ChromaVectorStore(embeddings)
    elif store_type == "azure_search":
        return AzureSearchVectorStore(embeddings)
    elif store_type == "kendra":
        return KendraVectorStore(embeddings)
    elif store_type == "aurora_pgvector":
        return AuroraPgvectorStore(embeddings)
    elif store_type == "dynamodb":
        return DynamoDBVectorStore(embeddings)
    elif store_type == "vertex_ai":
        return VertexAIVectorStore(embeddings)
    else:
        raise ValueError(
            f"Unsupported vector store type: {store_type}. "
            f"Supported types: faiss, lancedb, weaviate, opensearch, pinecone, chroma, azure_search, kendra, aurora_pgvector, dynamodb, vertex_ai"
        )
