from fastapi import APIRouter, Depends
from sqlmodel import select
from app.deps import get_db
from app.models import Profile
from app.schemas.api import ProfileCreate, ProfileOut
from app.services.errors import ApiError
from app.languages import LANGUAGE_NAMES

router = APIRouter(prefix="/api/profiles", tags=["profiles"])

@router.get("", response_model=list[ProfileOut])
def list_profiles(db=Depends(get_db)):
    return [ProfileOut.model_validate(p, from_attributes=True) for p in db.exec(select(Profile).order_by(Profile.created_at,Profile.id)).all()]

@router.post("", response_model=ProfileOut, status_code=201)
def create_profile(data: ProfileCreate, db=Depends(get_db)):
    if not data.name.strip() or data.native_language not in LANGUAGE_NAMES:
        raise ApiError(422,"invalid_profile","Enter a name and a supported native language.",stage="request")
    profile = Profile(**data.model_dump())
    profile.name = profile.name.strip()
    db.add(profile); db.commit(); db.refresh(profile)
    return ProfileOut.model_validate(profile, from_attributes=True)
