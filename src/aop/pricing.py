"""Token estimation and cost calculation.

Prices are USD per 1M tokens (input, output). They are ILLUSTRATIVE defaults:
override them with a JSON file (AOP_PRICING_FILE) shaped like {"model-prefix": [in, out]}.
"""
import json
import os

DEFAULT_PRICES = {
    "mock": (0.0, 0.0),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "claude-haiku": (1.00, 5.00),
    "claude-sonnet": (3.00, 15.00),
    "claude-opus": (15.00, 75.00),
    "gemini-flash": (0.30, 2.50),
    "gemini-pro": (1.25, 10.00),
}


def load_prices():
    prices = dict(DEFAULT_PRICES)
    path = os.environ.get("AOP_PRICING_FILE")
    if path and os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for key, val in json.load(fh).items():
                prices[key] = (float(val[0]), float(val[1]))
    return prices


def estimate_tokens(text):
    """Rough estimate (~4 chars/token). Used only when the provider reports no usage."""
    return max(1, len(text or "") // 4)


def cost_usd(model, tokens_in, tokens_out, prices=None):
    prices = prices or DEFAULT_PRICES
    name = (model or "").lower()
    best = None
    for prefix in prices:
        if name.startswith(prefix) and (best is None or len(prefix) > len(best)):
            best = prefix
    if best is None:
        return 0.0
    p_in, p_out = prices[best]
    return (tokens_in * p_in + tokens_out * p_out) / 1_000_000
