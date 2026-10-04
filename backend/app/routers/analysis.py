from fastapi import APIRouter, Depends
from app.deps import get_db
from app.schemas.api import TargetLanguage
from app.schemas.analysis import AnalysisOut
from app.services import analysis
router = APIRouter(prefix="/api/profiles",tags=["analysis"])

@router.get("/{profile_id}/analysis",response_model=AnalysisOut)
def get(profile_id: int,language: TargetLanguage,db=Depends(get_db)):
    return analysis.get_analysis(db,profile_id,language)
