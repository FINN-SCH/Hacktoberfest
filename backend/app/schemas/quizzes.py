from typing import Literal
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from .api import TargetLanguage

class QuizCreate(BaseModel):
    profile_id: int
    language: TargetLanguage

class Option(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1, max_length=30)
    text: str = Field(min_length=1)

class GeneratedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1, max_length=30)
    source_mistake_id: int
    kind: Literal["mc", "fill_in"]
    question: str = Field(min_length=1)
    options: list[Option]
    correct_option_id: str | None
    accepted_answers: list[str]
    explanation: str = Field(min_length=1)
    ambiguous: bool

class QuizGeneration(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    questions: list[GeneratedQuestion] = Field(min_length=1, max_length=5)

class QuizQuestionOut(BaseModel):
    id: str
    source_mistake_id: int
    kind: Literal["mc", "fill_in"]
    question: str
    options: list[Option]
    source_original: str
    source_corrected: str

class QuizOut(BaseModel):
    id: int
    profile_id: int
    language: TargetLanguage
    questions: list[QuizQuestionOut]
    created_at: datetime

class QuizAnswers(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: dict[str, str]

class QuestionResult(BaseModel):
    id: str
    status: Literal["correct", "wrong", "skipped_source_excluded"]
    correct_answer: str | None
    explanation: str
    source_original: str
    source_corrected: str

class QuizAttemptOut(BaseModel):
    id: int
    quiz_id: int
    correct: int
    total: int
    results: list[QuestionResult]
