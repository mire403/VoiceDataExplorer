"""
Query engine: voice-first queries over the event graph.
1) Last week's meetings: all KPI decisions
2) A given KPI: discussion count and trend
3) Risks/concerns that did not become decisions
Implementation: event + entity filters; optional LLM for natural-language intent.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from ..schemas import EventGraphData, ExtractedEvent, Relation, TimelineEntry


@dataclass
class QueryResult:
    """Structured query result: events + optional timeline slice."""
    events: list[ExtractedEvent]
    timeline_entries: list[TimelineEntry]
    meta: dict[str, Any]


def _event_ids_linked_to_entity(
    graph: EventGraphData,
    entity_id: str,
    relation_types: list[str] | None = None,
) -> set[str]:
    """Event IDs that have relation to this entity (e.g. decides_on, mentions)."""
    relation_types = relation_types or ["mentions", "decides_on", "assigned_to", "depends_on"]
    out: set[str] = set()
    for r in graph.relations:
        if r.relation not in relation_types:
            continue
        if r.to_id == entity_id:
            out.add(r.from_id)
        if r.from_id == entity_id:
            out.add(r.to_id)
    return out


def _entity_by_name(graph: EventGraphData, name: str) -> list[str]:
    """Entity IDs whose name contains name (case-insensitive)."""
    name_lower = name.lower()
    return [e.entity_id for e in graph.entities if name_lower in e.name.lower()]


# --- Query 1: KPI decisions (e.g. "last week's meetings, all KPI decisions") ---


def query_kpi_decisions(
    graph: EventGraphData,
    event_type: str = "Decision",
    kpi_filter: bool = True,
    since_seconds: float | None = None,
) -> QueryResult:
    """
    All decisions that mention or relate to KPIs.
    If since_seconds set, only utterances with start >= (max_time - since_seconds).
    """
    decisions = [e for e in graph.events if e.type == event_type]
    if kpi_filter:
        kpi_entity_ids = {e.entity_id for e in graph.entities if e.type == "KPI"}
        event_ids_with_kpi = set()
        for r in graph.relations:
            if r.relation in ("mentions", "decides_on") and (r.to_id in kpi_entity_ids or r.from_id in kpi_entity_ids):
                event_ids_with_kpi.add(r.from_id if r.from_id in {x.event_id for x in graph.events} else r.to_id)
        decisions = [e for e in decisions if e.event_id in event_ids_with_kpi or any(ent in kpi_entity_ids for ent in (e.entities or []))]
        # Also include decisions whose content/entities overlap with KPI names
        kpi_names = {e.name.lower() for e in graph.entities if e.type == "KPI"}
        for e in graph.events:
            if e.type != event_type:
                continue
            if e.event_id in event_ids_with_kpi:
                continue
            if any(k in (e.content or "").lower() for k in kpi_names):
                decisions.append(e)
            if any(any(k in (x or "").lower() for k in kpi_names) for x in (e.entities or [])):
                if e not in decisions:
                    decisions.append(e)
    # Deduplicate
    seen = set()
    unique = []
    for e in decisions:
        if e.event_id not in seen:
            seen.add(e.event_id)
            unique.append(e)
    decisions = unique

    if since_seconds is not None and graph.utterances:
        max_t = max(u.end for u in graph.utterances)
        cutoff = max_t - since_seconds
        utt_ids_after = {u.utterance_id for u in graph.utterances if u.start >= cutoff}
        decisions = [e for e in decisions if e.source_utterance in utt_ids_after]

    timeline = _events_to_timeline_entries(graph, decisions)
    return QueryResult(events=decisions, timeline_entries=timeline, meta={"query": "kpi_decisions"})


# --- Query 2: KPI mention count and trend ---


def query_kpi_mentions_trend(
    graph: EventGraphData,
    kpi_name_or_id: str,
) -> QueryResult:
    """
    For a given KPI (name or entity_id): how many times mentioned, in which events, and over time (timeline).
    """
    entity_ids = _entity_by_name(graph, kpi_name_or_id)
    if not entity_ids and kpi_name_or_id in {e.entity_id for e in graph.entities}:
        entity_ids = [kpi_name_or_id]
    event_ids = set()
    for eid in entity_ids:
        event_ids |= _event_ids_linked_to_entity(graph, eid)
    events = [e for e in graph.events if e.event_id in event_ids]
    # Also events that mention this KPI in content/entities
    kpi_names = [e.name for e in graph.entities if e.entity_id in entity_ids or kpi_name_or_id.lower() in e.name.lower()]
    for e in graph.events:
        if e.event_id in event_ids:
            continue
        if any(k in (e.content or "").lower() for k in kpi_names):
            events.append(e)
        elif any(any(k in (x or "").lower() for k in kpi_names) for x in (e.entities or [])):
            events.append(e)
    seen = set()
    unique = [e for e in events if e.event_id not in seen and not seen.add(e.event_id)]
    timeline = _events_to_timeline_entries(graph, unique)
    return QueryResult(
        events=unique,
        timeline_entries=timeline,
        meta={"query": "kpi_mentions_trend", "kpi": kpi_name_or_id, "count": len(unique)},
    )


# --- Query 3: Risks/concerns without a decision ---


def query_risks_without_decision(
    graph: EventGraphData,
) -> QueryResult:
    """
    Risks and concerns that are not linked (by relation or same-utterance) to a Decision.
    """
    risk_events = [e for e in graph.events if e.type in ("Risk", "Concern")]
    decision_event_ids = {e.event_id for e in graph.events if e.type == "Decision"}
    # Decisions that "address" a risk: same utterance, or relation depends_on/decides_on
    addressed_risk_event_ids: set[str] = set()
    for r in graph.relations:
        if r.from_id in decision_event_ids and r.to_id in {e.event_id for e in risk_events}:
            addressed_risk_event_ids.add(r.to_id)
        if r.to_id in decision_event_ids and r.from_id in {e.event_id for e in risk_events}:
            addressed_risk_event_ids.add(r.from_id)
    utterance_to_events: dict[str, list[str]] = {}
    for e in graph.events:
        utterance_to_events.setdefault(e.source_utterance, []).append(e.event_id)
    for utt, ev_ids in utterance_to_events.items():
        has_decision = any(eid in decision_event_ids for eid in ev_ids)
        if has_decision:
            for eid in ev_ids:
                if eid in {e.event_id for e in risk_events}:
                    addressed_risk_event_ids.add(eid)
    without_decision = [e for e in risk_events if e.event_id not in addressed_risk_event_ids]
    timeline = _events_to_timeline_entries(graph, without_decision)
    return QueryResult(
        events=without_decision,
        timeline_entries=timeline,
        meta={"query": "risks_without_decision", "count": len(without_decision)},
    )


def _events_to_timeline_entries(graph: EventGraphData, events: list[ExtractedEvent]) -> list[TimelineEntry]:
    """Convert event list to timeline entries (with time from utterance)."""
    utt_map = {u.utterance_id: u for u in graph.utterances}
    entries = []
    for ev in events:
        u = utt_map.get(ev.source_utterance)
        start = u.start if u else 0.0
        entries.append(
            TimelineEntry(
                time_seconds=start,
                event_summary=ev.content,
                event_type=ev.type,
                event_id=ev.event_id,
                source_utterance=ev.source_utterance,
                entities=list(ev.entities) if ev.entities else [],
            )
        )
    entries.sort(key=lambda x: (x.time_seconds, x.event_id))
    return entries


# --- Natural-language entry point (rule + optional LLM) ---


def run_query(
    graph: EventGraphData,
    query_text: str,
    llm_disambiguate: bool = False,
) -> QueryResult:
    """
    Run one of the three query types based on query text.
    - "KPI decisions" / "decisions about KPI" / "last week ... KPI decisions" -> query_kpi_decisions
    - "KPI X mentioned" / "how often X" / "trend for X" -> query_kpi_mentions_trend(graph, "X")
    - "risks without decision" / "concerns not addressed" -> query_risks_without_decision
    """
    q = query_text.lower().strip()
    if "risk" in q and ("without" in q or "not addressed" in q or "unaddressed" in q):
        return query_risks_without_decision(graph)
    if "kpi" in q and ("decision" in q or "decide" in q):
        return query_kpi_decisions(graph)
    if "mention" in q or "trend" in q or "how often" in q or "discussed" in q:
        # Try to extract KPI name (simple: take first quoted or last token)
        words = q.replace("?", "").split()
        kpi_candidate = words[-1] if words else "KPI"
        for w in words:
            if w not in ("the", "a", "for", "about", "kpi", "mentions", "trend", "how", "often", "discussed"):
                kpi_candidate = w
                break
        return query_kpi_mentions_trend(graph, kpi_candidate)
    # Default: KPI decisions
    return query_kpi_decisions(graph)
