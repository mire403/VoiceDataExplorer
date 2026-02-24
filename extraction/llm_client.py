"""
LLM client for extraction only (classification + extraction, no "memory").
Uses OpenAI API by default; can be swapped for other providers.
"""
from __future__ import annotations

import json
import os
from typing import Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


def get_client() -> Any:
    """Return OpenAI client if available and key set."""
    if OpenAI is None:
        raise ImportError("Install openai: pip install openai")
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("Set OPENAI_API_KEY for event/entity/relation extraction")
    return OpenAI(api_key=key)


def llm_extract(
    system_prompt: str,
    user_content: str,
    model: str = "gpt-4o-mini",
    temperature: float = 0.1,
) -> dict[str, Any] | list[Any]:
    """
    Call LLM for structured extraction. Expects JSON in response.
    Returns parsed JSON (dict or list).
    """
    client = get_client()
    response = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    )
    text = response.choices[0].message.content or ""
    text = text.strip()
    # Strip markdown code block if present
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)
