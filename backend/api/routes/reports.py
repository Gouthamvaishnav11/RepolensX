from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from models.database import get_db
from models.db_models import User, Repository, Analysis, AnalysisStatusEnum
from api.middleware.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{repo_id}/pdf")
async def download_pdf_report(
    repo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download full analysis report as PDF."""
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
        raise HTTPException(status_code=400, detail="Analysis not complete yet")

    analysis_result = await db.execute(
        select(Analysis).where(Analysis.repository_id == repo_id)
    )
    analysis = analysis_result.scalar_one_or_none()

    try:
        from utils.pdf_generator import generate_pdf_report

        repo_dict = {
            "full_name":   repo.full_name,
            "language":    repo.language,
            "description": repo.description,
            "stars":       repo.stars,
            "forks":       repo.forks,
        }

        analysis_dict = {
            "overall_score":       analysis.overall_score,
            "recruiter_score":     analysis.recruiter_score,
            "code_quality_score":  analysis.code_quality_score,
            "documentation_score": analysis.documentation_score,
            "testing_score":       analysis.testing_score,
            "devops_score":        analysis.devops_score,
            "architecture_score":  analysis.architecture_score,
            "summary":             analysis.summary,
            "strengths":           analysis.strengths,
            "weaknesses":          analysis.weaknesses,
            "missing_practices":   analysis.missing_practices,
            "recruiter_feedback":  analysis.recruiter_feedback,
            "mentor_roadmap":      analysis.mentor_roadmap,
            "total_files":         analysis.total_files,
            "total_commits":       analysis.total_commits,
        }

        pdf_bytes = generate_pdf_report(repo_dict, analysis_dict)

        filename = f"repolens-{repo.name}-report.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
