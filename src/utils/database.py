"""Database utilities for connection and query execution."""

from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from ..config import config
from .database_factory import get_database_engine, get_database_info


class DatabaseManager:
    """Manages database connections and query execution."""
    
    def __init__(
        self,
        database_url: Optional[str] = None,
        database_type: Optional[str] = None
    ):
        """Initialize database manager.
        
        Args:
            database_url: Database connection URL (uses config if not provided)
            database_type: Database type (uses config if not provided)
        """
        self.database_url = database_url or config.database_url
        self.database_type = database_type or config.database_type
        self.engine: Optional[Engine] = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish database connection."""
        try:
            self.engine = get_database_engine(
                database_type=self.database_type,
                connection_url=self.database_url
            )
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError as e:
            raise Exception(f"Failed to connect to database: {str(e)}")
    
    def execute_query(self, query: str) -> pd.DataFrame:
        """Execute SQL query and return results as DataFrame.
        
        Args:
            query: SQL query string
            
        Returns:
            Query results as pandas DataFrame
        """
        if self.engine is None:
            raise Exception("Database not connected")
        
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql_query(text(query), conn)
            return df
        except SQLAlchemyError as e:
            raise Exception(f"Query execution failed: {str(e)}")
    
    def get_tables(self) -> List[str]:
        """Get list of all tables in the database.
        
        Returns:
            List of table names
        """
        if self.engine is None:
            raise Exception("Database not connected")
        
        # For DuckDB, use native queries instead of SQLAlchemy inspector
        if config.database_type == "duckdb":
            query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' AND table_type = 'BASE TABLE'"
            result = self.execute_query(query)
            return result['table_name'].tolist()
        
        inspector = inspect(self.engine)
        return inspector.get_table_names()
    
    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get schema information for a specific table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with schema information
        """
        if self.engine is None:
            raise Exception("Database not connected")
        
        # For DuckDB, use native queries
        if config.database_type == "duckdb":
            query = f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'main' AND table_name = '{table_name}'
            ORDER BY ordinal_position
            """
            columns_df = self.execute_query(query)
            
            columns = []
            for _, row in columns_df.iterrows():
                columns.append({
                    "name": row["column_name"],
                    "type": row["data_type"],
                    "nullable": row["is_nullable"] == "YES"
                })
            
            return {
                "table_name": table_name,
                "columns": columns,
                "primary_keys": {"constrained_columns": []},
                "foreign_keys": [],
                "indexes": []
            }
        
        inspector = inspect(self.engine)
        
        columns = inspector.get_columns(table_name)
        primary_keys = inspector.get_pk_constraint(table_name)
        foreign_keys = inspector.get_foreign_keys(table_name)
        indexes = inspector.get_indexes(table_name)
        
        return {
            "table_name": table_name,
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "indexes": indexes
        }
    
    def get_schema_info(self) -> str:
        """Get formatted schema information for all tables.
        
        Returns:
            Formatted schema string
        """
        tables = self.get_tables()
        schema_parts = ["Database Schema:\n"]
        
        for table in tables:
            schema = self.get_table_schema(table)
            schema_parts.append(f"\nTable: {table}")
            schema_parts.append("Columns:")
            
            for col in schema["columns"]:
                col_type = str(col["type"])
                nullable = "NULL" if col["nullable"] else "NOT NULL"
                schema_parts.append(f"  - {col['name']}: {col_type} {nullable}")
            
            if schema["primary_keys"].get("constrained_columns"):
                pk_cols = ", ".join(schema["primary_keys"]["constrained_columns"])
                schema_parts.append(f"  Primary Key: ({pk_cols})")
            
            if schema["foreign_keys"]:
                schema_parts.append("  Foreign Keys:")
                for fk in schema["foreign_keys"]:
                    fk_cols = ", ".join(fk["constrained_columns"])
                    ref_table = fk["referred_table"]
                    ref_cols = ", ".join(fk["referred_columns"])
                    schema_parts.append(f"    - {fk_cols} -> {ref_table}({ref_cols})")
        
        return "\n".join(schema_parts)
    
    def get_sample_data(self, table_name: str, limit: int = 5) -> pd.DataFrame:
        """Get sample data from a table.
        
        Args:
            table_name: Name of the table
            limit: Number of rows to retrieve
            
        Returns:
            Sample data as DataFrame
        """
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        return self.execute_query(query)
    
    def validate_query(self, query: str) -> bool:
        """Validate SQL query syntax without executing it.
        
        Args:
            query: SQL query to validate
            
        Returns:
            True if query is valid, False otherwise
        """
        try:
            # Use EXPLAIN to validate without executing
            explain_query = f"EXPLAIN {query}"
            self.execute_query(explain_query)
            return True
        except:
            return False
    
    def close(self) -> None:
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
