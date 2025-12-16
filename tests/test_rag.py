"""Tests for RAG system."""

import pytest
from unittest.mock import Mock, patch
from langchain.docstore.document import Document
from src.rag.rag_system import RAGSystem


class TestRAGSystem:
    """Test RAG System."""
    
    @patch('src.rag.rag_system.get_vector_store')
    @patch('src.rag.rag_system.ChatOpenAI')
    def test_initialization(self, mock_chat, mock_vector_store):
        """Test RAG system initialization."""
        rag = RAGSystem()
        
        assert rag.vector_store is not None
        assert rag.llm is not None
        assert rag.text_splitter is not None
    
    @patch('src.rag.rag_system.get_vector_store')
    @patch('src.rag.rag_system.ChatOpenAI')
    def test_index_text(self, mock_chat, mock_vector_store):
        """Test indexing text."""
        mock_store = Mock()
        mock_vector_store.return_value = mock_store
        
        rag = RAGSystem()
        rag.index_text("test content", {"key": "value"})
        
        # Verify add_documents was called
        assert mock_store.add_documents.called
