"""Example: Using different database systems."""

import os
from dotenv import load_dotenv

load_dotenv()

from src.utils.database import DatabaseManager
from src.utils.database_factory import get_database_info


def test_database(db_type: str, connection_url: str):
    """Test a specific database connection.
    
    Args:
        db_type: Type of database
        connection_url: Connection URL
    """
    print(f"\n{'=' * 60}")
    print(f"Testing {db_type.upper()} Database")
    print('=' * 60)
    
    try:
        # Create database manager
        db = DatabaseManager(database_url=connection_url, database_type=db_type)
        print(f"✅ Successfully connected to {db_type}")
        
        # Get database info
        info = get_database_info()
        print(f"\nDatabase Info:")
        print(f"  Type: {info['type']}")
        print(f"  Cloud: {info['is_cloud']}")
        print(f"  Parallel: {info['supports_parallel']}")
        
        # Get tables
        tables = db.get_tables()
        print(f"\n📊 Tables ({len(tables)}):")
        for table in tables[:5]:  # Show first 5
            print(f"  - {table}")
        if len(tables) > 5:
            print(f"  ... and {len(tables) - 5} more")
        
        # Test query
        if tables:
            query = f"SELECT * FROM {tables[0]} LIMIT 3"
            print(f"\n📝 Test Query: {query}")
            result = db.execute_query(query)
            print(f"✅ Retrieved {len(result)} rows")
            print(result.to_string())
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def main():
    """Test different database systems."""
    
    print("=" * 60)
    print("Multi-Database Example")
    print("=" * 60)
    
    # Test configurations
    databases = []
    
    # SQLite
    if os.path.exists("data/analytics.db"):
        databases.append(("sqlite", "sqlite:///./data/analytics.db"))
    
    # PostgreSQL
    if os.getenv("POSTGRES_URL"):
        databases.append(("postgresql", os.getenv("POSTGRES_URL")))
    
    # MySQL
    if os.getenv("MYSQL_URL"):
        databases.append(("mysql", os.getenv("MYSQL_URL")))
    
    # DuckDB
    if os.getenv("DUCKDB_URL"):
        databases.append(("duckdb", os.getenv("DUCKDB_URL")))
    
    # Snowflake
    if os.getenv("SNOWFLAKE_ACCOUNT"):
        databases.append(("snowflake", None))  # Will use config params
    
    # Redshift
    if os.getenv("REDSHIFT_URL"):
        databases.append(("redshift", os.getenv("REDSHIFT_URL")))
    
    # BigQuery
    if os.getenv("BIGQUERY_PROJECT"):
        databases.append(("bigquery", None))  # Will use config params
    
    if not databases:
        print("\n⚠️ No databases configured!")
        print("\nTo test databases, set connection URLs in .env:")
        print("  - SQLite: Run 'python examples/create_sample_db.py'")
        print("  - PostgreSQL: POSTGRES_URL=postgresql://user:pass@localhost/db")
        print("  - MySQL: MYSQL_URL=mysql://user:pass@localhost/db")
        print("  - DuckDB: DUCKDB_URL=duckdb:///path/to/db.duckdb")
        print("  - Snowflake: Set SNOWFLAKE_* environment variables")
        print("  - Redshift: REDSHIFT_URL=redshift+psycopg2://...")
        print("  - BigQuery: BIGQUERY_PROJECT=your-project-id")
        return
    
    # Test each configured database
    for db_type, connection_url in databases:
        test_database(db_type, connection_url)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("Summary")
    print('=' * 60)
    print(f"Tested {len(databases)} database(s):")
    for db_type, _ in databases:
        print(f"  ✓ {db_type.upper()}")


if __name__ == "__main__":
    main()
