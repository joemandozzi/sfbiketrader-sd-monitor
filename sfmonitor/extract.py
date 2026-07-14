"""LLM-based extraction of bike-frame details out of free-text IG captions.

Captions are informal marketplace text ("posted for a friend, 58cm Bianchi
Volpe, downtube shifters, $400 obo") so a fixed keyword list would miss too
much -- an LLM call handles messy real-world phrasing instead.
"""
import json
import os
import re
from dataclasses import dataclass
from typing import List, Optional

from anthropic import Anthropic

# Claude sometimes wraps its JSON response in a markdown code fence despite
# being told not to -- strip ```json / ``` fences before parsing.
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

API_KEY_ENV_VAR = "ANTHROPIC_API_KEY"
MODEL = "claude-sonnet-5"

EXTRACTION_PROMPT = """You are extracting bike-frame-for-sale details from an \
Instagram marketplace caption. Read the caption below and return a JSON array \
of every distinct frame/bike mentioned as for sale. Each element must have \
these keys (use null when not mentioned): "brand", "model", "frame_size", \
"price", "condition". If the caption doesn't mention any frame for sale, \
return an empty array. Return ONLY the JSON array, no other text.

Caption:
{caption}"""


class ExtractConfigError(RuntimeError):
    """Raised when the Anthropic API key isn't configured."""


@dataclass
class FrameMention:
    brand: Optional[str]
    model: Optional[str]
    frame_size: Optional[str]
    price: Optional[str]
    condition: Optional[str]


def get_client() -> Anthropic:
    key = os.environ.get(API_KEY_ENV_VAR)
    if not key:
        raise ExtractConfigError(
            f"Set {API_KEY_ENV_VAR} to your Anthropic API key (see README.md for setup steps)."
        )
    return Anthropic(api_key=key)


def extract_frame_info(caption: str, client: Optional[Anthropic] = None) -> List[FrameMention]:
    if not caption.strip():
        return []
    client = client or get_client()
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": EXTRACTION_PROMPT.format(caption=caption)}],
    )
    # The model may emit a leading ThinkingBlock before its text response --
    # find the actual text block rather than assuming content[0] is it.
    text_block = next((block for block in response.content if block.type == "text"), None)
    if text_block is None:
        return []
    text = _CODE_FENCE_RE.sub("", text_block.text.strip()).strip()
    try:
        items = json.loads(text)
    except json.JSONDecodeError:
        return []
    return [
        FrameMention(
            brand=item.get("brand"),
            model=item.get("model"),
            frame_size=item.get("frame_size"),
            price=item.get("price"),
            condition=item.get("condition"),
        )
        for item in items
    ]
