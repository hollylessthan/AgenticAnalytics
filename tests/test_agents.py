"""Tests for agents."""

import pytest
from unittest.mock import Mock, patch
from src.agents.base import AgentState


class TestAgentState:
    """Test AgentState class."""
    
    def test_agent_state_initialization(self):
        """Test AgentState initialization."""
        state = AgentState(user_query="test query")
        
        assert state.user_query == "test query"
        assert state.conversation_history == []
        assert state.sql_query is None
        assert state.errors == []
        assert state.metadata == {}
    
    def test_agent_state_with_data(self):
        """Test AgentState with data."""
        state = AgentState(
            user_query="test",
            sql_query="SELECT * FROM test",
            errors=["error1"]
        )
        
        assert state.sql_query == "SELECT * FROM test"
        assert len(state.errors) == 1
