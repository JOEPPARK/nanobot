"""Message complexity classifier for smart model routing.

Classifies incoming messages by trailing question marks:
- ???  → opus (highest capability)
- ??   → sonnet (mid capability)
- else → default model
"""

from __future__ import annotations

import re
from enum import Enum

from loguru import logger


class ComplexityTier(str, Enum):
    """Message complexity tiers mapped to model capability levels."""

    DEFAULT = "default"
    SONNET = "sonnet"
    OPUS = "opus"


_TRAILING_QM = re.compile(r"\?{2,}\s*$")


def classify_message(content: str) -> ComplexityTier:
    """Classify a message by counting trailing question marks.

    - ??? (3+) → OPUS
    - ??  (2)  → SONNET
    - otherwise → DEFAULT (use config default model)
    """
    if not content or not content.strip():
        return ComplexityTier.DEFAULT

    text = content.rstrip()

    m = _TRAILING_QM.search(text)
    if not m:
        logger.debug("Classified as DEFAULT (no trailing ??)")
        return ComplexityTier.DEFAULT

    qm_count = m.group().count("?")

    if qm_count >= 3:
        logger.debug("Classified as OPUS (trailing {} question marks)", qm_count)
        return ComplexityTier.OPUS

    if qm_count == 2:
        logger.debug("Classified as SONNET (trailing ?? )")
        return ComplexityTier.SONNET

    logger.debug("Classified as DEFAULT")
    return ComplexityTier.DEFAULT


# Model indicator suffixes
MODEL_INDICATORS: dict[ComplexityTier, str] = {
    ComplexityTier.DEFAULT: "",
    ComplexityTier.SONNET: "(s)",
    ComplexityTier.OPUS: "(o)",
}

# Fallback order: opus -> sonnet -> default
FALLBACK_ORDER: dict[ComplexityTier, ComplexityTier | None] = {
    ComplexityTier.OPUS: ComplexityTier.SONNET,
    ComplexityTier.SONNET: ComplexityTier.DEFAULT,
    ComplexityTier.DEFAULT: None,
}

# Model pricing per 1M tokens (input, output) in USD
MODEL_PRICING: dict[str, tuple[float, float]] = {
    "haiku": (1.0, 5.0),
    "sonnet": (3.0, 15.0),
    "opus": (15.0, 75.0),
}


def _detect_pricing_key(model: str) -> str | None:
    """Detect pricing key from model name (e.g. 'anthropic/claude-sonnet-4-5' -> 'sonnet')."""
    model_lower = model.lower()
    for key in MODEL_PRICING:
        if key in model_lower:
            return key
    return None


def format_token_usage(
    input_tokens: int, output_tokens: int, model: str,
) -> str:
    """Format token usage line with optional cost estimate.

    Returns e.g. '📊 in: 2,521 / out: 1,843 / $0.05'
    """
    parts = [f"📊 in: {input_tokens:,} / out: {output_tokens:,}"]
    pricing_key = _detect_pricing_key(model)
    if pricing_key:
        inp_price, out_price = MODEL_PRICING[pricing_key]
        cost = (input_tokens * inp_price + output_tokens * out_price) / 1_000_000
        parts.append(f"${cost:.2f}")
    return " / ".join(parts)
