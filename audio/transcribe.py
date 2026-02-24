"""
Speech-to-Text: Whisper / WhisperX.
Output: standardized JSON with text, speaker (if available), start_time, end_time.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Literal

from ..schemas import TranscriptionResult, Utterance


def _utterance_id() -> str:
    return f"utt_{uuid.uuid4().hex[:12]}"


def transcribe_audio(
    audio_path: str | Path,
    model_size: str = "base",
    device: str = "cpu",
    use_whisperx: bool = False,
) -> TranscriptionResult:
    """
    Transcribe audio to standardized utterances.
    Prefer WhisperX when available (speaker + word-level timestamps).
    Fallback: Whisper segment-level timestamps, speaker = "Unknown".
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {path}")

    if use_whisperx:
        return transcribe_audio_whisperx(str(path), device=device)
    return transcribe_audio_whisper(str(path), model_size=model_size, device=device)


def transcribe_audio_whisper(
    audio_path: str,
    model_size: str = "base",
    device: str = "cpu",
) -> TranscriptionResult:
    """Whisper-only: segment-level timestamps, no speaker diarization."""
    try:
        import whisper
    except ImportError:
        raise ImportError("Install openai-whisper: pip install openai-whisper")

    model = whisper.load_model(model_size, device=device)
    result = model.transcribe(audio_path, word_timestamps=False)

    utterances: list[Utterance] = []
    segments = result.get("segments") or []

    for i, seg in enumerate(segments):
        start = float(seg.get("start", 0))
        end = float(seg.get("end", start))
        text = (seg.get("text") or "").strip()
        if not text:
            continue
        utterances.append(
            Utterance(
                utterance_id=_utterance_id(),
                speaker="Unknown",
                start=start,
                end=end,
                text=text,
            )
        )

    return TranscriptionResult(source_file=audio_path, utterances=utterances)


def transcribe_audio_whisperx(
    audio_path: str,
    device: str = "cpu",
    batch_size: int = 16,
) -> TranscriptionResult:
    """
    WhisperX: alignment + optional diarization → speaker + precise timestamps.
    Output format: utterance_id, speaker, start, end, text.
    Falls back to segments-only if align/diarization unavailable.
    """
    try:
        import whisperx
        import torch
    except ImportError:
        raise ImportError("Install whisperx and torch: pip install whisperx torch")

    if device == "cuda" and not torch.cuda.is_available():
        device = "cpu"

    model = whisperx.load_model("base", device, compute_type="float32")
    audio = whisperx.load_audio(audio_path)
    transcribe_result = model.transcribe(audio, batch_size=batch_size)
    segments = transcribe_result.get("segments") or []

    # Optional alignment (improves timestamps)
    try:
        model_align, metadata = whisperx.load_align_model(
            language_code=transcribe_result.get("language", "en"),
            device=device,
        )
        aligned = whisperx.align(
            segments,
            model_align,
            metadata,
            audio,
            device,
            return_char_alignments=False,
        )
        segments = aligned.get("segments") or segments
    except Exception:
        pass

    # Optional diarization (requires extra model). If not run, use "Unknown".
    try:
        diarize_model = whisperx.DiarizationPipeline(use_auth_token=None, device=device)
        diarize_segments = diarize_model(audio)
        segments = whisperx.assign_word_speakers(diarize_segments, {"segments": segments}).get("segments", segments)
    except Exception:
        pass

    utterances: list[Utterance] = []
    for i, seg in enumerate(segments):
        start = float(seg.get("start", 0))
        end = float(seg.get("end", start))
        text = (seg.get("text") or "").strip()
        speaker = seg.get("speaker") or "Unknown"
        if isinstance(speaker, int):
            speaker = f"Speaker {speaker}"
        if not text:
            continue
        utterances.append(
            Utterance(
                utterance_id=_utterance_id(),
                speaker=str(speaker),
                start=start,
                end=end,
                text=text,
            )
        )

    return TranscriptionResult(source_file=audio_path, utterances=utterances)


def save_transcription(result: TranscriptionResult, out_path: str | Path) -> None:
    """Persist transcription as JSON."""
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)


def load_transcription(path: str | Path) -> TranscriptionResult:
    """Load transcription from JSON."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return TranscriptionResult.model_validate(data)
