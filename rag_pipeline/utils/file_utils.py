"""
File utilities
"""
import json
import os
from pathlib import Path
from typing import Any, Dict


def ensure_directory(path: str) -> Path:
    """
    Ensure a directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load JSON from file
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Loaded JSON data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """
    Save data to JSON file
    
    Args:
        data: Data to save
        file_path: Output file path
        indent: JSON indentation
    """
    # Ensure directory exists
    ensure_directory(os.path.dirname(file_path))
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)
