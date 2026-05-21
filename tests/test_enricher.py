"""Tests for the enricher module."""
import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.enricher import Enricher
from src.core.columns import detect_name_columns, detect_text_columns, guess_enrichment_type
from src.llm.client import LLMConfig


def test_detect_name_columns():
    """Test name column detection."""
    headers = ["name", "company", "description", "country", "text"]
    names = detect_name_columns(headers)
    assert "name" in names
    assert "company" in names
    assert "description" not in names


def test_detect_text_columns():
    """Test text column detection."""
    headers = ["name", "description", "review", "country"]
    texts = detect_text_columns(headers)
    assert "description" in texts
    assert "review" in texts
    assert "name" not in texts


def test_guess_enrichment_type():
    """Test enrichment type guessing."""
    headers = ["name", "industry"]
    types = guess_enrichment_type(headers)
    assert "classify" in types
    assert "describe" in types

    headers = ["review", "feedback"]
    types = guess_enrichment_type(headers)
    assert "sentiment" in types


def test_estimate_cost():
    """Test cost estimation."""
    enricher = Enricher(llm_config=LLMConfig(api_key="test"))
    rows = [{"name": "Test Company Inc"}, {"name": "Another Corp"}]
    estimate = enricher.estimate_total_cost(rows, ["classify"], ["name"])
    assert estimate["rows"] == 2
    assert estimate["enrichments"] == 1
    assert estimate["estimated_total_cost"] > 0


if __name__ == "__main__":
    test_detect_name_columns()
    test_detect_text_columns()
    test_guess_enrichment_type()
    test_estimate_cost()
    print("✅ All enricher tests passed!")
