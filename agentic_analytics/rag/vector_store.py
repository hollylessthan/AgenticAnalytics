"""Vector store management for RAG."""

import faiss
import numpy as np
from typing import List, Dict, Any, Optional
from langchain_openai import OpenAIEmbeddings
from agentic_analytics.config.settings import settings


class VectorStore:
    """Vector store for storing and retrieving database schema information."""
    
    def __init__(self, store_type: str = "faiss"):
        """Initialize vector store.
        
        Args:
            store_type: Type of vector store ('faiss' or 'weaviate')
        """
        self.store_type = store_type
        self.embeddings = None
        
        # Only initialize embeddings if API key is available
        if settings.openai_api_key:
            try:
                self.embeddings = OpenAIEmbeddings(
                    model=settings.embedding_model,
                    api_key=settings.openai_api_key
                )
            except Exception as e:
                print(f"Warning: Failed to initialize embeddings: {e}")
                self.embeddings = None
        
        self.documents: List[Dict[str, Any]] = []
        self.index: Optional[faiss.Index] = None
        self.dimension: int = 1536  # OpenAI embedding dimension
        
        if store_type == "faiss":
            self._init_faiss()
        elif store_type == "weaviate":
            self._init_weaviate()
    
    def _init_faiss(self):
        """Initialize FAISS index."""
        self.index = faiss.IndexFlatL2(self.dimension)
    
    def _init_weaviate(self):
        """Initialize Weaviate client."""
        # Placeholder for Weaviate initialization
        # This would require weaviate-client setup
        try:
            import weaviate
            self.weaviate_client = weaviate.Client(settings.weaviate_url)
        except Exception as e:
            print(f"Weaviate initialization failed: {e}. Falling back to FAISS.")
            self._init_faiss()
            self.store_type = "faiss"
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """Add documents to the vector store.
        
        Args:
            documents: List of document dictionaries with 'text' and 'metadata' keys
        """
        if not documents:
            return
        
        # If embeddings are not initialized, just store the documents without embeddings
        if self.embeddings is None:
            self.documents.extend(documents)
            return
        
        # Extract texts
        texts = [doc.get("text", "") for doc in documents]
        
        # Generate embeddings
        try:
            embeddings = self.embeddings.embed_documents(texts)
            
            if self.store_type == "faiss":
                self._add_to_faiss(embeddings, documents)
            elif self.store_type == "weaviate":
                self._add_to_weaviate(embeddings, documents)
        except Exception as e:
            print(f"Warning: Failed to generate embeddings: {e}")
            self.documents.extend(documents)
    
    def _add_to_faiss(self, embeddings: List[List[float]], documents: List[Dict[str, Any]]):
        """Add embeddings to FAISS index."""
        embeddings_array = np.array(embeddings).astype('float32')
        self.index.add(embeddings_array)
        self.documents.extend(documents)
    
    def _add_to_weaviate(self, embeddings: List[List[float]], documents: List[Dict[str, Any]]):
        """Add embeddings to Weaviate."""
        # Placeholder for Weaviate add operation
        pass
    
    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query: Query text
            k: Number of results to return
            
        Returns:
            List of matching documents
        """
        if self.store_type == "faiss":
            return self._search_faiss(query, k)
        elif self.store_type == "weaviate":
            return self._search_weaviate(query, k)
        return []
    
    def _search_faiss(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Search FAISS index."""
        if self.index.ntotal == 0 or self.embeddings is None:
            # If no embeddings, return all documents (fallback)
            return self.documents[:k] if self.documents else []
        
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)
            query_array = np.array([query_embedding]).astype('float32')
            
            # Search
            k = min(k, self.index.ntotal)
            distances, indices = self.index.search(query_array, k)
            
            # Get matching documents
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.documents):
                    doc = self.documents[idx].copy()
                    doc['score'] = float(distances[0][i])
                    results.append(doc)
            
            return results
        except Exception as e:
            print(f"Warning: Search failed: {e}")
            return self.documents[:k] if self.documents else []
    
    def _search_weaviate(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Search Weaviate."""
        # Placeholder for Weaviate search
        return []
    
    def load_schema(self, schema_info: str):
        """Load database schema into vector store.
        
        Args:
            schema_info: Database schema as text
        """
        # Split schema into logical chunks (by table)
        tables = schema_info.split("\n\n")
        documents = []
        
        for table in tables:
            if table.strip():
                documents.append({
                    "text": table,
                    "metadata": {"type": "schema"}
                })
        
        self.add_documents(documents)
