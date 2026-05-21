"""Entity extraction prompt templates."""

EXTRACT_SYSTEM = "You are a named entity recognition system. Extract entities and return as JSON."


def extract_prompt(text: str) -> str:
    """Generate an extraction prompt."""
    return (
        "Extract key entities from this text: company names, people, dates, locations. "
        "Return as a JSON object with keys: companies, people, dates, locations. "
        "If none found, use empty arrays. Text: {text}"
    ).format(text=text)
