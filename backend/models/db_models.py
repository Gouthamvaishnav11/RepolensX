from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, Text, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum


class Base(DeclarativeBase):
    pass


class PlanEnum(str, enum.Enum):
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class AnalysisStatusEnum(str, enum.Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    EMBEDDING = "embedding"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── User ─────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    name = Column(String, nullable=True)
    plan = Column(Enum(PlanEnum), default=PlanEnum.FREE)
    repos_analyzed_this_month = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    repositories = relationship("Repository", back_populates="user")
    preferences = relationship("UserPreferences", back_populates="user", uselist=False)


# ─── UserPreferences ──────────────────────────────────────
class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True)
    email_notifications = Column(Boolean, default=True)
    public_profile = Column(Boolean, default=False)
    preferred_language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="preferences")


# ─── Repository ───────────────────────────────────────────
class Repository(Base):
    __tablename__ = "repositories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    github_url = Column(String, nullable=False)
    github_repo_id = Column(String, nullable=True)
    owner = Column(String, nullable=False)
    name = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    language = Column(String, nullable=True)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    is_private = Column(Boolean, default=False)
    status = Column(Enum(AnalysisStatusEnum), default=AnalysisStatusEnum.PENDING)
    chroma_collection_id = Column(String, nullable=True)
    public_share_token = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="repositories")
    analysis = relationship("Analysis", back_populates="repository", uselist=False)


# ─── Analysis ─────────────────────────────────────────────
class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"), unique=True)

    # Scores (0-100)
    overall_score = Column(Float, nullable=True)
    recruiter_score = Column(Float, nullable=True)
    code_quality_score = Column(Float, nullable=True)
    documentation_score = Column(Float, nullable=True)
    testing_score = Column(Float, nullable=True)
    devops_score = Column(Float, nullable=True)
    architecture_score = Column(Float, nullable=True)

    # Agent outputs (stored as JSON)
    recruiter_feedback = Column(JSON, nullable=True)     # Agent 4 output
    mentor_roadmap = Column(JSON, nullable=True)         # Agent 7 output
    code_analysis = Column(JSON, nullable=True)          # Agent 3 output
    docs_analysis = Column(JSON, nullable=True)          # Agent 5 output
    devops_analysis = Column(JSON, nullable=True)        # Agent 6 output

    # Summary
    summary = Column(Text, nullable=True)
    strengths = Column(JSON, nullable=True)
    weaknesses = Column(JSON, nullable=True)
    missing_practices = Column(JSON, nullable=True)

    # Metadata
    total_files = Column(Integer, default=0)
    total_commits = Column(Integer, default=0)
    total_issues = Column(Integer, default=0)
    languages_detected = Column(JSON, nullable=True)

    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    repository = relationship("Repository", back_populates="analysis")


# ─── ChatMessage ──────────────────────────────────────────
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repository_id = Column(UUID(as_uuid=True), ForeignKey("repositories.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    role = Column(String, nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)   # RAG retrieved chunks
    created_at = Column(DateTime, default=datetime.utcnow)
