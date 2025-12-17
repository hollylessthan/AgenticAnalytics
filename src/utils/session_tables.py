"""Session table manager for pinning DataFrames as temporary tables."""

import duckdb
import pandas as pd
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path


class PinnedTable(dict):
    """Information about a pinned table."""
    
    def __init__(self, name: str, original_query: str, row_count: int, columns: List[str], created_at: datetime):
        super().__init__(
            name=name,
            original_query=original_query,
            row_count=row_count,
            columns=columns,
            created_at=created_at
        )


class SessionTableManager:
    """Manages temporary pinned tables within a user session."""
    
    def __init__(self, db_connection: Any):
        """Initialize the session table manager.
        
        Args:
            db_connection: Database connection (DuckDB or other)
        """
        self.db = db_connection
        self.pinned_tables: Dict[str, PinnedTable] = {}
        self.table_counter = 0
    
    def pin_dataframe(self, df: pd.DataFrame, original_query: str = "", custom_name: str = None) -> str:
        """Pin a DataFrame as a temporary table.
        
        Args:
            df: DataFrame to pin
            original_query: The SQL query that generated this data
            custom_name: Optional custom name for the table
            
        Returns:
            Name of the created table
        """
        # Generate table name
        if custom_name:
            table_name = f"pinned_{custom_name}"
        else:
            self.table_counter += 1
            table_name = f"pinned_table_{self.table_counter}"
        
        # Create temporary table in DuckDB
        if isinstance(self.db, duckdb.DuckDBPyConnection):
            # DuckDB can create table directly from DataFrame
            self.db.execute(f"CREATE OR REPLACE TEMP TABLE {table_name} AS SELECT * FROM df")
        else:
            # For other databases, we'd need different logic
            raise NotImplementedError("Only DuckDB is supported for pinned tables currently")
        
        # Store metadata
        self.pinned_tables[table_name] = PinnedTable(
            name=table_name,
            original_query=original_query,
            row_count=len(df),
            columns=list(df.columns),
            created_at=datetime.now()
        )
        
        return table_name
    
    def list_pinned_tables(self) -> List[Dict[str, Any]]:
        """Get list of all pinned tables.
        
        Returns:
            List of table metadata dicts
        """
        return [dict(table) for table in self.pinned_tables.values()]
    
    def get_table_info(self, table_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific pinned table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table metadata dict or None if not found
        """
        return dict(self.pinned_tables.get(table_name)) if table_name in self.pinned_tables else None
    
    def get_table_preview(self, table_name: str, limit: int = 5) -> Optional[pd.DataFrame]:
        """Get a preview of a pinned table.
        
        Args:
            table_name: Name of the table
            limit: Number of rows to return
            
        Returns:
            DataFrame preview or None if table not found
        """
        if table_name not in self.pinned_tables:
            return None
        
        try:
            return self.db.execute(f"SELECT * FROM {table_name} LIMIT {limit}").fetchdf()
        except Exception:
            return None
    
    def rename_table(self, old_name: str, new_name: str) -> bool:
        """Rename a pinned table.
        
        Args:
            old_name: Current table name
            new_name: New table name (will be prefixed with 'pinned_')
            
        Returns:
            True if successful, False otherwise
        """
        if old_name not in self.pinned_tables:
            return False
        
        new_table_name = f"pinned_{new_name}" if not new_name.startswith("pinned_") else new_name
        
        try:
            # Rename in database
            self.db.execute(f"CREATE OR REPLACE TEMP TABLE {new_table_name} AS SELECT * FROM {old_name}")
            self.db.execute(f"DROP TABLE {old_name}")
            
            # Update metadata
            table_info = self.pinned_tables.pop(old_name)
            table_info['name'] = new_table_name
            self.pinned_tables[new_table_name] = table_info
            
            return True
        except Exception:
            return False
    
    def drop_table(self, table_name: str) -> bool:
        """Drop a pinned table.
        
        Args:
            table_name: Name of the table to drop
            
        Returns:
            True if successful, False otherwise
        """
        if table_name not in self.pinned_tables:
            return False
        
        try:
            self.db.execute(f"DROP TABLE IF EXISTS {table_name}")
            del self.pinned_tables[table_name]
            return True
        except Exception:
            return False
    
    def clear_all(self) -> None:
        """Drop all pinned tables."""
        for table_name in list(self.pinned_tables.keys()):
            self.drop_table(table_name)
    
    def get_schema_info(self) -> str:
        """Get schema information for all pinned tables.
        
        This can be included in SQL agent prompts so LLM knows about pinned tables.
        
        Returns:
            Formatted schema string
        """
        if not self.pinned_tables:
            return ""
        
        schema_parts = ["\n=== PINNED TABLES (User-saved data) ==="]
        
        for table_name, info in self.pinned_tables.items():
            schema_parts.append(f"\nTable: {table_name}")
            schema_parts.append(f"  Columns: {', '.join(info['columns'])}")
            schema_parts.append(f"  Rows: {info['row_count']}")
            if info['original_query']:
                schema_parts.append(f"  Source: {info['original_query'][:100]}...")
        
        return "\n".join(schema_parts)
