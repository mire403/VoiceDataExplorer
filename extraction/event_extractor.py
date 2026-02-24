"""
Semantic event extraction: LLM classifies and extracts events from utterances.
Event types: Decision, KPI_Mention, Action_Item, Risk, Concern.
Output: structured events with content, entities, owner, time_ref, source_utterance.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from ..schemas import ExtractedEvent, EventType, Utterance
from .llm_client import llm_extract

EVENT_TYPES: list[EventType] = [
    "Decision",
    "KPI_Mention",
    "Action_Item",
    "Risk",
    "Concern",
]

SYSTEM_PROMPT = """You are an extractor. For each utterance (labeled with [utterance_id]), output a JSON array of events.
Event types: Decision, KPI_Mention, Action_Item, Risk, Concern.
- Decision: a concrete decision or commitment made.
- KPI_Mention: any metric, KPI, or number mentioned (revenue, retention, churn, etc.).
- Action_Item: a task or action assigned or agreed.
- Risk: a risk or uncertainty raised.
- Concern: a worry or objection raised.

For each event output exactly:
- source_utterance: the utterance_id in brackets from the input (e.g. utt_abc123)
- type: one of the types above
- content: short phrase (what was said)
- entities: list of named things (KPIs, people, projects) mentioned
- owner: person responsible if mentioned, else null
- time_ref: time constraint if mentioned (e.g. "next quarter", "by Friday"), else null

Output only a JSON array. No explanation. If no events in an utterance, omit it. Every event must have source_utterance set to one of the given utterance IDs."""

def _event_id() -> str:
    return f"evt_{uuid.uuid4().hex[:12]}"


def extract_events_from_batch(
    utterances: list[Utterance],
    model: str = "gpt-4o-mini",
) -> list[ExtractedEvent]:
    """
    Call LLM on a batch of utterances; return flat list of events.
    Each event gets source_utterance from LLM or fallback to first utterance in batch.
    """
    if not utterances:
        return []

    valid_ids = {u.utterance_id for u in utterances}
    lines = []
    for u in utterances:
        lines.append(f"[{u.utterance_id}] {u.speaker}: {u.text}")
    user_content = "\n".join(lines)

    raw = llm_extract(SYSTEM_PROMPT, user_content, model=model)
    if not isinstance(raw, list):
        raw = [raw] if isinstance(raw, dict) else []

    events: list[ExtractedEvent] = []
    for e in raw:
        if not isinstance(e, dict):
            continue
        t = e.get("type")
        if t not in EVENT_TYPES:
            continue
        src = e.get("source_utterance")
        if src not in valid_ids:
            src = utterances[0].utterance_id if utterances else ""
        events.append(
            ExtractedEvent(
                event_id=_event_id(),
                type=t,
                content=e.get("content") or "",
                entities=e.get("entities") or [],
                owner=e.get("owner"),
                time_ref=e.get("time_ref"),
                source_utterance=src,
            )
        )
    return events


def extract_events(
    utterances: list[Utterance],
    batch_size: int = 10,
    model: str = "gpt-4o-mini",
) -> list[ExtractedEvent]:
    """
    Extract events from all utterances in batches.
    Every event traces back to source_utterance (and thus to timestamps).
    """
    all_events: list[ExtractedEvent] = []
    for i in range(0, len(utterances), batch_size):
        batch = utterances[i : i + batch_size]
        batch_events = extract_events_from_batch(batch, model=model)
        all_events.extend(batch_events)
    return all_events
