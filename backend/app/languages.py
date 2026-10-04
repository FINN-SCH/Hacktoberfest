"""Per-language settings: claimed target languages, levels, scenarios, openings, spoken recast templates."""

TARGET_LANGUAGES: dict[str, str] = {"de": "German", "en": "English"}

LEVELS = ("A1", "A2", "B1", "B2")

SCENARIOS: dict[str, str] = {
    "cafe": "Ordering at a cafe",
    "job_interview": "Job interview",
    "doctor": "At the doctor's",
    "free_talk": "Free conversation",
}

# Languages a profile may pick as its native/explanation language.
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "de": "German",
    "ar": "Arabic",
    "es": "Spanish",
    "fr": "French",
    "tr": "Turkish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
}

# The spoken correction is a recast in the TARGET language, so TTS never mixes languages.
RECAST_TEMPLATES: dict[str, str] = {
    "de": "Du meinst: {sentence}",
    "en": "You mean: {sentence}",
}

OPENINGS: dict[str, dict[str, str]] = {
    "de": {
        "cafe": "Hallo und willkommen im Café! Was möchtest du heute trinken?",
        "job_interview": "Guten Tag, schön, dass Sie da sind. Erzählen Sie mir bitte etwas über sich.",
        "doctor": "Guten Tag, ich bin Doktor Weber. Was fehlt Ihnen denn?",
        "free_talk": "Hallo! Wie war dein Tag bisher?",
    },
    "en": {
        "cafe": "Hi, welcome to the cafe! What can I get you today?",
        "job_interview": "Good morning, thanks for coming in. Could you tell me a bit about yourself?",
        "doctor": "Hello, I'm Doctor Miller. What brings you in today?",
        "free_talk": "Hi there! How has your day been so far?",
    },
}


def resolve_explanation_language(mode: str, native_language: str, target_language: str) -> str:
    """Snapshot a concrete language code for explanations ("native" or "target" mode)."""
    if mode == "target":
        return target_language
    return native_language


def spoken_text(target_language: str, corrected_sentence: str | None, reply: str) -> str:
    if corrected_sentence:
        recast = RECAST_TEMPLATES[target_language].format(sentence=corrected_sentence.strip())
        return f"{recast} {reply.strip()}"
    return reply.strip()
