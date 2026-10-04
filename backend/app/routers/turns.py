from fastapi import APIRouter, Depends, Form, File, UploadFile, Response
from app.deps import get_db, get_providers, get_settings
from app.schemas.api import TurnOut, CorrectionOut
from app.services import turns, exclusions, reports
from app.services.errors import ApiError

router = APIRouter(prefix="/api", tags=["turns"])

@router.get("/sessions/{session_id}/turns", response_model=list[TurnOut])
def list_turns(session_id: int, db=Depends(get_db)):
    reports.require_session(db,session_id)
    return turns.list_turns(db,session_id)

@router.post("/sessions/{session_id}/turns", response_model=TurnOut)
async def submit(session_id: int, client_turn_id: str=Form(...),
    speech_span_ms: int=Form(...), voiced_ms: int=Form(...),pause_ms: int=Form(...),
    audio: UploadFile | None=File(None),db=Depends(get_db),providers=Depends(get_providers),settings=Depends(get_settings)):
    payload = None
    if audio is not None:
        if audio.content_type not in {"audio/wav","audio/x-wav","audio/wave"}:
            raise ApiError(415,"invalid_audio","Upload a WAV recording.",stage="request")
        payload = await audio.read(6_000_001)
        if len(payload) > 6_000_000:
            raise ApiError(413,"audio_too_large","Keep recordings under three minutes.",stage="request")
    return await turns.submit_turn(db,providers,settings,session_id,client_turn_id,payload,
                                  speech_span_ms,voiced_ms,pause_ms)

@router.get("/sessions/{session_id}/turns/by-client/{client_turn_id}", response_model=TurnOut)
def by_client(session_id: int,client_turn_id: str,db=Depends(get_db)):
    return turns.get_turn_by_client(db,session_id,client_turn_id)

@router.post("/turns/{turn_id}/speech", responses={200:{"content":{"audio/mpeg":{},"audio/wav":{}}}})
async def speech(turn_id: int,db=Depends(get_db),providers=Depends(get_providers)):
    result = await turns.synthesize_turn(db,providers,turn_id)
    return Response(content=result.audio,media_type=result.media_type,headers={"Cache-Control":"no-store"})

@router.post("/turns/{turn_id}/misheard", response_model=TurnOut)
def misheard(turn_id: int,db=Depends(get_db)):
    return exclusions.mark_misheard(db,turn_id)

@router.post("/mistakes/{mistake_id}/not-a-mistake", response_model=CorrectionOut)
def not_a_mistake(mistake_id: int,db=Depends(get_db)):
    return exclusions.mark_not_a_mistake(db,mistake_id)
