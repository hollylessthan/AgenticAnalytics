"""RAG (Retrieval Augmented Generation) system with metadata filtering."""

from typing import List, Optional, Dict, Any, Tuple
import json
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate

from .vector_store import get_vector_store, VectorStoreBase, LanceDBVectorStore
from .method_card import MethodCard
from ..config import config
from ..utils.llm_factory import get_llm
from ..utils.embedding_factory import get_embeddings


class RAGSystem:
    """RAG system with metadata-aware retrieval for context-aware query processing."""
    
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
        
        # Check if using LanceDB for metadata filtering support
        self.supports_metadata_filtering = isinstance(self.vector_store, LanceDBVectorStore)
    
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
            metadata={
                "type": "database_schema",
                "source": "database_schema",
                "topic": "schema",
                "doc_type": "schema"
            }
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
    
    def retrieve_context(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """Retrieve relevant context from vector store.
        
        The reranking system uses metadata (topic) matching for better relevance,
        eliminating the need for hardcoded query expansion.
        
        Args:
            query: User query
            k: Number of documents to retrieve
            filter_dict: Optional metadata filters for LanceDB:
                {"source": "sklearn"}  # Only sklearn docs
                {"topic": "preprocessing"}  # Only preprocessing docs
                {"source": "sklearn", "topic": "modeling"}  # Combine filters
            
        Returns:
            List of relevant documents
        """
        # Use reranking if available (LanceDB) - reranker uses topic metadata matching
        if hasattr(self.vector_store, 'similarity_search_with_rerank'):
            return self.vector_store.similarity_search_with_rerank(
                query, 
                k=k, 
                initial_k=k*5,  # Retrieve 5x candidates for reranking
                filter_dict=filter_dict
            )
        elif self.supports_metadata_filtering and filter_dict:
            return self.vector_store.similarity_search(query, k=k, filter_dict=filter_dict)
        else:
            return self.vector_store.similarity_search(query, k=k)
    
    def retrieve_preprocessing_context(self, query: str, k: int = 3) -> List[Document]:
        """Retrieve preprocessing-specific context.
        
        Args:
            query: User query
            k: Number of documents
        
        Returns:
            Preprocessing-related documents
        """
        if self.supports_metadata_filtering:
            return self.vector_store.similarity_search(
                query,
                k=k,
                filter_dict={"topic": "preprocessing"}
            )
        else:
            # Fallback: Add preprocessing keywords to query
            enhanced_query = f"preprocessing data cleaning encoding scaling {query}"
            return self.vector_store.similarity_search(enhanced_query, k=k)
    
    def retrieve_modeling_context(self, query: str, k: int = 3) -> List[Document]:
        """Retrieve model selection context.
        
        Args:
            query: User query
            k: Number of documents
        
        Returns:
            Modeling-related documents
        """
        if self.supports_metadata_filtering:
            return self.vector_store.similarity_search(
                query,
                k=k,
                filter_dict={"topic": "modeling"}
            )
        else:
            enhanced_query = f"model selection algorithm classification regression {query}"
            return self.vector_store.similarity_search(enhanced_query, k=k)
    
    def retrieve_statistics_context(self, query: str, k: int = 3) -> List[Document]:
        """Retrieve statistical tests context.
        
        Args:
            query: User query
            k: Number of documents
        
        Returns:
            Statistics-related documents
        """
        if self.supports_metadata_filtering:
            return self.vector_store.similarity_search(
                query,
                k=k,
                filter_dict={"topic": "statistics"}
            )
        else:
            enhanced_query = f"statistical test correlation hypothesis testing {query}"
            return self.vector_store.similarity_search(enhanced_query, k=k)
    
    def retrieve_schema_context(self, query: str, k: int = 3) -> List[Document]:
        """Retrieve database schema context.
        
        Args:
            query: User query
            k: Number of documents
        
        Returns:
            Schema-related documents
        """
        if self.supports_metadata_filtering:
            return self.vector_store.similarity_search(
                query,
                k=k,
                filter_dict={"source": "database_schema"}
            )
        else:
            # Fallback: Standard retrieval
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
    
    def retrieve_method_cards(
        self,
        query: str,
        data_profile: Optional[Dict[str, Any]] = None,
        k: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[MethodCard, float]]:
        """Retrieve method cards from method knowledge base.
        
        This is the new paradigm: retrieve applicable methods (decision units)
        instead of random documentation paragraphs.
        
        Args:
            query: User query describing the problem
            data_profile: Optional data profile from ProfilingAgent for constraint matching
            k: Number of method cards to return
            filter_dict: Optional metadata filters:
                {"category": "model_classification"}
                {"problem_type": "normality_test"}
                {"source": "sklearn"}
        
        Returns:
            List of tuples (MethodCard, confidence_score)
        """
        # Get method card vector store (separate table)
        from .vector_store import LanceDBVectorStore
        
        # Create store with method_cards table
        method_store = LanceDBVectorStore(
            embeddings=self.embeddings,
            table_name="method_cards"
        )
        
        if method_store.table is None:
            print(f"[MethodCards] Table 'method_cards' not found. Run load_method_cards.py first.")
            return []
        
        # Step 1: Vector search (semantic similarity)
        # Retrieve more candidates for constraint filtering
        initial_k = k * 3 if data_profile else k * 2
        
        if hasattr(method_store, 'similarity_search_with_rerank'):
            # Use reranking for better results
            docs = method_store.similarity_search_with_rerank(
                query,
                k=initial_k,
                initial_k=initial_k * 2,
                filter_dict=filter_dict
            )
        else:
            docs = method_store.similarity_search(
                query,
                k=initial_k,
                filter_dict=filter_dict
            )
        
        # Step 2: Parse method cards from documents
        method_cards = []
        for doc in docs:
            try:
                # Reconstruct MethodCard from metadata
                # card_json is stored in metadata_json dictionary
                metadata_json_str = doc.metadata.get("metadata_json")
                if metadata_json_str:
                    # Parse the metadata_json string to get the dict
                    metadata_dict = json.loads(metadata_json_str) if isinstance(metadata_json_str, str) else metadata_json_str
                    # Extract card_json from metadata dict
                    card_json = metadata_dict.get("card_json")
                    if card_json:
                        card_dict = json.loads(card_json) if isinstance(card_json, str) else card_json
                        card = MethodCard.from_dict(card_dict)
                        method_cards.append(card)
            except Exception as e:
                # If parsing fails, skip this card
                print(f"[MethodCards] Error parsing card: {e}")
                continue
        
        # Step 3: Constraint filtering and scoring
        if data_profile and method_cards:
            scored_cards = []
            for card in method_cards:
                passes_constraints, applicability_score = card.matches_data_profile(data_profile)
                if passes_constraints or applicability_score > 0.3:  # Soft threshold
                    scored_cards.append((card, applicability_score))
            
            # Sort by applicability score
            scored_cards.sort(key=lambda x: x[1], reverse=True)
            return scored_cards[:k]
        else:
            # No data profile - return based on semantic similarity only
            # Assign uniform scores
            return [(card, 1.0) for card in method_cards[:k]]
    
    def retrieve_methods_for_preprocessing(
        self,
        query: str,
        data_profile: Optional[Dict[str, Any]] = None,
        k: int = 3
    ) -> List[Tuple[MethodCard, float]]:
        """Retrieve preprocessing method cards.
        
        Args:
            query: Preprocessing query
            data_profile: Optional data profile for constraint matching
            k: Number of methods to return
        
        Returns:
            List of (MethodCard, confidence) tuples
        """
        # Filter for preprocessing categories
        filter_dict = {
            "topic": "preprocessing"  # Matches preprocessing_imputation, preprocessing_scaling, etc.
        }
        
        return self.retrieve_method_cards(
            query=query,
            data_profile=data_profile,
            k=k,
            filter_dict=filter_dict
        )
    
    def retrieve_methods_for_modeling(
        self,
        query: str,
        data_profile: Optional[Dict[str, Any]] = None,
        k: int = 3
    ) -> List[Tuple[MethodCard, float]]:
        """Retrieve model selection method cards.
        
        Args:
            query: Model selection query
            data_profile: Optional data profile for constraint matching
            k: Number of models to return
        
        Returns:
            List of (MethodCard, confidence) tuples
        """
        # Filter for model categories
        filter_dict = {
            "topic": "model"  # Matches model_classification, model_regression
        }
        
        return self.retrieve_method_cards(
            query=query,
            data_profile=data_profile,
            k=k,
            filter_dict=filter_dict
        )
    
    def retrieve_methods_for_statistics(
        self,
        query: str,
        data_profile: Optional[Dict[str, Any]] = None,
        k: int = 3
    ) -> List[Tuple[MethodCard, float]]:
        """Retrieve statistical test method cards.
        
        Args:
            query: Statistics query (normality, correlation, etc.)
            data_profile: Optional data profile for constraint matching
            k: Number of tests to return
        
        Returns:
            List of (MethodCard, confidence) tuples
        """
        # Filter for stats categories
        filter_dict = {
            "topic": "stats"  # Matches stats_normality, stats_correlation, etc.
        }
        
        return self.retrieve_method_cards(
            query=query,
            data_profile=data_profile,
            k=k,
            filter_dict=filter_dict
        )
    
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
