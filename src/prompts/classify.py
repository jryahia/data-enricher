"""Classification prompt templates."""

CLASSIFY_SYSTEM = "You are a business classifier. Return only the category name, nothing else."


def classify_prompt(value: str, categories: str = None) -> str:
    """Generate a classification prompt for a given value."""
    if categories:
        return (
            f"Classify this item into one of the following categories: {categories}. "
            f"Return only the category name. Data: {value}"
        )
    return (
        "Classify this business into one of: Technology, Healthcare, Finance, "
        "Education, E-commerce, Other. Return only the category name. Data: {value}"
    ).format(value=value)
