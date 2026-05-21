"""Description prompt templates."""

DESCRIBE_SYSTEM = "You are a professional business writer. Write concise, one-sentence descriptions."


def describe_prompt(value: str) -> str:
    """Generate a description prompt."""
    return (
        "Write a one-sentence professional description for this business. "
        "Keep it concise and informative. Data: {value}"
    ).format(value=value)
