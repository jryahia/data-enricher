"""Auto-detect which columns to enrich."""
from typing import List, Dict, Any, Set


NAME_KEYWORDS = {"name", "title", "company", "business", "brand", "product", "organization", "org", "entity"}
DESC_KEYWORDS = {"description", "desc", "about", "summary", "overview", "details", "bio", "blurb"}
TEXT_KEYWORDS = {"text", "content", "comment", "review", "feedback", "message", "body", "tweet", "post"}


def detect_name_columns(headers: List[str]) -> List[str]:
    """Detect columns likely containing names/titles."""
    results = []
    for h in headers:
        hl = h.lower().strip()
        if hl in NAME_KEYWORDS or any(kw in hl for kw in NAME_KEYWORDS):
            results.append(h)
    return results


def detect_text_columns(headers: List[str]) -> List[str]:
    """Detect columns likely containing free text."""
    results = []
    for h in headers:
        hl = h.lower().strip()
        if hl in TEXT_KEYWORDS or hl in DESC_KEYWORDS or any(kw in hl for kw in TEXT_KEYWORDS) or any(kw in hl for kw in DESC_KEYWORDS):
            results.append(h)
    return results


def detect_all_columns(headers: List[str]) -> Dict[str, List[str]]:
    """Return categorized column names."""
    return {
        "name": detect_name_columns(headers),
        "text": detect_text_columns(headers),
        "other": [h for h in headers if h not in detect_name_columns(headers) and h not in detect_text_columns(headers)],
    }


def guess_enrichment_type(headers: List[str]) -> List[str]:
    """Guess appropriate enrichment types based on columns."""
    types = []
    if detect_name_columns(headers):
        types.append("classify")
        types.append("describe")
    if detect_text_columns(headers):
        types.append("sentiment")
        types.append("extract")
    return types if types else ["classify"]
