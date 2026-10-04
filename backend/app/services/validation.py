"""Evidence checks on the tutor LLM output (PLAN.md section 3). Any failure fails the turn's analysis."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Optional

from ..schemas.llm import TurnAnalysis
from ..topics import is_valid_topic

_QUOTES = str.maketrans({
    "‘": "'", "’": "'", "‚": "'", "‛": "'", "´": "'", "`": "'",
    "“": '"', "”": '"', "„": '"', "‟": '"', "«": '"', "»": '"',
})
_EDGE_PUNCT = " \t\n.,!?;:\"'()[]…-"


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """Normalise for matching (unify quotes, lower(), collapse whitespace) and map each output
    character back to its index in `text`. Umlauts and ß are kept: lower() never turns ß into ss."""
    out: list[str] = []
    index_map: list[int] = []
    prev_space = True  # drops leading whitespace
    for i, ch in enumerate(text):
        if ch.isspace():
            if not prev_space:
                out.append(" ")
                index_map.append(i)
            prev_space = True
            continue
        prev_space = False
        for low in ch.translate(_QUOTES).lower():
            out.append(low)
            index_map.append(i)
    if out and out[-1] == " ":
        out.pop()
        index_map.pop()
    return "".join(out), index_map


def normalize(text: str) -> str:
    return normalize_with_map(nfc(text))[0]


def _clean_quote(text: str) -> str:
    return normalize(text).strip(_EDGE_PUNCT)


def find_spans(transcript: str, quote: str) -> list[tuple[int, int]]:
    """All non-overlapping (start, end) spans of `quote` in `transcript` (both NFC), after normalisation."""
    norm_t, index_map = normalize_with_map(transcript)
    needle = _clean_quote(quote)
    if not needle:
        return []
    spans = []
    pos = norm_t.find(needle)
    while pos != -1:
        start = index_map[pos]
        end = index_map[pos + len(needle) - 1] + 1
        spans.append((start, end))
        pos = norm_t.find(needle, pos + len(needle))
    return spans


@dataclass
class ValidatedCorrection:
    llm_ref: str
    original: str  # transcript's actual text for the first matching span
    corrected: str
    corrected_sentence: str
    kind: str
    topic: str
    explanation: str
    highlight_start: Optional[int]  # only when the span is unique
    highlight_end: Optional[int]


@dataclass
class ValidatedAnalysis:
    corrections: list[ValidatedCorrection]
    spoken_ref: Optional[str]
    needs_clarification: bool
    reply: str


class AnalysisValidationError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def validate_analysis(analysis: TurnAnalysis, transcript: str, language: str) -> ValidatedAnalysis:
    transcript = nfc(transcript)
    errors: list[str] = []
    validated: list[ValidatedCorrection] = []
    seen_ids: set[str] = set()

    for c in analysis.corrections:
        label = f"correction {c.id!r}"
        if c.id in seen_ids:
            errors.append(f"{label}: duplicate id")
            continue
        seen_ids.add(c.id)
        if not is_valid_topic(c.topic, language):
            errors.append(f"{label}: topic {c.topic!r} is not in the {language} topic list")
        spans = find_spans(transcript, c.original)
        if not spans:
            errors.append(f"{label}: original {c.original!r} does not appear in the transcript")
        corrected_norm = _clean_quote(c.corrected)
        if not corrected_norm:
            errors.append(f"{label}: corrected is empty")
        elif corrected_norm not in normalize(c.corrected_sentence):
            errors.append(f"{label}: corrected_sentence must contain corrected")
        if spans and corrected_norm and corrected_norm == _clean_quote(c.original):
            errors.append(f"{label}: corrected is identical to original")
        if not spans:
            continue
        start, end = spans[0]
        unique = len(spans) == 1
        validated.append(ValidatedCorrection(
            llm_ref=c.id,
            original=transcript[start:end],
            corrected=c.corrected.strip(),
            corrected_sentence=c.corrected_sentence.strip(),
            kind=c.kind,
            topic=c.topic,
            explanation=c.explanation.strip(),
            highlight_start=start if unique else None,
            highlight_end=end if unique else None,
        ))

    spoken = analysis.spoken_correction_id
    if spoken is not None:
        target = next((c for c in analysis.corrections if c.id == spoken), None)
        if target is None:
            errors.append(f"spoken_correction_id {spoken!r} references no correction")
        elif target.kind != "error":
            errors.append(f"spoken_correction_id {spoken!r} must reference a kind=error correction")

    if not analysis.reply.strip():
        errors.append("reply is empty")

    if errors:
        raise AnalysisValidationError(errors)
    return ValidatedAnalysis(
        corrections=validated,
        spoken_ref=spoken,
        needs_clarification=analysis.needs_clarification,
        reply=analysis.reply.strip(),
    )
