"""
Utterance segmentation: normalize / merge / split utterances.
Input: TranscriptionResult (from Whisper/WhisperX).
Output: Same schema; may merge short segments or split long ones for extraction.
"""
from __future__ import annotations

from ..schemas import TranscriptionResult, Utterance


# MVP: pass-through with optional normalization (min/max duration, merge same speaker).
MIN_UTTERANCE_SEC = 1.0   # skip very short fragments
MAX_UTTERANCE_SEC = 45.0  # split or cap for LLM context
MERGE_SAME_SPEAKER_GAP = 2.0  # merge if same speaker and gap < this


def segment_utterances(
    transcription: TranscriptionResult,
    min_sec: float = MIN_UTTERANCE_SEC,
    max_sec: float = MAX_UTTERANCE_SEC,
    merge_same_speaker_gap: float = MERGE_SAME_SPEAKER_GAP,
) -> TranscriptionResult:
    """
    Normalize utterances: drop too-short, optionally merge same-speaker nearby.
    Does not split long segments in MVP (extraction handles chunks).
    """
    utterances = list(transcription.utterances)
    if not utterances:
        return transcription

    # Filter too short
    filtered = [u for u in utterances if (u.end - u.start) >= min_sec]
    if not filtered:
        filtered = utterances  # keep at least all

    # Optional merge: same speaker, gap <= merge_same_speaker_gap
    merged: list[Utterance] = []
    i = 0
    while i < len(filtered):
        u = filtered[i]
        current_start = u.start
        current_end = u.end
        texts = [u.text]
        j = i + 1
        while j < len(filtered):
            next_u = filtered[j]
            if next_u.speaker != u.speaker:
                break
            if next_u.start - current_end > merge_same_speaker_gap:
                break
            current_end = next_u.end
            texts.append(next_u.text)
            j += 1
        if len(texts) > 1:
            merged.append(
                Utterance(
                    utterance_id=u.utterance_id,
                    speaker=u.speaker,
                    start=current_start,
                    end=current_end,
                    text=" ".join(texts),
                )
            )
        else:
            merged.append(u)
        i = j

    return TranscriptionResult(
        source_file=transcription.source_file,
        utterances=merged,
    )
