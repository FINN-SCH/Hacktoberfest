from collections import defaultdict
from sqlmodel import select
from app.models import Session, ProfileAnalysis, utcnow
from app.languages import resolve_explanation_language
from app.schemas.analysis import AnalysisOut, WrittenAnalysis, TopicFrequency, RecurringTopic, RecurringExample, ImprovingTopic
from app.services import eligibility
from app.services.validation import normalize
from app.services.reports import history_item, stale_exclusions, generate_validated
from app.services.quizzes import require_profile
from app.services.errors import ApiError
from app.topics import topic_label, is_valid_topic
from app.prompts import analysis as prompt

def _sessions(db, profile_id, language):
    return list(db.exec(select(Session).where(Session.profile_id==profile_id, Session.target_language==language,
        Session.status=="ended").order_by(Session.started_at, Session.id)).all())

def get_analysis(db, profile_id: int, language: str) -> AnalysisOut:
    require_profile(db, profile_id)
    sessions = _sessions(db, profile_id, language)
    errors = eligibility.active_errors(db, profile_id=profile_id, language=language, ended_only=True)
    grouped = defaultdict(list)
    for m in errors:
        grouped[m.topic].append(m)
    frequency = [TopicFrequency(topic=topic,label=topic_label(topic),errors=len(items),
        share=len(items)/len(errors),sessions=len({m.session_id for m in items}),last_seen=max(m.created_at for m in items))
        for topic, items in grouped.items()]
    frequency.sort(key=lambda x:(x.errors,x.last_seen),reverse=True)
    recurring = []
    for row in frequency:
        if row.sessions < 2:
            continue
        examples = defaultdict(list)
        for m in grouped[row.topic]:
            examples[normalize(m.corrected)].append(m)
        repeated = sorted(examples.values(), key=lambda x:(len(x),x[-1].created_at),reverse=True)[:3]
        recurring.append(RecurringTopic(topic=row.topic,label=row.label,sessions=row.sessions,errors=row.errors,
            examples=[RecurringExample(original=x[-1].original,corrected=x[-1].corrected,count=len(x)) for x in repeated]))
    improving = []
    if len(sessions) >= 3 and all(len(eligibility.eligible_turns(db,session_id=s.id)) >= 5 for s in sessions[-2:]):
        last_ids = {s.id for s in sessions[-2:]}
        improving = [ImprovingTopic(topic=row.topic,label=row.label) for row in frequency
                     if not any(m.session_id in last_ids for m in grouped[row.topic])]
    attempts = list(db.exec(select(ProfileAnalysis).where(ProfileAnalysis.profile_id==profile_id,
        ProfileAnalysis.language==language).order_by(ProfileAnalysis.generated_at.desc(),ProfileAnalysis.id.desc())).all())
    latest_ok = next((a for a in attempts if a.status=="ok"), None)
    return AnalysisOut(profile_id=profile_id,language=language,session_count=len(sessions),topic_frequency=frequency,
        progress=[history_item(db,s) for s in sessions],recurring=recurring,improving=improving,
        written=WrittenAnalysis.model_validate_json(latest_ok.content_json) if latest_ok else None,
        based_on_sessions=latest_ok.session_count if latest_ok else None,generated_at=latest_ok.generated_at if latest_ok else None,
        stale_exclusions=stale_exclusions(db,latest_ok.evidence_cutoff_at,profile_id=profile_id,language=language) if latest_ok else 0,
        latest_attempt_failed=bool(attempts and attempts[0].status=="failed"))

async def generate_analysis(db, providers, profile_id: int, language: str):
    cutoff = utcnow()
    snapshot = get_analysis(db,profile_id,language)
    if snapshot.session_count < 2:
        return
    errors = eligibility.active_errors(db,profile_id=profile_id,language=language,ended_only=True)
    sources = {m.id:m for m in errors[-30:]}
    topics = {x.topic for x in snapshot.topic_frequency}
    profile = require_profile(db,profile_id)
    context = {"language":language,"explanation_language":resolve_explanation_language(profile.default_explanation_mode,profile.native_language,language),
        "statistics":snapshot.model_dump(mode="json",exclude={"written"}),
        "mistakes":[{"id":m.id,"topic":m.topic,"original":m.original,"corrected":m.corrected} for m in sources.values()]}
    db.commit()
    def validate(out):
        for focus in out.focus_areas:
            if focus.topic not in topics or not is_valid_topic(focus.topic, language):
                raise ValueError("Focus topic must occur in the supplied current topic table")
            if any(mid not in sources or sources[mid].topic != focus.topic for mid in focus.example_mistake_ids):
                raise ValueError("Example ids must be supplied eligible mistakes of this topic")
    attempt = ProfileAnalysis(profile_id=profile_id,language=language,status="failed",
                              evidence_cutoff_at=cutoff,session_count=snapshot.session_count)
    try:
        out = await generate_validated(providers,prompt.messages(context),WrittenAnalysis,"analysis",validate)
        attempt.status = "ok"
        attempt.content_json = out.model_dump_json()
    except ApiError as exc:
        attempt.error = exc.body.code
    except Exception:
        # Runs as a background task: always record the attempt so the UI never waits forever.
        attempt.error = "internal_error"
    attempt.generated_at = utcnow()
    db.add(attempt); db.commit()
