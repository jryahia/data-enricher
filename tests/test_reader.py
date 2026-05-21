"""Tests for the reader module."""
import os
import sys
import tempfile
import csv
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.reader import read_csv, read_json, read_text, read_file, read_from_string


def test_read_csv():
    """Test reading a CSV file."""
    content = "name,industry\nAcme Inc,Technology\nBeta Corp,Healthcare\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    rows = read_csv(path)
    assert len(rows) == 2
    assert rows[0]["name"] == "Acme Inc"
    assert rows[1]["industry"] == "Healthcare"
    os.unlink(path)


def test_read_json():
    """Test reading a JSON file."""
    data = [{"name": "Acme Inc", "industry": "Technology"}, {"name": "Beta Corp", "industry": "Healthcare"}]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f)
        path = f.name
    rows = read_json(path)
    assert len(rows) == 2
    assert rows[0]["name"] == "Acme Inc"
    os.unlink(path)


def test_read_text():
    """Test reading a plain text file."""
    content = "Acme Inc\nBeta Corp\nGamma LLC\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    rows = read_text(path)
    assert len(rows) == 3
    assert rows[0]["text"] == "Acme Inc"
    os.unlink(path)


def test_read_file_auto():
    """Test auto-detection of file format."""
    content = "name,industry\nAcme Inc,Technology\n"
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write(content)
        path = f.name
    rows = read_file(path)
    assert len(rows) == 1
    assert rows[0]["name"] == "Acme Inc"
    os.unlink(path)


def test_read_from_string():
    """Test reading from strings."""
    csv_data = "name,score\nAlice,95\nBob,87\n"
    rows = read_from_string(csv_data, fmt="csv")
    assert len(rows) == 2
    assert rows[0]["name"] == "Alice"

    json_data = '[{"name": "Acme", "value": 100}]'
    rows = read_from_string(json_data, fmt="json")
    assert len(rows) == 1
    assert rows[0]["name"] == "Acme"


if __name__ == "__main__":
    test_read_csv()
    test_read_json()
    test_read_text()
    test_read_file_auto()
    test_read_from_string()
    print("✅ All reader tests passed!")
