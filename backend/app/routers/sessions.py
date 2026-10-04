from fastapi import APIRouter, Depends, BackgroundTasks, Request
from sqlmodel import select, Session as DBSession
from app.deps import get_db, get_providers
from app.models import Session
from app.schemas.api import SessionCreate, SessionOut, SessionStartOut
from app.schemas.reports import ReportOut, SessionHistoryOut
from app.services import turns, reports, analysis
from app.services.quizzes import require_profile

router = APIRouter(prefix="/api", tags=["sessions"])

@router.post("/sessions", response_model=SessionStartOut, status_code=201)
async def start(data: SessionCreate, db=Depends(get_db)):
    return await turns.start_session(db, data)

@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: int, db=Depends(get_db)):
    return SessionOut.model_validate(reports.require_session(db,session_id),from_attributes=True)

@router.get("/profiles/{profile_id}/sessions", response_model=list[SessionHistoryOut])
def history(profile_id: int, db=Depends(get_db)):
    require_profile(db,profile_id)
    rows = db.exec(select(Session).where(Session.profile_id==profile_id).order_by(Session.started_at.desc(),Session.id.desc())).all()
    return [reports.history_item(db,s) for s in rows]

async def update_analysis(engine, providers, profile_id, language):
    with DBSession(engine) as db:
        await analysis.generate_analysis(db,providers,profile_id,language)

@router.post("/sessions/{session_id}/end", response_model=ReportOut)
async def end(session_id: int, background: BackgroundTasks, request: Request,
              db=Depends(get_db), providers=Depends(get_providers)):
    previous = reports.require_session(db,session_id).status
    result = await reports.end_session(db,providers,session_id)
    if previous != "ended":
        background.add_task(update_analysis,request.app.state.engine,providers,
                            result.session.profile_id,result.session.target_language)
    return result

@router.get("/sessions/{session_id}/report", response_model=ReportOut)
def report(session_id: int, db=Depends(get_db)):
    return reports.get_report(db,session_id)

@router.post("/sessions/{session_id}/report/regenerate", response_model=ReportOut)
async def regenerate(session_id: int, db=Depends(get_db),providers=Depends(get_providers)):
    return await reports.regenerate(db,providers,session_id)
