"""Custom prompt handler with {column} placeholders."""
from typing import Dict, Any


def render_custom_prompt(template: str, row: Dict[str, Any]) -> str:
    """Render a custom prompt template by replacing {column_name} placeholders."""
    result = template
    for key, value in row.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, str(value))
    return result
