"""Database factory for creating database connections for different types."""

from typing import Optional, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from ..config import config


def get_database_engine(
    database_type: Optional[str] = None,
    connection_url: Optional[str] = None,
    **kwargs
) -> Engine:
    """Get database engine based on database type.
    
    Args:
        database_type: Type of database (sqlite, postgresql, mysql, duckdb, etc.)
        connection_url: Connection URL (overrides auto-generation)
        **kwargs: Additional engine-specific arguments
        
    Returns:
        SQLAlchemy Engine instance
        
    Raises:
        ValueError: If database type is not supported or credentials are missing
    """
    database_type = database_type or config.database_type
    
    # Use provided URL or generate from config
    if connection_url:
        return create_engine(connection_url, **kwargs)
    
    if database_type == "sqlite":
        return _get_sqlite_engine(**kwargs)
    elif database_type == "postgresql":
        return _get_postgresql_engine(**kwargs)
    elif database_type == "mysql":
        return _get_mysql_engine(**kwargs)
    elif database_type == "duckdb":
        return _get_duckdb_engine(**kwargs)
    elif database_type == "snowflake":
        return _get_snowflake_engine(**kwargs)
    elif database_type == "redshift":
        return _get_redshift_engine(**kwargs)
    elif database_type == "bigquery":
        return _get_bigquery_engine(**kwargs)
    else:
        raise ValueError(
            f"Unsupported database type: {database_type}. "
            f"Supported types: sqlite, postgresql, mysql, duckdb, snowflake, redshift, bigquery"
        )


def _get_sqlite_engine(**kwargs) -> Engine:
    """Get SQLite engine."""
    return create_engine(config.database_url, **kwargs)


def _get_postgresql_engine(**kwargs) -> Engine:
    """Get PostgreSQL engine."""
    return create_engine(config.database_url, **kwargs)


def _get_mysql_engine(**kwargs) -> Engine:
    """Get MySQL engine."""
    return create_engine(config.database_url, **kwargs)


def _get_duckdb_engine(**kwargs) -> Engine:
    """Get DuckDB engine."""
    try:
        import duckdb_engine
    except ImportError:
        raise ImportError(
            "DuckDB support requires duckdb-engine. "
            "Install it with: pip install duckdb-engine"
        )
    
    return create_engine(config.database_url, **kwargs)


def _get_snowflake_engine(**kwargs) -> Engine:
    """Get Snowflake engine."""
    try:
        import snowflake.sqlalchemy
    except ImportError:
        raise ImportError(
            "Snowflake support requires snowflake-sqlalchemy. "
            "Install it with: pip install snowflake-sqlalchemy"
        )
    
    # Build Snowflake connection URL
    if config.database_url and "snowflake" in config.database_url:
        return create_engine(config.database_url, **kwargs)
    
    # Build from individual parameters
    if not all([
        config.snowflake_account,
        config.snowflake_user,
        config.snowflake_password,
        config.snowflake_database
    ]):
        raise ValueError("Snowflake credentials incomplete in configuration")
    
    connection_url = (
        f"snowflake://{config.snowflake_user}:{config.snowflake_password}"
        f"@{config.snowflake_account}/{config.snowflake_database}"
    )
    
    if config.snowflake_schema:
        connection_url += f"/{config.snowflake_schema}"
    
    if config.snowflake_warehouse:
        connection_url += f"?warehouse={config.snowflake_warehouse}"
    
    return create_engine(connection_url, **kwargs)


def _get_redshift_engine(**kwargs) -> Engine:
    """Get Amazon Redshift engine."""
    try:
        import redshift_connector
    except ImportError:
        raise ImportError(
            "Redshift support requires redshift-connector. "
            "Install it with: pip install redshift-connector sqlalchemy-redshift"
        )
    
    return create_engine(config.database_url, **kwargs)


def _get_bigquery_engine(**kwargs) -> Engine:
    """Get Google BigQuery engine."""
    try:
        from sqlalchemy_bigquery import BigQueryDialect
    except ImportError:
        raise ImportError(
            "BigQuery support requires sqlalchemy-bigquery. "
            "Install it with: pip install sqlalchemy-bigquery"
        )
    
    if not config.bigquery_project:
        raise ValueError("BIGQUERY_PROJECT not set in configuration")
    
    # BigQuery connection URL format
    connection_url = f"bigquery://{config.bigquery_project}"
    
    # Set credentials path if provided
    if config.bigquery_credentials_path:
        import os
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config.bigquery_credentials_path
    
    return create_engine(connection_url, **kwargs)


def get_database_info() -> Dict[str, Any]:
    """Get information about the configured database.
    
    Returns:
        Dictionary with database type and connection details
    """
    return {
        "type": config.database_type,
        "url": config.database_url if config.database_type in ["sqlite", "postgresql", "mysql", "duckdb"] else "[REDACTED]",
        "supports_transactions": config.database_type in ["postgresql", "mysql", "sqlite"],
        "supports_parallel": config.database_type in ["snowflake", "redshift", "bigquery"],
        "is_cloud": config.database_type in ["snowflake", "redshift", "bigquery"]
    }
