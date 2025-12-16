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
        # AWS Kendra requires special handling - not a typical vector store
        raise NotImplementedError(
            "AWS Kendra support requires custom implementation. "
            "Use OpenSearch or another vector store for AWS."
        )
    elif store_type == "vertex_ai":
        # Vertex AI Vector Search requires special setup
        raise NotImplementedError(
            "Vertex AI Vector Search requires custom implementation. "
            "Consider using Chroma or FAISS for Google Cloud."
        )
    else:
        raise ValueError(
            f"Unsupported vector store type: {store_type}. "
            f"Supported types: faiss, weaviate, opensearch, pinecone, chroma, azure_search"
        )
