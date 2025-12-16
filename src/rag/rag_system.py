"""RAG (Retrieval Augmented Generation) system."""

from typing import List, Optional
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

from .vector_store import get_vector_store, VectorStoreBase
from ..config import config
from ..utils.llm_factory import get_llm
from ..utils.embedding_factory import get_embeddings


class RAGSystem:
    """RAG system for context-aware query processing."""
    
    def __init__(
        self,
        llm=None,
        vector_store=None,
        embeddings=None
    ):
        """Initialize RAG system.
        
        Args:
            llm: Optional LLM instance (uses factory if not provided)
            vector_store: Optional vector store instance (uses factory if not provided)
            embeddings: Optional embeddings instance (uses factory if not provided)
        """
        self.embeddings = embeddings or get_embeddings()
        self.vector_store = vector_store or get_vector_store(embeddings=self.embeddings)
        self.llm = llm or get_llm()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    def index_documents(self, documents: List[Document]) -> None:
        """Index documents for retrieval.
        
        Args:
            documents: List of documents to index
        """
        # Split documents into chunks
        splits = self.text_splitter.split_documents(documents)
        
        # Add to vector store
        self.vector_store.add_documents(splits)
    
    def index_text(self, text: str, metadata: dict = None) -> None:
        """Index plain text.
        
        Args:
            text: Text to index
            metadata: Optional metadata
        """
        doc = Document(page_content=text, metadata=metadata or {})
        self.index_documents([doc])
    
    def index_database_schema(self, schema_info: str) -> None:
        """Index database schema for better SQL generation.
        
        Args:
            schema_info: Database schema information
        """
        self.index_text(
            schema_info,
            metadata={"type": "database_schema"}
        )
    
    def index_query_examples(self, examples: List[dict]) -> None:
        """Index example queries for few-shot learning.
        
        Args:
            examples: List of example dicts with 'question' and 'sql' keys
        """
        for example in examples:
            text = f"Question: {example['question']}\nSQL: {example['sql']}"
            self.index_text(
                text,
                metadata={"type": "query_example"}
            )
    
    def retrieve_context(self, query: str, k: int = 5) -> List[Document]:
        """Retrieve relevant context for a query.
        
        Args:
            query: User query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        return self.vector_store.similarity_search(query, k=k)
    
    def augment_query(self, query: str, k: int = 5) -> str:
        """Augment query with retrieved context.
        
        Args:
            query: Original query
            k: Number of context documents to retrieve
            
        Returns:
            Augmented query with context
        """
        context_docs = self.retrieve_context(query, k=k)
        
        if not context_docs:
            return query
        
        context = "\n\n".join([doc.page_content for doc in context_docs])
        
        augmented = f"""Context Information:
{context}

User Query: {query}"""
        
        return augmented
    
    def query_with_rag(self, query: str, system_prompt: str = None) -> str:
        """Query with RAG augmentation.
        
        Args:
            query: User query
            system_prompt: Optional system prompt
            
        Returns:
            LLM response with RAG context
        """
        # Retrieve context
        context_docs = self.retrieve_context(query)
        context = "\n\n".join([doc.page_content for doc in context_docs])
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt or "You are a helpful data analyst assistant. Use the provided context to answer the question."),
            ("user", """Context:
{context}

Question: {question}

Answer:""")
        ])
        
        # Get response
        response = self.llm.invoke(prompt.format_messages(
            context=context,
            question=query
        ))
        
        return response.content
    
    def save_index(self, path: str = "faiss_index") -> None:
        """Save vector store index.
        
        Args:
            path: Path to save index
        """
        self.vector_store.save(path)
    
    def load_index(self, path: str = "faiss_index") -> None:
        """Load vector store index.
        
        Args:
            path: Path to load index from
        """
        self.vector_store.load(path)
