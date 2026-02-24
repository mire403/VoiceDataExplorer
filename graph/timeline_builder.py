"""
Timeline builder: Event Timeline (not a flat text list).
Elements: time point, event summary, original speech position (seconds).
"""
from __future__ import annotations

from ..schemas import EventGraphData, ExtractedEvent, TimelineEntry, Utterance
from .event_graph import utterance_by_id


def build_timeline(
    graph: EventGraphData,
    utterances: list[Utterance] | None = None,
) -> list[TimelineEntry]:
    """
    Build a chronological timeline: each entry has time_seconds, event_summary, event_type, event_id, source_utterance.
    Time is taken from the source utterance start (seconds).
    """
    utterances = utterances or graph.utterances
    utt_map = {u.utterance_id: u for u in utterances}

    entries: list[TimelineEntry] = []
    for ev in graph.events:
        u = utt_map.get(ev.source_utterance)
        start_sec = u.start if u else 0.0
        entries.append(
            TimelineEntry(
                time_seconds=start_sec,
                event_summary=ev.content,
                event_type=ev.type,
                event_id=ev.event_id,
                source_utterance=ev.source_utterance,
                entities=list(ev.entities),
            )
        )

    entries.sort(key=lambda x: (x.time_seconds, x.event_id))
    return entries


def timeline_by_meeting(
    graph: EventGraphData,
    meeting_date: str | None = None,
) -> list[TimelineEntry]:
    """
    Same as build_timeline; meeting_date reserved for future multi-meeting (filter by date).
    """
    return build_timeline(graph, graph.utterances)
