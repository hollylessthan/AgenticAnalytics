"""Utility functions."""

import os
import json
from typing import Any, Dict
from datetime import datetime


def ensure_dir(directory: str) -> None:
    """Ensure directory exists, create if it doesn't.
    
    Args:
        directory: Directory path
    """
    os.makedirs(directory, exist_ok=True)


def save_json(data: Any, filepath: str) -> None:
    """Save data as JSON file.
    
    Args:
        data: Data to save
        filepath: Path to save file
    """
    ensure_dir(os.path.dirname(filepath))
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_json(filepath: str) -> Any:
    """Load data from JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded data
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def timestamp() -> str:
    """Get current timestamp string.
    
    Returns:
        Timestamp string
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def format_dataframe_for_display(df, max_rows: int = 10) -> str:
    """Format DataFrame for display.
    
    Args:
        df: pandas DataFrame
        max_rows: Maximum rows to display
        
    Returns:
        Formatted string
    """
    if len(df) > max_rows:
        return f"{df.head(max_rows).to_string()}\n\n... ({len(df) - max_rows} more rows)"
    return df.to_string()
