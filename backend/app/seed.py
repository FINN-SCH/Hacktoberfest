"""Offline demo fixtures. All generated sessions are explicitly labelled; no providers are used."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from sqlalchemy import delete
from sqlmodel import SQLModel, Session as DBSession, select
from app.config import Settings
from app.db import make_engine
from app.languages import OPENINGS
from app.models import Profile, Session, Turn, Mistake, Quiz, QuizAttempt, ProfileAnalysis, utcnow
from app.schemas.analysis import WrittenAnalysis
from app.schemas.reports import ReportGeneration
from app.services import eligibility
from app.services.analysis import get_analysis
from app.services.scoring import session_scores
from app.services.validation import find_spans
from app.topics import is_valid_topic

DEMO_NAME = "Demo learner"

class SeedError(ValueError):
    pass

# Each tuple is transcript plus (original, replacement, corrected sentence, topic, explanation), or None.
GERMAN = [
    [
        ("Heute ich möchte in diesem Café frühstücken, weil ich danach mit meiner Schwester in die Stadt gehe.",
         ("Heute ich möchte", "Heute möchte ich", "Heute möchte ich in diesem Café frühstücken, weil ich danach mit meiner Schwester in die Stadt gehe.", "de_verb_second", "After Heute, the finite verb comes before the subject.")),
        ("Ich nehme der Kaffee mit Milch und dazu ein frisches Brötchen, aber bitte ohne Zucker.",
         ("der Kaffee", "den Kaffee", "Ich nehme den Kaffee mit Milch und dazu ein frisches Brötchen, aber bitte ohne Zucker.", "de_accusative", "The masculine direct object takes den.")),
        ("Ich fahre nach dem Frühstück mit den Bus zum Bahnhof, denn meine Schwester wartet dort auf mich.",
         ("mit den Bus", "mit dem Bus", "Ich fahre nach dem Frühstück mit dem Bus zum Bahnhof, denn meine Schwester wartet dort auf mich.", "de_dative", "Mit takes the dative case.")),
        ("Am Wochenende besuche ich oft meine Familie, und wir kochen zusammen eine große Suppe mit frischem Gemüse.", None),
        ("Meine Schwester arbeitet in einer kleinen Buchhandlung in der Nähe, deshalb treffen wir uns meistens am Bahnhof.", None),
        ("Vielen Dank, das Frühstück schmeckt sehr gut. Ich möchte jetzt bezahlen und danach noch einen kurzen Spaziergang machen.", None),
    ],
    [
        ("Morgen ich gehe mit meiner Freundin in ein neues Café, weil wir dort gemeinsam für unsere Prüfung lernen wollen.",
         ("Morgen ich gehe", "Morgen gehe ich", "Morgen gehe ich mit meiner Freundin in ein neues Café, weil wir dort gemeinsam für unsere Prüfung lernen wollen.", "de_verb_second", "Put the finite verb second after Morgen.")),
        ("Ich bestelle der Tee mit Zitrone und ein kleines Stück Kuchen, denn heute habe ich wirklich großen Hunger.",
         ("der Tee", "den Tee", "Ich bestelle den Tee mit Zitrone und ein kleines Stück Kuchen, denn heute habe ich wirklich großen Hunger.", "de_accusative", "Bestellen has a direct object: den Tee.")),
        ("Wir fahren mit dem Bus in die Stadt und treffen uns vor dem Café direkt neben der alten Bibliothek.", None),
        ("Für die Prüfung muss ich noch viele neue Wörter lernen, aber die kurzen Gespräche helfen mir beim Sprechen.", None),
        ("Meine Freundin bestellt lieber Wasser, weil sie schon zu Hause einen Kaffee getrunken hat und jetzt etwas Kaltes möchte.", None),
        ("Nach dem Lernen gehen wir zusammen nach Hause. Ich freue mich auf das Abendessen und möchte später ein Buch lesen.", None),
    ],
    [
        ("Heute ich möchte nach der Arbeit wieder in diesem Café sitzen und meiner Freundin von meinem ersten Arbeitstag erzählen.",
         ("Heute ich möchte", "Heute möchte ich", "Heute möchte ich nach der Arbeit wieder in diesem Café sitzen und meiner Freundin von meinem ersten Arbeitstag erzählen.", "de_verb_second", "Heute occupies the first position, so möchte comes next.")),
        ("Ich nehme der Kaffee und ein Brötchen mit Käse, weil ich seit dem Frühstück noch nichts gegessen habe.",
         ("der Kaffee", "den Kaffee", "Ich nehme den Kaffee und ein Brötchen mit Käse, weil ich seit dem Frühstück noch nichts gegessen habe.", "de_accusative", "Use den for the masculine direct object.")),
        ("Mit dem Bus brauche ich ungefähr zwanzig Minuten zur Arbeit, aber heute bin ich wegen des schönen Wetters gelaufen.", None),
        ("Meine neuen Kollegen sind sehr freundlich. In der Mittagspause haben wir über unsere Familien und unsere Lieblingsgerichte gesprochen.", None),
        ("Am Anfang war ich ein bisschen nervös, doch meine Kollegin hat mir alles gezeigt und meine Fragen geduldig beantwortet.", None),
        ("Morgen möchte ich früher aufstehen und mein Mittagessen selbst vorbereiten. Danach habe ich am Abend mehr Zeit zum Lernen.", None),
    ],
]
ENGLISH = [
    ("Yesterday I go to a small café with my sister, and we talked about our plans for the coming weekend.",
     ("Yesterday I go", "Yesterday I went", "Yesterday I went to a small café with my sister, and we talked about our plans for the coming weekend.", "en_past_simple_irregular", "Yesterday needs the past form went.")),
    ("My sister work in a bookshop near the station, so we usually meet there when she finishes in the afternoon.",
     ("My sister work", "My sister works", "My sister works in a bookshop near the station, so we usually meet there when she finishes in the afternoon.", "en_third_person_s", "A third-person singular subject takes works.")),
    ("I would like a cup of tea and a sandwich with cheese, please. Could we sit near the window today?", None),
    ("The weather was lovely, so we walked through the park after lunch and took some photographs of the flowers.", None),
    ("This weekend I am going to cook dinner for my family. I want to try a new recipe with vegetables.", None),
    ("Thank you for the tea. Everything was delicious, and I would like to pay before I leave for the station.", None),
]

def _remove_demo(db: DBSession, profiles: list[Profile], demo_sessions: list[Session]) -> None:
    if len(profiles) != 1 or not demo_sessions:
        raise SeedError("The name Demo learner is reserved, but these rows are not a recognized demo. Nothing deleted.")
    profile_id = profiles[0].id
    if any(s.profile_id != profile_id for s in demo_sessions):
        raise SeedError("Demo sessions belong to another profile. Nothing deleted; review the data manually.")
    if db.exec(select(Session.id).where(Session.profile_id == profile_id, Session.is_demo_data == False)).first() is not None:
        raise SeedError("Demo learner has non-demo sessions. Reset refused to preserve real practice; use a separate profile.")
    session_ids = [s.id for s in demo_sessions]
    quiz_ids = select(Quiz.id).where(Quiz.profile_id == profile_id)
    db.exec(delete(QuizAttempt).where(QuizAttempt.quiz_id.in_(quiz_ids)))
    db.exec(delete(Quiz).where(Quiz.profile_id == profile_id))
    db.exec(delete(ProfileAnalysis).where(ProfileAnalysis.profile_id == profile_id))
    db.exec(delete(Mistake).where(Mistake.session_id.in_(session_ids)))
    db.exec(delete(Turn).where(Turn.session_id.in_(session_ids)))
    db.exec(delete(Session).where(Session.id.in_(session_ids)))
    db.exec(delete(Profile).where(Profile.id == profile_id))
    db.flush()

def _session(db, profile_id, language, entries, started_at, ordinal):
    ended_at = started_at + timedelta(minutes=4)
    cutoff = ended_at - timedelta(seconds=1)
    session = Session(profile_id=profile_id, target_language=language, explanation_language="en",
        level="A2", scenario="cafe", status="ended", is_demo_data=True, started_at=started_at,
        ended_at=ended_at, snapshot_status="ok", snapshot_evidence_cutoff_at=cutoff,
        snapshot_generated_at=ended_at)
    db.add(session)
    db.flush()
    db.add(Turn(session_id=session.id, seq=0, kind="opening", correction_status="done",
                tutor_reply=OPENINGS[language]["cafe"], created_at=started_at, updated_at=started_at))
    for seq, (transcript, correction) in enumerate(entries, 1):
        when = started_at + timedelta(seconds=seq * 25)
        turn = Turn(session_id=session.id, seq=seq, client_turn_id=f"demo-v1-{ordinal}-{seq}",
            correction_status="done", transcript=transcript, speech_span_ms=15000, voiced_ms=12000,
            pause_ms=3000, tutor_reply="Danke! Was möchtest du noch erzählen?" if language == "de" else "Thank you! What else would you like to tell me?",
            llm_model="offline-demo-fixture", prompt_version="demo-v1", created_at=when, updated_at=when)
        db.add(turn)
        db.flush()
        if correction:
            original, corrected, sentence, topic, explanation = correction
            spans = find_spans(transcript, original)
            if original not in transcript or len(spans) != 1 or not is_valid_topic(topic, language):
                raise SeedError("Invalid demo correction evidence")
            begin, end = spans[0]
            if transcript[begin:end] != original or corrected not in sentence:
                raise SeedError("Invalid demo highlight or replacement")
            mistake = Mistake(profile_id=profile_id, session_id=session.id, turn_id=turn.id,
                language=language, topic=topic, kind="error", original=original, corrected=corrected,
                corrected_sentence=sentence, explanation=explanation, highlight_start=begin,
                highlight_end=end, llm_ref="c1", created_at=when)
            db.add(mistake)
            db.flush()
            turn.spoken_correction_mistake_id = mistake.id
            db.add(turn)
    db.flush()
    turns = eligibility.eligible_turns(db, session_id=session.id)
    if not session_scores(db, session).sufficient_sample:
        raise SeedError("Demo session does not meet the sample minimum")
    quoted = turns[-1]
    summary = {"weaknesses": ["Verb position and accusative articles"] if language == "de" else ["Past forms and third-person verb endings"],
               "next_focus": "Practise a short café conversation using correct verb and article forms. This is illustrative demo feedback."}
    snapshot = ReportGeneration.model_validate({"vocab_rating": 3, "vocab_evidence": [
        {"turn_id": quoted.id, "quote": quoted.transcript, "explanation": "Connected everyday vocabulary appropriate to an A2 café conversation."}],
        "summary": summary})
    session.vocab_rating = snapshot.vocab_rating
    session.vocab_evidence_json = json.dumps([item.model_dump() for item in snapshot.vocab_evidence], ensure_ascii=False)
    session.summary_json = snapshot.summary.model_dump_json()
    db.add(session)
    db.flush()

def seed_demo(db: DBSession, *, reset_demo: bool = False, now: datetime | None = None) -> Profile:
    now = now or utcnow()
    profiles = list(db.exec(select(Profile).where(Profile.name == DEMO_NAME)).all())
    demo_sessions = list(db.exec(select(Session).where(Session.is_demo_data == True)).all())
    if demo_sessions and not reset_demo:
        raise SeedError("Demo data already exists. Use --reset-demo to replace only demo data.")
    if profiles or demo_sessions:
        if not reset_demo:
            raise SeedError("The name Demo learner is reserved by existing data. Nothing changed.")
        _remove_demo(db, profiles, demo_sessions)
    try:
        profile = Profile(name=DEMO_NAME, native_language="en", default_explanation_mode="native",
                          created_at=now - timedelta(days=10))
        db.add(profile)
        db.flush()
        for index, days in enumerate((9, 6, 2)):
            _session(db, profile.id, "de", GERMAN[index], now - timedelta(days=days), index)
        _session(db, profile.id, "en", ENGLISH, now - timedelta(days=1), 3)
        computed = get_analysis(db, profile.id, "de")
        mistakes = eligibility.active_errors(db, profile_id=profile.id, language="de", ended_only=True)
        focus = [{"topic": topic, "why": f"This topic appears in {next(x.sessions for x in computed.topic_frequency if x.topic == topic)} demo sessions.",
                  "tip": tip, "example_mistake_ids": [m.id for m in mistakes if m.topic == topic][-2:]}
                 for topic, tip in (("de_verb_second", "After Heute or Morgen, put the finite verb second."),
                                    ("de_accusative", "Practise Ich nehme den Kaffee and Ich bestelle den Tee."))]
        written = WrittenAnalysis.model_validate({
            "summary": "Illustrative demo analysis: verb position and accusative articles recur. Dative prepositions are absent from the last two qualifying sessions.",
            "strengths": [{"text": "Connected everyday speech", "evidence": "All three German demo sessions meet the five-turn and sixty-second sample minimum."}],
            "focus_areas": focus})
        db.add(ProfileAnalysis(profile_id=profile.id, language="de", status="ok",
            evidence_cutoff_at=now, generated_at=now, session_count=computed.session_count,
            content_json=written.model_dump_json()))
        db.commit()
        db.refresh(profile)
        return profile
    except Exception:
        db.rollback()
        raise

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Create labelled demo data without any provider calls.")
    parser.add_argument("--reset-demo", action="store_true", help="Replace demo data; refuse if the demo profile contains real sessions.")
    args = parser.parse_args(argv)
    settings = Settings()
    engine = make_engine(str(settings.db_path))
    try:
        # Creating tables must NOT invoke startup recovery on somebody's active real turns.
        SQLModel.metadata.create_all(engine)
        with DBSession(engine) as db:
            profile = seed_demo(db, reset_demo=args.reset_demo)
            print(f"PASS demo profile {profile.id}: 3 German + 1 English ended sessions; no provider calls.")
        return 0
    except SeedError as exc:
        print(f"REFUSED {exc}")
        return 1
    finally:
        engine.dispose()

if __name__ == "__main__":
    raise SystemExit(main())
