"""
Relation extraction: explicit relations between events and entities.
Relations: mentions, decides_on, assigned_to, depends_on.
Stored as { from, to, relation }.
"""
from __future__ import annotations

from ..schemas import Entity, ExtractedEvent, Relation, RelationType
from .llm_client import llm_extract

RELATION_TYPES: list[RelationType] = ["mentions", "decides_on", "assigned_to", "depends_on"]

SYSTEM_PROMPT = """You are a relation extractor. Given events and entities, output a JSON array of relations.
Each relation: { "from_id": "<event_id or entity_id>", "to_id": "<event_id or entity_id>", "relation": "<type>" }
Relation types: mentions, decides_on, assigned_to, depends_on.
- mentions: event mentions entity (or entity in event)
- decides_on: event is a decision about an entity (e.g. KPI)
- assigned_to: action/decision assigned to a person
- depends_on: event/action depends on another event or entity

Use only the exact event_id and entity_id strings provided. Output only a JSON array."""


def extract_relations(
    events: list[ExtractedEvent],
    entities: list[Entity],
    model: str = "gpt-4o-mini",
) -> list[Relation]:
    """
    Extract explicit relations: event -> entity, event -> event.
    Stored for graph and query (which KPI was decided on, who is assigned, etc.).
    """
    if not events and not entities:
        return []

    event_ids = {e.event_id for e in events}
    entity_ids = {e.entity_id for e in entities}
    valid_ids = event_ids | entity_ids

    lines = ["Events:"]
    for e in events:
        lines.append(f"  {e.event_id}: {e.type} | {e.content} | entities={e.entities} | owner={e.owner}")
    lines.append("Entities:")
    for e in entities:
        lines.append(f"  {e.entity_id}: {e.type} | {e.name}")
    user_content = "\n".join(lines)

    raw = llm_extract(SYSTEM_PROMPT, user_content, model=model)
    if not isinstance(raw, list):
        raw = [raw] if isinstance(raw, dict) else []

    relations: list[Relation] = []
    seen: set[tuple[str, str, str]] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        from_id = item.get("from_id") or item.get("from")
        to_id = item.get("to_id") or item.get("to")
        rel = item.get("relation")
        if from_id not in valid_ids or to_id not in valid_ids or rel not in RELATION_TYPES:
            continue
        key = (from_id, to_id, rel)
        if key in seen:
            continue
        seen.add(key)
        relations.append(Relation(from_id=from_id, to_id=to_id, relation=rel))
    return relations
