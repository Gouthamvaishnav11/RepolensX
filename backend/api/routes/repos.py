from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import secrets
import re
from uuid import UUID

from models.database import get_db
from models.db_models import User, Repository, Analysis, PlanEnum, AnalysisStatusEnum
from models.schemas import RepoSubmitRequest, RepoResponse, RepoStatusResponse
from api.middleware.auth import get_current_user

router = APIRouter(prefix="/repos", tags=["Repositories"])


PLAN_LIMITS = {
    PlanEnum.FREE: 3,
    PlanEnum.PRO: 20,
    PlanEnum.TEAM: 9999,
    PlanEnum.ENTERPRISE: 9999,
}


def parse_github_url(url: str) -> tuple[str, str]:
    """Extract owner and repo name from GitHub URL."""
    patterns = [
        r"github\.com/([^/]+)/([^/\s]+?)(?:\.git)?(?:/.*)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            owner = match.group(1)
            name = match.group(2).rstrip("/")
            return owner, name
    raise ValueError(f"Invalid GitHub URL: {url}")


@router.post("/submit", response_model=RepoResponse)
async def submit_repository(
    request: RepoSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a GitHub repository for analysis."""

    # Check plan limits
    limit = PLAN_LIMITS.get(current_user.plan, 3)
    if current_user.repos_analyzed_this_month >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Monthly limit reached. Upgrade to PRO for more analyses.",
        )

    # Parse GitHub URL
    try:
        owner, name = parse_github_url(request.github_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    full_name = f"{owner}/{name}"

    # Check if already submitted by this user
    existing = await db.execute(
        select(Repository).where(
            Repository.user_id == current_user.id,
            Repository.full_name == full_name,
        )
    )
    existing_repo = existing.scalar_one_or_none()
    if existing_repo:
        return existing_repo

    # Create repository record
    repo = Repository(
        user_id=current_user.id,
        github_url=request.github_url,
        owner=owner,
        name=name,
        full_name=full_name,
        status=AnalysisStatusEnum.PENDING,
        public_share_token=secrets.token_urlsafe(16),
    )
    db.add(repo)

    # Create empty analysis record
    await db.flush()
    analysis = Analysis(repository_id=repo.id)
    db.add(analysis)

    # Increment user monthly counter
    current_user.repos_analyzed_this_month += 1

    await db.commit()
    await db.refresh(repo)

    # Queue background analysis task
    from tasks.celery_app import analyze_repository_task
    analyze_repository_task.delay(str(repo.id), str(current_user.id))

    return repo


@router.get("/{repo_id}/status", response_model=RepoStatusResponse)
async def get_repo_status(
    repo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check analysis status of a repository."""
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    status_messages = {
        AnalysisStatusEnum.PENDING: ("Queued for analysis...", 0),
        AnalysisStatusEnum.INGESTING: ("Fetching repository data from GitHub...", 20),
        AnalysisStatusEnum.EMBEDDING: ("Building vector knowledge base...", 50),
        AnalysisStatusEnum.ANALYZING: ("Running AI agents analysis...", 75),
        AnalysisStatusEnum.COMPLETED: ("Analysis complete!", 100),
        AnalysisStatusEnum.FAILED: ("Analysis failed. Please try again.", 0),
    }

    message, progress = status_messages.get(repo.status, ("Unknown status", 0))

    return RepoStatusResponse(
        repo_id=repo_id,
        status=repo.status,
        message=message,
        progress_percent=progress,
    )


@router.get("/{repo_id}/report")
async def get_report(
    repo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get full analysis report for a repository."""
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repo.status != AnalysisStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=202,
            detail=f"Analysis not complete yet. Current status: {repo.status}"
        )

    analysis_result = await db.execute(
        select(Analysis).where(Analysis.repository_id == repo_id)
    )
    analysis = analysis_result.scalar_one_or_none()

    return {
        "repository": {
            "id": str(repo.id),
            "full_name": repo.full_name,
            "github_url": repo.github_url,
            "language": repo.language,
            "stars": repo.stars,
            "description": repo.description,
        },
        "analysis": {
            "scores": {
                "overall": analysis.overall_score,
                "recruiter": analysis.recruiter_score,
                "code_quality": analysis.code_quality_score,
                "documentation": analysis.documentation_score,
                "testing": analysis.testing_score,
                "devops": analysis.devops_score,
                "architecture": analysis.architecture_score,
            },
            "summary": analysis.summary,
            "strengths": analysis.strengths,
            "weaknesses": analysis.weaknesses,
            "missing_practices": analysis.missing_practices,
            "recruiter_feedback": analysis.recruiter_feedback,
            "mentor_roadmap": analysis.mentor_roadmap,
            "code_analysis": analysis.code_analysis,
            "docs_analysis": analysis.docs_analysis,
            "devops_analysis": analysis.devops_analysis,
            "total_files": analysis.total_files,
            "total_commits": analysis.total_commits,
            "languages": analysis.languages_detected,
        }
    }


@router.get("/public/{share_token}")
async def get_public_report(
    share_token: str,
    db: AsyncSession = Depends(get_db),
):
    """Get public analysis report by share token (no auth needed)."""
    result = await db.execute(
        select(Repository).where(Repository.public_share_token == share_token)
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Report not found")

    analysis_result = await db.execute(
        select(Analysis).where(Analysis.repository_id == repo.id)
    )
    analysis = analysis_result.scalar_one_or_none()

    return {
        "repository": repo.full_name,
        "overall_score": analysis.overall_score if analysis else None,
        "recruiter_score": analysis.recruiter_score if analysis else None,
        "summary": analysis.summary if analysis else None,
    }


@router.get("/my-repos")
async def get_my_repos(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all repositories submitted by current user."""
    result = await db.execute(
        select(Repository)
        .where(Repository.user_id == current_user.id)
        .order_by(Repository.created_at.desc())
    )
    repos = result.scalars().all()
    return repos
