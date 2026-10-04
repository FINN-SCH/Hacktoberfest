from fastapi import APIRouter, Depends
from app.deps import get_db, get_providers
from app.schemas.quizzes import QuizCreate, QuizOut, QuizAnswers, QuizAttemptOut
from app.services import quizzes
router = APIRouter(prefix="/api/quizzes",tags=["quizzes"])

@router.post("",response_model=QuizOut,status_code=201)
async def create(data: QuizCreate,db=Depends(get_db),providers=Depends(get_providers)):
    return await quizzes.create_quiz(db,providers,data.profile_id,data.language)

@router.post("/{quiz_id}/attempts",response_model=QuizAttemptOut)
def grade(quiz_id: int,data: QuizAnswers,db=Depends(get_db)):
    return quizzes.grade(db,quiz_id,data)
