"""Base agent classes and utilities."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from datetime import datetime


class ConversationSnapshot(BaseModel):
    """Snapshot of a conversation turn with results."""
    
    timestamp: datetime = Field(default_factory=datetime.now, description="When this snapshot was created")
    query: str = Field(default="", description="User query for this turn")
    sql_query: Optional[str] = Field(default=None, description="SQL query executed")
    dataframe: Optional[Any] = Field(default=None, description="DataFrame result (stored in memory)")
    visualization_path: Optional[str] = Field(default=None, description="Path to visualization")
    visualization_code: Optional[str] = Field(default=None, description="Code used to generate visualization")
    response: Optional[str] = Field(default=None, description="Agent response to user")
    snapshot_id: int = Field(default=0, description="Sequential ID for this snapshot (1, 2, 3...)")
    
    class Config:
        arbitrary_types_allowed = True


class AgentState(BaseModel):
    """State shared across all agents in the workflow."""
    
    # Core query information
    query: str = Field(default="", description="Original user query")
    user_query: str = Field(default="", description="Alias for query (backward compatibility)")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    
    # Routing information (new for hybrid classifier)
    plan_type: Optional[str] = Field(default=None, description="Execution plan type from classifier")
    confidence_score: Optional[float] = Field(default=None, description="Classifier confidence (0-1)")
    agent_chain: List[str] = Field(default_factory=list, description="Sequence of agents executed")
    
    # SQL agent outputs
    sql_query: Optional[str] = None
    query_results: Optional[Any] = None  # Can be DataFrame, list, dict, or any type
    
    # Analysis agent outputs
    analysis_code: Optional[str] = None
    analysis_results: Optional[str] = None  # Changed to string for easier communication
    
    # Visualization agent outputs
    visualization_code: Optional[str] = None
    visualization_path: Optional[str] = None
    visualization_paths: List[str] = Field(default_factory=list, description="Paths to all generated visualizations")
    
    # Communication agent outputs
    final_response: Optional[str] = None  # Main response to user
    final_answer: Optional[str] = None  # Backward compatibility alias
    result_summary: Optional[str] = Field(default=None, description="Brief summary of results")
    
    # Session state (NEW - for data reuse and iterative refinement)
    cached_dataframe: Optional[Any] = Field(default=None, description="Cached DataFrame from previous query")
    last_sql_query: Optional[str] = Field(default=None, description="Last executed SQL query")
    current_visualization_code: Optional[str] = Field(default=None, description="Current visualization code for updates")
    reuse_data: bool = Field(default=False, description="Whether to reuse cached data instead of re-querying")
    update_visualization: bool = Field(default=False, description="Whether to update existing viz instead of creating new")
    
    # Conversation history (NEW - stores last N snapshots for multi-turn context)
    state_history: List[ConversationSnapshot] = Field(default_factory=list, description="Last N conversation snapshots with data/viz")
    max_history_size: int = Field(default=10, description="Maximum number of snapshots to keep")
    referenced_snapshot_id: Optional[int] = Field(default=None, description="ID of snapshot being referenced (e.g., 'use data from step 2')")
    
    # Control flow
    errors: List[str] = Field(default_factory=list)
    next_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def sync_query_fields(self):
        """Sync query and user_query fields for backward compatibility."""
        if self.query and not self.user_query:
            self.user_query = self.query
        elif self.user_query and not self.query:
            self.query = self.user_query
        elif not self.query and not self.user_query:
            self.query = ""
            self.user_query = ""
        
        # Sync final_response and final_answer
        if self.final_response and not self.final_answer:
            self.final_answer = self.final_response
        elif self.final_answer and not self.final_response:
            self.final_response = self.final_answer
        
        return self
    
    def add_snapshot(self) -> None:
        """Create a snapshot of current state and add to history.
        
        Automatically trims history to max_history_size.
        """
        if self.query_results is not None or self.visualization_path:
            snapshot = ConversationSnapshot(
                query=self.query,
                sql_query=self.sql_query,
                dataframe=self.query_results if hasattr(self.query_results, 'shape') else None,  # Only store DataFrames
                visualization_path=self.visualization_path,
                visualization_code=self.visualization_code,
                response=self.final_response,
                snapshot_id=len(self.state_history) + 1
            )
            self.state_history.append(snapshot)
            
            # Trim to max size
            if len(self.state_history) > self.max_history_size:
                self.state_history = self.state_history[-self.max_history_size:]
                # Re-index snapshots
                for idx, snap in enumerate(self.state_history, 1):
                    snap.snapshot_id = idx
    
    def get_snapshot(self, snapshot_id: int) -> Optional[ConversationSnapshot]:
        """Retrieve a specific snapshot by ID.
        
        Args:
            snapshot_id: The snapshot ID to retrieve
            
        Returns:
            ConversationSnapshot if found, None otherwise
        """
        for snapshot in self.state_history:
            if snapshot.snapshot_id == snapshot_id:
                return snapshot
        return None
    
    def get_latest_snapshot(self) -> Optional[ConversationSnapshot]:
        """Get the most recent snapshot.
        
        Returns:
            Latest ConversationSnapshot if exists, None otherwise
        """
        return self.state_history[-1] if self.state_history else None


class BaseAgent(ABC):
    """Base class for all agents."""
    
    def __init__(self, config: Any = None, name: str = None, description: str = None):
        """Initialize the agent.
        
        Args:
            config: Configuration object (for new agents)
            name: Agent name (for backward compatibility)
            description: Agent description (for backward compatibility)
        """
        self.config = config
        self.name = name or self.__class__.__name__
        self.description = description or f"{self.__class__.__name__} agent"
    
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
