"""Base agent classes and utilities."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentState(BaseModel):
    """State shared across all agents in the workflow."""
    
    user_query: str = Field(description="Original user query")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    sql_query: Optional[str] = None
    query_results: Optional[Any] = None
    analysis_code: Optional[str] = None
    analysis_results: Optional[Dict[str, Any]] = None
    visualization_code: Optional[str] = None
    visualization_path: Optional[str] = None
    final_answer: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    next_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, description: str):
        """Initialize the agent.
        
        Args:
            name: Agent name
            description: Agent description
        """
        self.name = name
        self.description = description
    
    @abstractmethod
    def execute(self, state: AgentState) -> AgentState:
        """Execute the agent's task.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state
        """
        pass
    
    def should_continue(self, state: AgentState) -> bool:
        """Determine if the agent should continue processing.
        
        Args:
            state: Current agent state
            
        Returns:
            True if agent should continue, False otherwise
        """
        return state.next_agent is not None
