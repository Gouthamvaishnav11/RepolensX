from pydantic import BaseModel, HttpUrl, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class PlanEnum(str, Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class AnalysisStatusEnum(str, Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    EMBEDDING = "embedding"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Auth Schemas ─────────────────────────────────────────
class GitHubCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ─── User Schemas ─────────────────────────────────────────
class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: UUID
    github_id: str
    plan: PlanEnum
    repos_analyzed_this_month: int
    created_at: datetime

    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    public_profile: Optional[bool] = None
    preferred_language: Optional[str] = None


# ─── Repository Schemas ───────────────────────────────────
class RepoSubmitRequest(BaseModel):
    github_url: str

    class Config:
        json_schema_extra = {
            "example": {
                "github_url": "https://github.com/username/repository"
            }
        }


class RepoResponse(BaseModel):
    id: UUID
    github_url: str
    owner: str
    name: str
    full_name: str
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int
    forks: int
    status: AnalysisStatusEnum
    public_share_token: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RepoStatusResponse(BaseModel):
    repo_id: UUID
    status: AnalysisStatusEnum
    message: str
    progress_percent: int


# ─── Analysis Schemas ─────────────────────────────────────
class ScoreBreakdown(BaseModel):
    overall_score: Optional[float] = None
    recruiter_score: Optional[float] = None
    code_quality_score: Optional[float] = None
    documentation_score: Optional[float] = None
    testing_score: Optional[float] = None
    devops_score: Optional[float] = None
    architecture_score: Optional[float] = None


class AnalysisResponse(BaseModel):
    id: UUID
    repository_id: UUID
    scores: ScoreBreakdown
    summary: Optional[str] = None
    strengths: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    missing_practices: Optional[List[str]] = None
    recruiter_feedback: Optional[Dict[str, Any]] = None
    mentor_roadmap: Optional[Dict[str, Any]] = None
    code_analysis: Optional[Dict[str, Any]] = None
    docs_analysis: Optional[Dict[str, Any]] = None
    devops_analysis: Optional[Dict[str, Any]] = None
    total_files: int = 0
    total_commits: int = 0
    languages_detected: Optional[Dict[str, int]] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Chat Schemas ─────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Why is my architecture weak?",
                "conversation_history": []
            }
        }


class ChatSource(BaseModel):
    file_path: str
    content_preview: str
    relevance_score: float


class ChatResponse(BaseModel):
    message: str
    sources: List[ChatSource] = []
    repo_id: UUID


# ─── Comparison Schemas ───────────────────────────────────
class CompareRequest(BaseModel):
    repo_id_1: UUID
    repo_id_2: UUID


class CompareResponse(BaseModel):
    repo_1: RepoResponse
    repo_2: RepoResponse
    comparison: Dict[str, Any]
    winner: Optional[str] = None
    insights: List[str] = []
