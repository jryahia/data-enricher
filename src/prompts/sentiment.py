"""Sentiment analysis prompt templates."""

SENTIMENT_SYSTEM = "You are a sentiment analyzer. Return exactly: positive, negative, or neutral."


def sentiment_prompt(text: str) -> str:
    """Generate a sentiment analysis prompt."""
    return (
        "Analyze the sentiment of this text. Return exactly one word: "
        "positive, negative, or neutral. Text: {text}"
    ).format(text=text)
