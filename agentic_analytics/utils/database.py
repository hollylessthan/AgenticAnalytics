"""Database utility functions."""

import sqlite3
from typing import Dict, List


def get_schema_info(database_path: str) -> str:
    """Extract schema information from SQLite database.
    
    Args:
        database_path: Path to SQLite database file
        
    Returns:
        String representation of the database schema
    """
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema_parts = []
    
    for table in tables:
        table_name = table[0]
        
        # Validate table name to prevent SQL injection
        # Only allow alphanumeric and underscore characters
        if not table_name.replace('_', '').isalnum():
            continue
        
        # Get table schema (safe to use f-string after validation)
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        # Format table schema
        table_schema = [f"Table: {table_name}"]
        table_schema.append("Columns:")
        
        for col in columns:
            col_name = col[1]
            col_type = col[2]
            not_null = "NOT NULL" if col[3] else ""
            pk = "PRIMARY KEY" if col[5] else ""
            table_schema.append(f"  - {col_name} {col_type} {not_null} {pk}".strip())
        
        schema_parts.append("\n".join(table_schema))
    
    conn.close()
    
    return "\n\n".join(schema_parts)


def create_sample_database(database_path: str):
    """Create a sample database for testing.
    
    Args:
        database_path: Path where database should be created
    """
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            sale_date TEXT NOT NULL,
            revenue REAL NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            signup_date TEXT NOT NULL
        )
    """)
    
    # Insert sample data
    products_data = [
        (1, "Laptop", "Electronics", 999.99, 50),
        (2, "Mouse", "Electronics", 29.99, 200),
        (3, "Keyboard", "Electronics", 79.99, 150),
        (4, "Monitor", "Electronics", 299.99, 75),
        (5, "Desk Chair", "Furniture", 199.99, 40),
    ]
    
    cursor.executemany("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?)", products_data)
    
    sales_data = [
        (1, 1, 2, "2024-01-15", 1999.98),
        (2, 2, 5, "2024-01-16", 149.95),
        (3, 1, 1, "2024-01-17", 999.99),
        (4, 3, 3, "2024-01-18", 239.97),
        (5, 4, 2, "2024-01-19", 599.98),
        (6, 5, 1, "2024-01-20", 199.99),
        (7, 2, 10, "2024-01-21", 299.90),
        (8, 3, 2, "2024-01-22", 159.98),
    ]
    
    cursor.executemany("INSERT OR REPLACE INTO sales VALUES (?, ?, ?, ?, ?)", sales_data)
    
    customers_data = [
        (1, "John Doe", "john@example.com", "2024-01-01"),
        (2, "Jane Smith", "jane@example.com", "2024-01-05"),
        (3, "Bob Johnson", "bob@example.com", "2024-01-10"),
    ]
    
    cursor.executemany("INSERT OR REPLACE INTO customers VALUES (?, ?, ?, ?)", customers_data)
    
    conn.commit()
    conn.close()
