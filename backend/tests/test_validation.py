import pytest

from app.schemas.llm import TurnAnalysis
from app.services.validation import AnalysisValidationError, find_spans, normalize, validate_analysis

TRANSCRIPT = "Ich habe nach Berlin gegangen."


def analysis(**overrides):
    correction = {
        "id": "c1",
        "original": "habe nach Berlin gegangen",
        "corrected": "bin nach Berlin gegangen",
        "corrected_sentence": "Ich bin nach Berlin gegangen.",
        "kind": "error",
        "topic": "de_perfekt_auxiliary",
        "explanation": "gehen forms the Perfekt with sein.",
    }
    correction.update(overrides.pop("correction", {}))
    data = {
        "corrections": [correction],
        "spoken_correction_id": "c1",
        "needs_clarification": False,
        "reply": "Was hast du in Berlin gemacht?",
    }
    data.update(overrides)
    return TurnAnalysis.model_validate(data)


def test_valid_analysis_keeps_transcript_span_and_highlight():
    v = validate_analysis(analysis(), TRANSCRIPT, "de")
    c = v.corrections[0]
    assert c.original == "habe nach Berlin gegangen"
    assert TRANSCRIPT[c.highlight_start:c.highlight_end] == c.original
    assert v.spoken_ref == "c1"


def test_span_match_tolerates_case_whitespace_quotes_and_edge_punctuation():
    t = "Ich  HABE nach Berlin gegangen"
    v = validate_analysis(analysis(correction={"original": "habe nach berlin gegangen."}), t, "de")
    assert v.corrections[0].original == "HABE nach Berlin gegangen"
    assert find_spans("He said ’hello’", "'hello'") == [(9, 14)]


def test_eszett_and_umlauts_are_not_folded():
    assert normalize("Straße") == "straße"
    assert find_spans("die Straße ist groß", "strasse") == []
    assert find_spans("Ich möchte", "mochte") == []


def test_repeated_span_gets_no_highlight():
    t = "he go home and he go to work"
    v = validate_analysis(
        analysis(correction={
            "original": "he go", "corrected": "he goes", "corrected_sentence": "He goes home.",
            "topic": "en_third_person_s",
        }),
        t,
        "en",
    )
    c = v.corrections[0]
    assert c.highlight_start is None and c.highlight_end is None
    assert c.original == "he go"


@pytest.mark.parametrize(
    "overrides,fragment",
    [
        ({"correction": {"original": "habe nach Hamburg gegangen"}}, "does not appear"),
        ({"correction": {"topic": "en_articles"}}, "not in the de topic list"),
        ({"correction": {"corrected_sentence": "Ich war in Berlin."}}, "must contain corrected"),
        ({"correction": {"corrected": "habe nach Berlin gegangen"}}, "identical"),
        ({"spoken_correction_id": "c9"}, "references no correction"),
        ({"correction": {"kind": "improvement"}}, "kind=error"),
    ],
)
def test_invalid_analysis_fails(overrides, fragment):
    with pytest.raises(AnalysisValidationError) as exc:
        validate_analysis(analysis(**overrides), TRANSCRIPT, "de")
    assert any(fragment in e for e in exc.value.errors)


def test_extra_fields_rejected_by_schema():
    with pytest.raises(Exception):
        TurnAnalysis.model_validate({
            "corrections": [], "spoken_correction_id": None, "needs_clarification": False,
            "reply": "Hi", "transcript": "rewritten",
        })


def test_no_corrections_is_valid():
    v = validate_analysis(analysis(corrections=[], spoken_correction_id=None), TRANSCRIPT, "de")
    assert v.corrections == []
