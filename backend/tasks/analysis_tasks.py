import asyncio
from loguru import logger


def run_full_analysis(repo_id: str, user_id: str):
    """Full 7-agent analysis pipeline using Orchestrator."""
    from models.database import SyncSessionLocal
    from models.db_models import Repository, Analysis, AnalysisStatusEnum
    from sqlalchemy import select

    logger.info(f"🚀 Starting full analysis for repo_id={repo_id}")

    with SyncSessionLocal() as db:
        repo = db.execute(select(Repository).where(Repository.id == repo_id)).scalar_one_or_none()
        if not repo:
            return {"status": "failed", "error": "Repository not found"}

        analysis = db.execute(select(Analysis).where(Analysis.repository_id == repo_id)).scalar_one_or_none()

        try:
            # ── STAGE 1: Ingestion ────────────────────────
            repo.status = AnalysisStatusEnum.INGESTING
            db.commit()
            logger.info("📥 Stage 1: Ingestion Agent...")

            from agents.ingestion_agent import IngestionAgent
            repo_data = asyncio.run(IngestionAgent().run(repo.owner, repo.name))

            repo.description = (repo_data.get("description", "") or "")[:500]
            repo.language    = repo_data.get("language", "")
            repo.stars       = repo_data.get("stars", 0)
            repo.forks       = repo_data.get("forks", 0)

            if analysis:
                analysis.total_files   = repo_data.get("total_files", 0)
                analysis.total_commits = repo_data.get("total_commits", 0)
                analysis.total_issues  = repo_data.get("total_issues", 0)
                analysis.languages_detected = repo_data.get("languages", {})
            db.commit()
            logger.info("✅ Stage 1 complete")

            # ── STAGE 2: Embedding ────────────────────────
            repo.status = AnalysisStatusEnum.EMBEDDING
            db.commit()
            logger.info("🧠 Stage 2: Embedding Agent...")

            from agents.embedding_agent import EmbeddingAgent
            collection_name = EmbeddingAgent().run(repo_data, repo_id)
            repo.chroma_collection_id = collection_name
            db.commit()
            logger.info("✅ Stage 2 complete")

            # ── STAGE 3: All Agents via Orchestrator ──────
            repo.status = AnalysisStatusEnum.ANALYZING
            db.commit()
            logger.info("🤖 Stage 3: Running all 7 agents via Orchestrator...")

            from agents.orchestrator import AgentOrchestrator
            result = AgentOrchestrator().run_all_agents(repo_data, repo_id)

            scores = result["scores"]

            if analysis:
                analysis.overall_score       = scores.get("overall", 0)
                analysis.recruiter_score     = scores.get("recruiter", 0)
                analysis.code_quality_score  = scores.get("code_quality", 0)
                analysis.documentation_score = scores.get("documentation", 0)
                analysis.testing_score       = scores.get("testing", 0)
                analysis.devops_score        = scores.get("devops", 0)
                analysis.architecture_score  = scores.get("architecture", 0)
                analysis.summary             = scores.get("summary", "")
                analysis.strengths           = scores.get("strengths", [])
                analysis.weaknesses          = scores.get("weaknesses", [])
                analysis.missing_practices   = scores.get("missing_practices", [])
                analysis.recruiter_feedback  = result.get("recruiter_feedback")
                analysis.mentor_roadmap      = result.get("mentor_roadmap")
                analysis.code_analysis       = result.get("code_analysis")
                analysis.docs_analysis       = result.get("docs_analysis")
                analysis.devops_analysis     = result.get("devops_analysis")
            db.commit()
            logger.info("✅ Stage 3 complete")

            # ── Done ──────────────────────────────────────
            from datetime import datetime
            repo.status = AnalysisStatusEnum.COMPLETED
            if analysis:
                analysis.completed_at = datetime.utcnow()
            db.commit()

            logger.success(f"🎉 Analysis complete for {repo.full_name} — Score: {scores.get('overall', 0)}/100")
            return {"status": "completed", "repo_id": repo_id, "score": scores.get("overall", 0)}

        except Exception as e:
            repo.status = AnalysisStatusEnum.FAILED
            db.commit()
            logger.error(f"❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}
