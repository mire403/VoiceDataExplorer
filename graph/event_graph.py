"""
Event graph: events, entities, relations as a queryable structure.
Explicit storage of: which event triggers which decision, which KPIs mentioned, etc.
"""
from __future__ import annotations

from ..schemas import Entity, EventGraphData, ExtractedEvent, Relation, Utterance


def build_event_graph(
    events: list[ExtractedEvent],
    entities: list[Entity],
    relations: list[Relation],
    utterances: list[Utterance],
) -> EventGraphData:
    """
    Build the full event graph: events, entities, relations, utterances.
    All relations are explicit (from_id, to_id, relation).
    """
    return EventGraphData(
        events=events,
        entities=entities,
        relations=relations,
        utterances=utterances,
    )


def utterance_by_id(utterances: list[Utterance], uid: str) -> Utterance | None:
    """Get utterance by utterance_id (for timestamp lookup)."""
    for u in utterances:
        if u.utterance_id == uid:
            return u
    return None


def events_by_utterance(graph: EventGraphData, utterance_id: str) -> list[ExtractedEvent]:
    """Events that originated from this utterance."""
    return [e for e in graph.events if e.source_utterance == utterance_id]


def entities_mentioned_in_event(graph: EventGraphData, event_id: str) -> list[Entity]:
    """Entities linked to this event via mentions/decides_on."""
    out: list[Entity] = []
    entity_ids = {r.to_id for r in graph.relations if r.from_id == event_id and r.to_id in {x.entity_id for x in graph.entities}}
    for e in graph.entities:
        if e.entity_id in entity_ids:
            out.append(e)
    return out
