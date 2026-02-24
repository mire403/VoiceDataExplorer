"""
Entity extraction: KPI, Person, Project, Client from events and utterances.
Stored with entity_id, type, name, source_events.
"""
from __future__ import annotations

import uuid
from collections import defaultdict
from typing import Literal

from ..schemas import Entity, EntityType, ExtractedEvent
from .llm_client import llm_extract

ENTITY_TYPES: list[EntityType] = ["KPI", "Person", "Project", "Client"]

SYSTEM_PROMPT = """You are an entity extractor. Given a list of event contents and mentioned entities,
output a JSON array of unique entities. Each entity:
- type: KPI | Person | Project | Client
- name: normalized name (e.g. "Retention KPI", "John", "Project Alpha")
- source_events: list of event_ids that mention this entity (use the exact event_id strings provided)

KPIs: metrics, numbers, targets (revenue, retention, churn, NPS, etc.).
Person: people named or referred to.
Project: projects, initiatives, products.
Client: clients, accounts, segments.

Output only a JSON array. No explanation. Deduplicate by normalized name."""


def _entity_id(name: str, etype: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in name)[:32]
    return f"{etype}_{safe}_{uuid.uuid4().hex[:6]}"


def extract_entities(
    events: list[ExtractedEvent],
    model: str = "gpt-4o-mini",
) -> list[Entity]:
    """
    From events, extract unique entities (KPI, Person, Project, Client).
    Relations to events are stored in source_events.
    """
    if not events:
        return []

    lines = []
    for e in events:
        line = f"event_id={e.event_id} | type={e.type} | content={e.content} | entities={e.entities}"
        lines.append(line)
    user_content = "\n".join(lines)

    raw = llm_extract(SYSTEM_PROMPT, user_content, model=model)
    if not isinstance(raw, list):
        raw = [raw] if isinstance(raw, dict) else []

    event_ids = {ev.event_id for ev in events}
    entities_by_key: dict[tuple[str, str], list[str]] = defaultdict(list)  # (name, type) -> event_ids

    for item in raw:
        if not isinstance(item, dict):
            continue
        etype = item.get("type")
        if etype not in ENTITY_TYPES:
            continue
        name = (item.get("name") or "").strip()
        if not name:
            continue
        source_events = item.get("source_events") or []
        source_events = [s for s in source_events if s in event_ids]
        if not source_events:
            # Infer from event content/entities
            for ev in events:
                if name.lower() in (ev.content or "").lower() or any(name.lower() in (x or "").lower() for x in (ev.entities or [])):
                    source_events.append(ev.event_id)
        source_events = list(dict.fromkeys(source_events))  # dedupe
        key = (name, etype)
        for eid in source_events:
            if eid not in entities_by_key[key]:
                entities_by_key[key].append(eid)

    result: list[Entity] = []
    for (name, etype), source_events in entities_by_key.items():
        result.append(
            Entity(
                entity_id=_entity_id(name, etype),
                type=etype,
                name=name,
                source_events=source_events,
            )
        )
    return result
