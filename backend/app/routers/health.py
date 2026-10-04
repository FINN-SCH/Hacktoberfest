from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api", tags=["health"])

class HealthResponse(BaseModel):
    status: str
    service: str

@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    # Liveness only: provider readiness is checked explicitly, not billed on each poll.
    return HealthResponse(status="ok", service="voice-language-tutor")
