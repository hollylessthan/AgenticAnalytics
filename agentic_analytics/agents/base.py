"""Base agent class for all specialized agents."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from langchain_openai import ChatOpenAI
from agentic_analytics.config.settings import settings


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str, description: str):
        """Initialize the base agent.
        
        Args:
            name: Name of the agent
            description: Description of agent's capabilities
        """
        self.name = name
        self.description = description
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.temperature,
            api_key=settings.openai_api_key
        )
    
    @abstractmethod
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the agent's task.
        
        Args:
            task: The task description
            context: Context information including previous results
            
        Returns:
            Dictionary containing results and metadata
        """
        pass
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
