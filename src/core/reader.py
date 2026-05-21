"""Read CSV, JSON, or plain text files."""
import csv
import json
import io
from pathlib import Path
from typing import List, Dict, Any, Optional, Union


def read_csv(filepath: Union[str, Path]) -> List[Dict[str, str]]:
    """Read a CSV file and return a list of dicts."""
    path = Path(filepath)
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append({k.strip(): v.strip() if v else "" for k, v in row.items()})
    return rows


def read_json(filepath: Union[str, Path]) -> List[Dict[str, Any]]:
    """Read a JSON file (list of objects or single object)."""
    path = Path(filepath)
    with open(path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    raise ValueError("JSON must be an object or array of objects")


def read_text(filepath: Union[str, Path]) -> List[Dict[str, str]]:
    """Read a plain text file, one row per line."""
    path = Path(filepath)
    with open(path, "r", encoding="utf-8-sig") as f:
        lines = [line.strip() for line in f if line.strip()]
    return [{"text": line} for line in lines]


def read_file(filepath: Union[str, Path]) -> List[Dict[str, Any]]:
    """Auto-detect format and read file."""
    path = Path(filepath)
    ext = path.suffix.lower()
    if ext == ".csv":
        return read_csv(path)
    elif ext == ".json":
        return read_json(path)
    elif ext == ".txt":
        return read_text(path)
    else:
        # Try CSV first, then JSON, then plain text
        try:
            return read_csv(path)
        except Exception:
            pass
        try:
            return read_json(path)
        except Exception:
            pass
        return read_text(path)


def read_from_string(content: str, fmt: str = "csv") -> List[Dict[str, Any]]:
    """Read data from a string."""
    if fmt == "csv":
        reader = csv.DictReader(io.StringIO(content))
        return [{k.strip(): v.strip() if v else "" for k, v in row.items()} for row in reader]
    elif fmt == "json":
        data = json.loads(content)
        if isinstance(data, dict):
            return [data]
        return data
    else:
        return [{"text": line.strip()} for line in content.strip().split("\n") if line.strip()]
