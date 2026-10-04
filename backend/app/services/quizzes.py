import json
import unicodedata
from collections import Counter
from app.models import Profile, Session, Quiz, QuizAttempt
from app.languages import resolve_explanation_language
from app.schemas.quizzes import QuizGeneration, QuizOut, QuizQuestionOut, QuizAttemptOut, QuestionResult
from app.services import eligibility
from app.services.reports import generate_validated
from app.services.errors import ApiError
from app.prompts import quiz as prompt

def normalize_answer(value: str) -> str:
    return " ".join(unicodedata.normalize("NFC", value).split())

def require_profile(db, profile_id):
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise ApiError(404, "profile_not_found", "Profile not found.")
    return profile

async def create_quiz(db, providers, profile_id: int, language: str) -> QuizOut:
    profile = require_profile(db, profile_id)
    errors = eligibility.active_errors(db, profile_id=profile_id, language=language)
    if not errors:
        raise ApiError(409, "no_mistakes", "Complete a conversation first; no eligible mistakes are available yet.")
    counts = Counter(m.topic for m in errors)
    latest_by_topic = {m.topic: (m.created_at, m.id) for m in errors}
    ranked = sorted(errors, key=lambda m: (counts[m.topic], latest_by_topic[m.topic], m.created_at, m.id), reverse=True)
    sessions = {m.session_id: db.get(Session, m.session_id) for m in errors}
    latest_session = max(sessions, key=lambda k: (sessions[k].started_at, k))
    recent = next(m for m in reversed(errors) if m.session_id == latest_session)
    selected = [recent] + [m for m in ranked if m.id != recent.id][:4]
    sources = {m.id: m for m in selected}
    context = {"language": language, "explanation_language": resolve_explanation_language(
        profile.default_explanation_mode, profile.native_language, language), "required_recent_source_id": recent.id,
        "sources": [{"id":m.id,"topic":m.topic,"original":m.original,"corrected":m.corrected,
                     "corrected_sentence":m.corrected_sentence,"explanation":m.explanation} for m in selected]}
    db.commit()
    def validate(out):
        ids = set()
        kept = []
        for q in out.questions:
            if q.id in ids:
                raise ValueError("Question ids must be unique")
            ids.add(q.id)
            if q.source_mistake_id not in sources:
                raise ValueError("Source must be one of the supplied eligible mistakes")
            if q.ambiguous:
                continue
            if q.kind == "mc":
                option_ids = [x.id for x in q.options]
                texts = [normalize_answer(x.text) for x in q.options]
                if len(option_ids) < 2 or len(set(option_ids)) != len(option_ids) or len(set(texts)) != len(texts):
                    raise ValueError("MC options must be distinct")
                if q.correct_option_id not in option_ids or q.accepted_answers:
                    raise ValueError("MC answer must reference an option id and accepted_answers must be empty")
            elif q.options or q.correct_option_id is not None or not q.accepted_answers or any(not normalize_answer(a) for a in q.accepted_answers):
                raise ValueError("Fill-in needs nonempty answers and no options or option key")
            kept.append(q)
        if not kept or not any(q.source_mistake_id == recent.id for q in kept):
            raise ValueError("Include an unambiguous question from required_recent_source_id")
        out.questions = kept
    generated = await generate_validated(providers, prompt.messages(context), QuizGeneration, "quiz", validate)
    # End the read snapshot and refresh so concurrent exclusions are visible.
    db.expire_all()
    questions = []
    for q in generated.questions:
        if eligibility.is_mistake_eligible(db, q.source_mistake_id, profile_id, language):
            source = sources[q.source_mistake_id]
            questions.append({**q.model_dump(), "source_original":source.original, "source_corrected":source.corrected})
    if not questions:
        raise ApiError(409, "no_mistakes", "The source mistakes were excluded. Create a new quiz.")
    current_errors = eligibility.active_errors(db, profile_id=profile_id, language=language)
    latest_session = max({m.session_id for m in current_errors}, key=lambda k: (db.get(Session,k).started_at,k))
    recent_ids = {m.id for m in current_errors if m.session_id == latest_session}
    if not any(q["source_mistake_id"] in recent_ids for q in questions):
        raise ApiError(409, "sources_changed", "Recent source mistakes changed. Create a new quiz.")
    quiz = Quiz(profile_id=profile_id, language=language, questions_json=json.dumps(questions, ensure_ascii=False))
    db.add(quiz); db.commit(); db.refresh(quiz)
    return QuizOut(id=quiz.id, profile_id=profile_id, language=language, created_at=quiz.created_at,
        questions=[QuizQuestionOut.model_validate(q) for q in questions])

def grade(db, quiz_id: int, data) -> QuizAttemptOut:
    quiz = db.get(Quiz, quiz_id)
    if quiz is None:
        raise ApiError(404, "quiz_not_found", "Quiz not found.")
    questions = json.loads(quiz.questions_json)
    if set(data.answers) - {q["id"] for q in questions}:
        raise ApiError(422, "invalid_answers", "An answer refers to an unknown question.")
    results = []
    correct = total = 0
    for q in questions:
        key = q["correct_option_id"] if q["kind"] == "mc" else q["accepted_answers"][0]
        display_key = next((x["text"] for x in q["options"] if x["id"] == key), key)
        if not eligibility.is_mistake_eligible(db, q["source_mistake_id"], quiz.profile_id, quiz.language):
            status = "skipped_source_excluded"
        else:
            total += 1
            answer = data.answers.get(q["id"], "")
            hit = answer == key if q["kind"] == "mc" else normalize_answer(answer) in {normalize_answer(x) for x in q["accepted_answers"]}
            correct += int(hit)
            status = "correct" if hit else "wrong"
        results.append(QuestionResult(id=q["id"], status=status, correct_answer=display_key,
            explanation=q["explanation"], source_original=q["source_original"], source_corrected=q["source_corrected"]))
    attempt = QuizAttempt(quiz_id=quiz_id, answers_json=data.model_dump_json(),
        results_json=json.dumps([x.model_dump() for x in results], ensure_ascii=False), correct=correct,total=total)
    db.add(attempt); db.commit(); db.refresh(attempt)
    return QuizAttemptOut(id=attempt.id,quiz_id=quiz_id,correct=correct,total=total,results=results)
