import asyncio
from loguru import logger


def run_full_analysis(repo_id: str, user_id: str):
    from models.database import SyncSessionLocal
    from models.db_models import Repository, Analysis, AnalysisStatusEnum
    from sqlalchemy import select

    logger.info(f"Starting analysis for repo_id={repo_id}")

    with SyncSessionLocal() as db:
        repo = db.execute(select(Repository).where(Repository.id == repo_id)).scalar_one_or_none()
        if not repo:
            return {"status": "failed", "error": "Repository not found"}

        analysis = db.execute(select(Analysis).where(Analysis.repository_id == repo_id)).scalar_one_or_none()

        try:
            # STAGE 1: Ingestion
            repo.status = AnalysisStatusEnum.INGESTING
            db.commit()
            logger.info("Stage 1: Ingestion Agent...")

            from agents.ingestion_agent import IngestionAgent
            repo_data = asyncio.run(IngestionAgent().run(repo.owner, repo.name))

            repo.description = (repo_data.get("description", "") or "")[:500]
            repo.language = repo_data.get("language", "")
            repo.stars = repo_data.get("stars", 0)
            repo.forks = repo_data.get("forks", 0)

            if analysis:
                analysis.total_files = repo_data.get("total_files", 0)
                analysis.total_commits = repo_data.get("total_commits", 0)
                analysis.total_issues = repo_data.get("total_issues", 0)
                analysis.languages_detected = repo_data.get("languages", {})
            db.commit()
            logger.info("Stage 1 complete")

            # STAGE 2: Embedding
            repo.status = AnalysisStatusEnum.EMBEDDING
            db.commit()
            logger.info("Stage 2: Embedding Agent...")

            from agents.embedding_agent import EmbeddingAgent
            collection_name = EmbeddingAgent().run(repo_data, repo_id)
            repo.chroma_collection_id = collection_name
            db.commit()
            logger.info("Stage 2 complete")

            # STAGE 3: Analysis Agents
            repo.status = AnalysisStatusEnum.ANALYZING
            db.commit()
            logger.info("Stage 3: Analysis Agents...")

            # Basic scoring
            scores = _run_basic_analysis(repo_data)

            # Agent 4: Recruiter
            try:
                from agents.recruiter_agent import RecruiterAgent
                recruiter_result = RecruiterAgent().run(repo_data)
                scores["recruiter"] = recruiter_result.get("confidence_score", scores.get("recruiter", 0))
                if analysis:
                    analysis.recruiter_feedback = recruiter_result
            except Exception as e:
                logger.error(f"Recruiter agent error: {e}")

            # Agent 7: Mentor
            try:
                from agents.mentor_agent import MentorAgent
                mentor_result = MentorAgent().run(repo_data, scores)
                if analysis:
                    analysis.mentor_roadmap = mentor_result
            except Exception as e:
                logger.error(f"Mentor agent error: {e}")

            if analysis:
                analysis.overall_score = scores.get("overall", 0)
                analysis.recruiter_score = scores.get("recruiter", 0)
                analysis.code_quality_score = scores.get("code_quality", 0)
                analysis.documentation_score = scores.get("documentation", 0)
                analysis.testing_score = scores.get("testing", 0)
                analysis.devops_score = scores.get("devops", 0)
                analysis.architecture_score = scores.get("architecture", 0)
                analysis.summary = scores.get("summary", "")
                analysis.strengths = scores.get("strengths", [])
                analysis.weaknesses = scores.get("weaknesses", [])
                analysis.missing_practices = scores.get("missing_practices", [])
            db.commit()

            from datetime import datetime
            repo.status = AnalysisStatusEnum.COMPLETED
            if analysis:
                analysis.completed_at = datetime.utcnow()
            db.commit()

            logger.info(f"Analysis complete for {repo.full_name}")
            return {"status": "completed", "repo_id": repo_id}

        except Exception as e:
            repo.status = AnalysisStatusEnum.FAILED
            db.commit()
            logger.error(f"Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "failed", "error": str(e)}


def _run_basic_analysis(repo_data: dict) -> dict:
    scores = {}
    strengths = []
    weaknesses = []
    missing = []

    readme = repo_data.get("readme", "")
    doc_score = 0
    if readme:
        doc_score += 40
        if len(readme) > 500: doc_score += 20
        if len(readme) > 1500: doc_score += 15
        if "install" in readme.lower(): doc_score += 10
        if "usage" in readme.lower(): doc_score += 10
        if "license" in readme.lower(): doc_score += 5
        strengths.append("README file present")
    else:
        weaknesses.append("Missing README file")
        missing.append("Add a README with setup instructions")
    scores["documentation"] = min(doc_score, 100)

    file_tree = repo_data.get("file_tree", {})
    folders = " ".join(file_tree.get("top_folders", []))
    file_types = file_tree.get("file_types", {})
    code_paths = " ".join(f["path"] for f in repo_data.get("code_files", [])).lower()

    test_score = 0
    if any(t in code_paths for t in ["test", "spec", "__tests__"]):
        test_score += 60
        strengths.append("Test files detected")
    else:
        missing.append("Add unit tests")
        weaknesses.append("No test files found")

    workflows = repo_data.get("workflows", [])
    if workflows:
        test_score += 40
        strengths.append(f"CI/CD configured ({len(workflows)} workflow(s))")
    else:
        missing.append("Add GitHub Actions CI/CD")
    scores["testing"] = min(test_score, 100)

    devops_score = 0
    if workflows: devops_score += 40
    if "dockerfile" in file_types or "docker-compose" in code_paths:
        devops_score += 30
        strengths.append("Docker configuration found")
    else:
        missing.append("Add Dockerfile")
    if ".env.example" in code_paths: devops_score += 15
    if ".gitignore" in code_paths: devops_score += 15
    scores["devops"] = min(devops_score, 100)

    total_commits = repo_data.get("total_commits", 0)
    code_score = 40
    if total_commits > 10: code_score += 20
    if total_commits > 50: code_score += 15
    if len(repo_data.get("code_files", [])) > 5: code_score += 15
    if repo_data.get("license"): code_score += 10
    scores["code_quality"] = min(code_score, 100)

    arch_score = 30
    good_patterns = ["src", "lib", "utils", "models", "routes", "services", "controllers", "api", "tests", "config"]
    matched = [p for p in good_patterns if p in folders.lower()]
    arch_score += min(len(matched) * 8, 50)
    if len(matched) >= 3: strengths.append(f"Good folder structure: {', '.join(matched[:4])}")
    elif len(matched) < 2: weaknesses.append("Consider organizing into proper folders")
    scores["architecture"] = min(arch_score, 100)

    scores["overall"] = round(
        scores["documentation"] * 0.20 + scores["testing"] * 0.20 +
        scores["devops"] * 0.15 + scores["code_quality"] * 0.25 + scores["architecture"] * 0.20
    )
    scores["recruiter"] = round(scores["overall"] * 0.9 + (5 if total_commits > 20 else 0))

    overall = scores["overall"]
    verdict = "strong" if overall >= 80 else "solid with room to improve" if overall >= 60 else "needs work"
    scores["summary"] = (
        f"This repository scores {overall}/100 overall and is {verdict}. "
        f"Docs: {scores['documentation']}/100, Tests: {scores['testing']}/100, Architecture: {scores['architecture']}/100."
    )
    scores["strengths"] = strengths[:6]
    scores["weaknesses"] = weaknesses[:6]
    scores["missing_practices"] = missing[:6]
    return scores
