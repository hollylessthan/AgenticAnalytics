"""Data retrieval agent."""

import sqlite3
import pandas as pd
from typing import Any, Dict
from agentic_analytics.agents.base import BaseAgent


class DataAgent(BaseAgent):
    """Agent responsible for executing SQL queries and retrieving data."""
    
    def __init__(self):
        super().__init__(
            name="Data Agent",
            description="Executes SQL queries and retrieves data from databases"
        )
    
    def execute(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SQL query and retrieve data.
        
        Args:
            task: SQL query to execute
            context: Dictionary containing 'database_path'
            
        Returns:
            Dictionary with 'data' (pandas DataFrame) and 'success' status
        """
        try:
            database_path = context.get("database_path", "")
            sql_query = task
            
            # Connect to database and execute query
            conn = sqlite3.connect(database_path)
            df = pd.read_sql_query(sql_query, conn)
            conn.close()
            
            return {
                "success": True,
                "data": df,
                "rows": len(df),
                "columns": list(df.columns),
                "agent": self.name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent": self.name
            }
