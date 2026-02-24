"""
Markdown timeline output.
Format: ### Meeting | time | **Type**: content (trace to seconds).
"""
from __future__ import annotations

from ..schemas import TimelineEntry


def _sec_to_mm_ss(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def render_timeline_markdown(
    entries: list[TimelineEntry],
    meeting_title: str = "Meeting",
    meeting_date: str | None = None,
) -> str:
    """
    Render timeline as Markdown.
    Example:
      ### 2024-01-12 | Client Meeting
      - ⏱️ 05:12 **Decision**: Increase retention KPI by 5%
      - ⏱️ 18:40 **Concern**: Risk of churn in SMB segment
    """
    lines = []
    header = meeting_title
    if meeting_date:
        header = f"{meeting_date} | {meeting_title}"
    lines.append(f"### {header}")
    lines.append("")
    for e in entries:
        time_str = _sec_to_mm_ss(e.time_seconds)
        lines.append(f"- ⏱️ {time_str}  **{e.event_type}**: {e.event_summary}")
    return "\n".join(lines)


def render_query_result_markdown(
    entries: list[TimelineEntry],
    query_name: str,
    meta: dict | None = None,
) -> str:
    """Render query result timeline as Markdown with a header."""
    lines = [f"## Query: {query_name}", ""]
    if meta:
        lines.append(f"*Meta: {meta}*")
        lines.append("")
    for e in entries:
        time_str = _sec_to_mm_ss(e.time_seconds)
        lines.append(f"- ⏱️ {time_str}  **{e.event_type}**: {e.event_summary}")
    return "\n".join(lines)
