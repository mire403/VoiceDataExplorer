"""
Structured schemas for pipeline outputs.
Every step outputs JSON; events trace back to original timestamps.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# --- Speech layer ---


class Utterance(BaseModel):
    """Standardized utterance from STT (speaker + timestamp)."""
    utterance_id: str
    speaker: str
    start: float  # seconds
    end: float
    text: str


class TranscriptionResult(BaseModel):
    """Full transcription output."""
    source_file: str
    utterances: list[Utterance]


# --- Event extraction ---

EventType = Literal["Decision", "KPI_Mention", "Action_Item", "Risk", "Concern"]


class ExtractedEvent(BaseModel):
    """Single semantic event from an utterance."""
    event_id: str
    type: EventType
    content: str
    entities: list[str] = Field(default_factory=list)
    owner: Optional[str] = None
    time_ref: Optional[str] = None
    source_utterance: str


# --- Entity & relation ---

EntityType = Literal["KPI", "Person", "Project", "Client"]


class Entity(BaseModel):
    """Named entity with type."""
    entity_id: str
    type: EntityType
    name: str
    source_events: list[str] = Field(default_factory=list)


RelationType = Literal["mentions", "decides_on", "assigned_to", "depends_on"]


class Relation(BaseModel):
    """Explicit relation between event and entity (or event-event)."""
    from_id: str  # event or entity id
    to_id: str
    relation: RelationType


# --- Graph & timeline ---


class TimelineEntry(BaseModel):
    """Single entry on the event timeline."""
    time_seconds: float
    event_summary: str
    event_type: EventType
    event_id: str
    source_utterance: str
    entities: list[str] = Field(default_factory=list)


class EventGraphData(BaseModel):
    """Full graph: events, entities, relations."""
    events: list[ExtractedEvent]
    entities: list[Entity]
    relations: list[Relation]
    utterances: list[Utterance]
