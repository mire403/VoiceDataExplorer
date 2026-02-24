"""
HTML timeline output: styled timeline with timestamps and event types.
"""
from __future__ import annotations

from ..schemas import TimelineEntry


def _sec_to_mm_ss(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def render_timeline_html(
    entries: list[TimelineEntry],
    meeting_title: str = "Meeting",
    meeting_date: str | None = None,
) -> str:
    """
    Render timeline as HTML with minimal inline styles.
    Each entry: time, type badge, summary.
    """
    header = meeting_title
    if meeting_date:
        header = f"{meeting_date} | {meeting_title}"

    rows = []
    for e in entries:
        time_str = _sec_to_mm_ss(e.time_seconds)
        rows.append(
            "    "
            + f'<li class="timeline-entry" data-time="{e.time_seconds:.1f}">'
            f'<span class="time">⏱️ {time_str}</span> '
            f'<span class="event-type event-{e.event_type.lower().replace(" ", "-")}">{e.event_type}</span>: '
            f'<span class="summary">{_escape(e.event_summary)}</span>'
            f"</li>"
        )
    body = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>VoiceDataExplorer — {_escape(header)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 1rem 2rem; max-width: 720px; }}
    h1 {{ font-size: 1.25rem; color: #333; }}
    .timeline {{ list-style: none; padding: 0; }}
    .timeline-entry {{ margin: 0.5rem 0; padding: 0.25rem 0; border-bottom: 1px solid #eee; }}
    .time {{ color: #666; font-variant-numeric: tabular-nums; margin-right: 0.5rem; }}
    .event-type {{ font-size: 0.75rem; font-weight: 600; padding: 0.1rem 0.4rem; border-radius: 4px; margin-right: 0.5rem; }}
    .event-decision {{ background: #d4edda; color: #155724; }}
    .event-kpi_mention {{ background: #cce5ff; color: #004085; }}
    .event-action_item {{ background: #fff3cd; color: #856404; }}
    .event-risk {{ background: #f8d7da; color: #721c24; }}
    .event-concern {{ background: #e2d5f1; color: #3d2a5c; }}
    .summary {{ color: #222; }}
  </style>
</head>
<body>
  <h1>{_escape(header)}</h1>
  <p><em>VoiceDataExplorer — voice-native analytical timeline. Every entry traces to original speech timestamps.</em></p>
  <ul class="timeline">
{body}
  </ul>
</body>
</html>"""


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def render_query_result_html(
    entries: list[TimelineEntry],
    query_name: str,
    meta: dict | None = None,
) -> str:
    """Render query result as HTML fragment (timeline list only)."""
    header = f"Query: {query_name}"
    if meta:
        header += f" — {meta.get('count', '')} results"
    return render_timeline_html(entries, meeting_title=header)
