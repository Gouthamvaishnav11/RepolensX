from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from models.database import get_db
from models.db_models import User, Repository, Analysis, AnalysisStatusEnum
from api.middleware.auth import get_current_user

router = APIRouter(prefix="/compare", tags=["Compare"])


@router.get("/{repo_id_1}/{repo_id_2}")
async def compare_repositories(
    repo_id_1: UUID,
    repo_id_2: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compare two analyzed repositories side by side."""

    async def get_repo_with_analysis(repo_id):
        r = await db.execute(
            select(Repository).where(
                Repository.id == repo_id,
                Repository.user_id == current_user.id,
            )
        )
        repo = r.scalar_one_or_none()
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_id} not found")
        if repo.status != AnalysisStatusEnum.COMPLETED:
            raise HTTPException(status_code=400, detail=f"{repo.full_name} not analyzed yet")
        a = await db.execute(select(Analysis).where(Analysis.repository_id == repo_id))
        analysis = a.scalar_one_or_none()
        return repo, analysis

    repo1, analysis1 = await get_repo_with_analysis(repo_id_1)
    repo2, analysis2 = await get_repo_with_analysis(repo_id_2)

    def scores(a):
        return {
            "overall":       a.overall_score or 0,
            "recruiter":     a.recruiter_score or 0,
            "code_quality":  a.code_quality_score or 0,
            "documentation": a.documentation_score or 0,
            "testing":       a.testing_score or 0,
            "devops":        a.devops_score or 0,
            "architecture":  a.architecture_score or 0,
        }

    s1 = scores(analysis1)
    s2 = scores(analysis2)

    # Determine winner per category
    comparison = {}
    for key in s1:
        comparison[key] = {
            "repo1": s1[key],
            "repo2": s2[key],
            "winner": repo1.full_name if s1[key] >= s2[key] else repo2.full_name,
            "diff": round(abs(s1[key] - s2[key]), 1),
        }

    # Overall winner
    overall_winner = repo1.full_name if s1["overall"] >= s2["overall"] else repo2.full_name

    # Insights
    insights = []
    for key, data in comparison.items():
        if data["diff"] > 20:
            better = data["winner"]
            worse = repo2.full_name if better == repo1.full_name else repo1.full_name
            insights.append(f"{better} significantly outperforms {worse} in {key.replace('_', ' ')} by {data['diff']} points")

    return {
        "repo1": {
            "id":        str(repo1.id),
            "full_name": repo1.full_name,
            "language":  repo1.language,
            "stars":     repo1.stars,
            "scores":    s1,
            "summary":   analysis1.summary,
            "strengths": analysis1.strengths,
        },
        "repo2": {
            "id":        str(repo2.id),
            "full_name": repo2.full_name,
            "language":  repo2.language,
            "stars":     repo2.stars,
            "scores":    s2,
            "summary":   analysis2.summary,
            "strengths": analysis2.strengths,
        },
        "comparison":     comparison,
        "overall_winner": overall_winner,
        "insights":       insights[:5],
    }
