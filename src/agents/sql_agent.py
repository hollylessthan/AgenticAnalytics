"""SQL Agent for converting natural language to SQL queries."""

from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.utilities import SQLDatabase
from langchain_core.language_models import BaseChatModel

from .base import BaseAgent, AgentState
from ..utils.database import DatabaseManager


class SQLAgent(BaseAgent):
    """Agent that converts natural language to SQL and executes queries."""
    
    def __init__(self, llm: BaseChatModel):
        """Initialize SQL Agent.
        
        Args:
            llm: Language model instance
        """
        super().__init__(
            name="sql_agent",
            description="Converts natural language queries to SQL and retrieves data"
        )
        self.llm = llm
        self.db_manager = DatabaseManager()
    
    def execute(self, state: AgentState) -> AgentState:
        """Execute SQL query generation and data retrieval.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with query results
        """
        try:
            # Get database schema for context
            schema_info = self.db_manager.get_schema_info()
            
            # Generate SQL query using LLM
            sql_query = self._generate_sql_query(state.user_query, schema_info)
            state.sql_query = sql_query
            
            # Execute query
            results = self.db_manager.execute_query(sql_query)
            state.query_results = results
            
            # Determine next step
            state.next_agent = self._determine_next_step(state.user_query)
            
        except Exception as e:
            state.errors.append(f"SQL Agent Error: {str(e)}")
            state.next_agent = None
        
        return state
    
    def _generate_sql_query(self, user_query: str, schema_info: str) -> str:
        """Generate SQL query from natural language.
        
        Args:
            user_query: User's natural language query
            schema_info: Database schema information
            
        Returns:
            SQL query string
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert SQL query generator. Given a natural language question and database schema, generate a valid SQL query.

Database Schema:
{schema}

Rules:
- Generate only the SQL query, no explanations
- Use proper SQL syntax
- Include appropriate JOINs, WHERE clauses, and aggregations
- Use aliases for clarity
- Ensure the query is safe (no DROP, DELETE, UPDATE unless explicitly requested)"""),
            ("user", "{question}")
        ])
        
        response = self.llm.invoke(prompt.format_messages(
            schema=schema_info,
            question=user_query
        ))
        
        # Clean up the SQL query
        sql_query = response.content.strip()
        # Remove markdown code blocks if present
        if sql_query.startswith("```sql"):
            sql_query = sql_query[6:]
        if sql_query.startswith("```"):
            sql_query = sql_query[3:]
        if sql_query.endswith("```"):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()
    
    def _determine_next_step(self, user_query: str) -> Optional[str]:
        """Determine what agent should run next.
        
        Args:
            user_query: User's query
            
        Returns:
            Next agent name or None
        """
        query_lower = user_query.lower()
        
        if any(word in query_lower for word in ["analyze", "correlation", "statistics", "trend", "pattern"]):
            return "analysis"
        elif any(word in query_lower for word in ["plot", "chart", "visualize", "graph", "show"]):
            return "visualization"
        else:
            return None  # Just return the data
