"""Tutor prompt for one learner turn. Output contract: schemas/llm.py TurnAnalysis."""

from __future__ import annotations

import json

from ..languages import LANGUAGE_NAMES, SCENARIOS, TARGET_LANGUAGES
from ..topics import TOPICS

PROMPT_VERSION = "turn-v1"
CONTEXT_TURNS = 10

_EXAMPLE = {
    "corrections": [{
        "id": "c1",
        "original": "habe nach Berlin gegangen",
        "corrected": "bin nach Berlin gegangen",
        "corrected_sentence": "Ich bin nach Berlin gegangen.",
        "kind": "error",
        "topic": "de_perfekt_auxiliary",
        "explanation": "Verbs of movement like gehen form the Perfekt with sein.",
    }],
    "spoken_correction_id": "c1",
    "needs_clarification": False,
    "reply": "Schön! Was hast du in Berlin gemacht?",
}


def system_prompt(target_language: str, level: str, scenario: str, explanation_language: str) -> str:
    target = TARGET_LANGUAGES[target_language]
    explain = LANGUAGE_NAMES.get(explanation_language, explanation_language)
    topics = "\n".join(f"- {key}: {label}" for key, label in TOPICS[target_language].items())
    return f"""You are a friendly {target} tutor having a spoken conversation with a learner at CEFR level {level}.
Scenario: {SCENARIOS[scenario]}. Stay in the scenario and keep the conversation going.

For the learner's LAST message only:
1. Find ALL grammar and word-choice errors. The message is a speech-recognition transcript: ignore punctuation, capitalisation and spelling. Do not flag correct sentences or matters of style as errors.
2. For each error add a correction:
   - "original": the wrong words copied EXACTLY and contiguously from the learner's message (keep it short).
   - "corrected": the replacement for exactly those words.
   - "corrected_sentence": the learner's whole sentence, corrected.
   - "kind": "error" for real mistakes; "improvement" only for a clearly more natural alternative to something correct (use rarely).
   - "topic": one key from this list:
{topics}
   - "explanation": one short sentence in {explain}.
   - "id": "c1", "c2", ...
3. "spoken_correction_id": the id of the single most important "error" correction, or null if there is none.
4. "reply": your next line in {target} only, at most 2 short sentences, suitable for level {level}, ending with a question. Do not mention the corrections in the reply.
5. If the message is unintelligible, cut off, or not in {target}: set "needs_clarification" to true, "corrections" to [], "spoken_correction_id" to null, and make "reply" a short request in {target} to repeat.

Respond with ONE JSON object only, no other text. Example:
{json.dumps(_EXAMPLE, ensure_ascii=False)}"""


def build_messages(
    target_language: str,
    level: str,
    scenario: str,
    explanation_language: str,
    history: list[tuple[str, str]],
    transcript: str,
) -> list[dict[str, str]]:
    """`history` = (role, text) pairs, oldest first, role "user" (learner) or "assistant" (tutor)."""
    messages = [{"role": "system", "content": system_prompt(target_language, level, scenario, explanation_language)}]
    messages += [{"role": role, "content": text} for role, text in history[-CONTEXT_TURNS * 2:]]
    messages.append({"role": "user", "content": transcript})
    return messages


def repair_messages(messages: list[dict[str, str]], bad_output: str, errors: list[str]) -> list[dict[str, str]]:
    problems = "\n".join(f"- {e}" for e in errors[:10])
    return messages + [
        {"role": "assistant", "content": bad_output[:4000]},
        {"role": "user", "content": f"Your JSON was rejected:\n{problems}\nReturn the corrected JSON object only."},
    ]
