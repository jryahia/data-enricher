"""Tests for the exporter module."""
import os
import sys
import tempfile
import csv
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.exporter import export_csv, export_json, export_data


def test_export_csv():
    """Test CSV export."""
    data = [{"name": "Acme", "category": "Tech"}, {"name": "Beta", "category": "Health"}]
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8") as f:
        path = f.name
    result = export_csv(data, path)
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert len(rows) == 2
    assert rows[0]["name"] == "Acme"
    os.unlink(path)


def test_export_json():
    """Test JSON export."""
    data = [{"name": "Acme", "category": "Tech"}]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
        path = f.name
    result = export_json(data, path)
    with open(path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert len(loaded) == 1
    assert loaded[0]["name"] == "Acme"
    os.unlink(path)


def test_export_auto():
    """Test auto-format detection."""
    data = [{"name": "Test"}]
    result = export_data(data, "output.csv")
    assert result.endswith(".csv")
    os.unlink("output.csv")

    result = export_data(data, "output.json", fmt="json")
    assert result.endswith(".json")
    os.unlink("output.json")


if __name__ == "__main__":
    test_export_csv()
    test_export_json()
    test_export_auto()
    print("✅ All exporter tests passed!")
