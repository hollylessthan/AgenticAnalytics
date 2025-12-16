"""SQL query generation agent."""

from typing import Any, Dict
from langchain.prompts import ChatPromptTemplate
from agentic_analytics.agents.base import BaseAgent


class SQLAgent(BaseAgent):
    """Agent responsible for converting natural language to SQL queries."""
    
    def __init__(self):
        super().__init__(
            name="SQL Agent",
            description="Converts natural language questions into SQL queries"
        )
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert SQL query generator. 
            Given a natural language question and database schema, generate a valid SQL query.
            
            Database Schema:
            {schema}
            
            Instructions:
            - Generate only the SQL query, no explanations
            - Use proper SQL syntax
            - Include appropriate WHERE, GROUP BY, ORDER BY clauses as needed
            - Use JOINs when multiple tables are involved
            """),
            ("user", "{question}")
        ])
    
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate SQL query from natural language question.
        
        Args:
            task: Natural language question
            context: Dictionary containing 'schema' information
            
        Returns:
            Dictionary with 'sql_query' and 'success' status
        """
        try:
            schema = context.get("schema", "")
            
            messages = self.prompt.format_messages(
                schema=schema,
                question=task
            )
            
            response = self.llm.invoke(messages)
            sql_query = response.content.strip()
            
            # Clean up the query (remove markdown code blocks if present)
            if sql_query.startswith("```sql"):
                sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
            elif sql_query.startswith("```"):
                sql_query = sql_query.replace("```", "").strip()
            
            return {
                "success": True,
                "sql_query": sql_query,
                "agent": self.name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
