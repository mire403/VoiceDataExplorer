"""
VoiceDataExplorer — End-to-end pipeline.
Audio → STT → Segmentation → Event/Entity/Relation extraction → Graph → Timeline & Query.
All outputs are structured (JSON); every event traces to original speech timestamps.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from voice_data_explorer.audio import transcribe_audio
from voice_data_explorer.audio.transcribe import save_transcription
from voice_data_explorer.extraction import extract_entities, extract_events, extract_relations
from voice_data_explorer.graph import build_event_graph, build_timeline
from voice_data_explorer.output import render_timeline_html, render_timeline_markdown
from voice_data_explorer.query import (
    query_kpi_decisions,
    query_kpi_mentions_trend,
    query_risks_without_decision,
    run_query,
)
from voice_data_explorer.segmentation import segment_utterances


def main() -> None:
    parser = argparse.ArgumentParser(
        description="VoiceDataExplorer — Voice-First Data Explorer. Transforms speech into structured, queryable data."
    )
    parser.add_argument("--audio", "-a", required=True, help="Path to audio file (wav/mp3)")
    parser.add_argument("--output-dir", "-o", default="./output", help="Output directory for JSON, MD, HTML")
    parser.add_argument("--use-whisperx", action="store_true", help="Use WhisperX (speaker + alignment)")
    parser.add_argument("--device", default="cpu", choices=("cpu", "cuda"), help="Device for STT")
    parser.add_argument("--skip-llm", action="store_true", help="Skip extraction (only transcribe + segment); no OPENAI_API_KEY needed")
    parser.add_argument("--query", "-q", help="Run a voice-first query after pipeline (e.g. 'KPI decisions', 'risks without decision')")
    args = parser.parse_args()

    audio_path = Path(args.audio)
    if not audio_path.exists():
        raise SystemExit(f"Audio file not found: {audio_path}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1) Speech layer
    print("Transcribing...")
    transcription = transcribe_audio(
        audio_path,
        device=args.device,
        use_whisperx=args.use_whisperx,
    )
    save_transcription(transcription, out_dir / "transcription.json")
    print(f"  Utterances: {len(transcription.utterances)}")

    # 2) Segmentation
    segmented = segment_utterances(transcription)
    utterances = segmented.utterances

    if args.skip_llm:
        print("Skipping extraction (--skip-llm). Output: transcription + segmentation only.")
        with open(out_dir / "utterances.json", "w", encoding="utf-8") as f:
            json.dump([u.model_dump() for u in utterances], f, ensure_ascii=False, indent=2)
        return

    # 3) Event extraction
    print("Extracting events...")
    events = extract_events(utterances)
    print(f"  Events: {len(events)}")

    # 4) Entity extraction
    print("Extracting entities...")
    entities = extract_entities(events)
    print(f"  Entities: {len(entities)}")

    # 5) Relation extraction
    print("Extracting relations...")
    relations = extract_relations(events, entities)
    print(f"  Relations: {len(relations)}")

    # 6) Graph
    graph = build_event_graph(events, entities, relations, utterances)
    with open(out_dir / "event_graph.json", "w", encoding="utf-8") as f:
        # Pydantic model_dump for EventGraphData
        data = {
            "events": [e.model_dump() for e in graph.events],
            "entities": [e.model_dump() for e in graph.entities],
            "relations": [r.model_dump() for r in graph.relations],
            "utterances": [u.model_dump() for u in graph.utterances],
        }
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 7) Timeline
    timeline = build_timeline(graph)
    md = render_timeline_markdown(
        timeline,
        meeting_title=audio_path.stem,
        meeting_date=None,
    )
    (out_dir / "timeline.md").write_text(md, encoding="utf-8")
    html = render_timeline_html(
        timeline,
        meeting_title=audio_path.stem,
        meeting_date=None,
    )
    (out_dir / "timeline.html").write_text(html, encoding="utf-8")
    print(f"  Timeline: {len(timeline)} entries -> timeline.md, timeline.html")

    # 8) Optional query
    if args.query:
        result = run_query(graph, args.query)
        q_md = f"# Query: {args.query}\n\n"
        q_md += f"Meta: {result.meta}\n\n"
        for e in result.timeline_entries:
            m = int(e.time_seconds) // 60
            s = int(e.time_seconds) % 60
            q_md += f"- ⏱️ {m:02d}:{s:02d} **{e.event_type}**: {e.event_summary}\n"
        (out_dir / "query_result.md").write_text(q_md, encoding="utf-8")
        print(f"  Query result: {len(result.events)} events -> query_result.md")

    print("Done. Output directory:", out_dir.resolve())


if __name__ == "__main__":
    main()
