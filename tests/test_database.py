"""Tests for database utilities."""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from src.utils.database import DatabaseManager


class TestDatabaseManager:
    """Test DatabaseManager class."""
    
    @patch('src.utils.database.create_engine')
    def test_initialization(self, mock_create_engine):
        """Test database manager initialization."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db = DatabaseManager("sqlite:///test.db")
        
        assert db.engine == mock_engine
        mock_create_engine.assert_called_once_with("sqlite:///test.db")
    
    @patch('src.utils.database.create_engine')
    def test_execute_query(self, mock_create_engine):
        """Test query execution."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db = DatabaseManager()
        
        # Mock successful query
        with patch('pandas.read_sql_query') as mock_read_sql:
            expected_df = pd.DataFrame({'col1': [1, 2, 3]})
            mock_read_sql.return_value = expected_df
            
            result = db.execute_query("SELECT * FROM test")
            
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 3
    
    @patch('src.utils.database.create_engine')
    def test_get_tables(self, mock_create_engine):
        """Test getting table list."""
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        db = DatabaseManager()
        
        with patch('src.utils.database.inspect') as mock_inspect:
            mock_inspector = Mock()
            mock_inspector.get_table_names.return_value = ['table1', 'table2']
            mock_inspect.return_value = mock_inspector
            
            tables = db.get_tables()
            
            assert tables == ['table1', 'table2']
