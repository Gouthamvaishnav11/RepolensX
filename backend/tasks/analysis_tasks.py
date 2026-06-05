import asyncio
import json
from loguru import logger


def run_full_analysis(repo_id: str, user_id: str) -> dict:
    from models.database import SyncSessionLocal
    from models.db_models import Repository, Analysis, AnalysisStatusEnum
    from sqlalchemy import select

    logger.info(f"Analysis start: {repo_id}")

    with SyncSessionLocal() as db:
        repo = db.execute(
            select(Repository).where(Repository.id == repo_id)
        ).scalar_one_or_none()
        if not repo:
            return {"status": "failed", "error": "Repository not found"}

        analysis = db.execute(
            select(Analysis).where(Analysis.repository_id == repo_id)
        ).scalar_one_or_none()

        try:
            # ── STAGE 1: Ingestion ────────────────────────
            _set_status(db, repo, AnalysisStatusEnum.INGESTING)
            from agents.ingestion_agent import IngestionAgent
            repo_data = asyncio.run(IngestionAgent().run(repo.owner, repo.name))

            repo.description = (repo_data.get("description") or "")[:500]
            repo.language    = repo_data.get("language", "")
            repo.stars       = repo_data.get("stars", 0)
            repo.forks       = repo_data.get("forks", 0)
            if analysis:
                analysis.total_files        = repo_data.get("total_files", 0)
                analysis.total_commits      = repo_data.get("total_commits", 0)
                analysis.total_issues       = repo_data.get("total_issues", 0)
                analysis.languages_detected = repo_data.get("languages", {})
            db.commit()
            logger.info("Stage 1 done")

            # ── STAGE 2: Embedding ────────────────────────
            _set_status(db, repo, AnalysisStatusEnum.EMBEDDING)
            from agents.embedding_agent import EmbeddingAgent
            collection_name = EmbeddingAgent().run(repo_data, repo_id)
            repo.chroma_collection_id = collection_name
            db.commit()
            logger.info("Stage 2 done")

            # ── STAGE 3: Single-pass LLM analysis ────────
            _set_status(db, repo, AnalysisStatusEnum.ANALYZING)
            scores  = _rule_scores(repo_data)
            result  = _llm_analysis(repo_data, scores)

            if analysis:
                s = result["scores"]
                analysis.overall_score       = s["overall"]
                analysis.recruiter_score     = s["recruiter"]
                analysis.code_quality_score  = s["code_quality"]
                analysis.documentation_score = s["documentation"]
                analysis.testing_score       = s["testing"]
                analysis.devops_score        = s["devops"]
                analysis.architecture_score  = s["architecture"]
                analysis.summary             = s["summary"]
                analysis.strengths           = s["strengths"]
                analysis.weaknesses          = s["weaknesses"]
                analysis.missing_practices   = s["missing_practices"]
                analysis.recruiter_feedback  = result["recruiter_feedback"]
                analysis.mentor_roadmap      = result["mentor_roadmap"]
            db.commit()
            logger.info("Stage 3 done")

            # ── Done ──────────────────────────────────────
            from datetime import datetime
            repo.status = AnalysisStatusEnum.COMPLETED
            if analysis:
                analysis.completed_at = datetime.utcnow()
            db.commit()

            overall = result["scores"]["overall"]
            logger.success(f"Analysis done: {repo.full_name} — {overall}/100")
            return {"status": "completed", "repo_id": repo_id, "score": overall}

        except Exception as e:
            repo.status = AnalysisStatusEnum.FAILED
            db.commit()
            logger.error(f"Analysis failed: {e}")
            import traceback; traceback.print_exc()
            return {"status": "failed", "error": str(e)}


def _set_status(db, repo, status):
    repo.status = status
    db.commit()


# ── Rule-based scoring — zero LLM, runs in <100ms ─────────

def _rule_scores(r: dict) -> dict:
    readme     = r.get("readme", "")
    code_files = r.get("code_files", [])
    code_paths = " ".join(f["path"] for f in code_files).lower()
    file_tree  = r.get("file_tree", {})
    folders    = " ".join(file_tree.get("top_folders", []))
    file_types = file_tree.get("file_types", {})
    workflows  = r.get("workflows", [])
    commits    = r.get("total_commits", 0)
    strengths, weaknesses, missing = [], [], []

    # Documentation
    doc = 0
    if readme:
        doc = 40
        if len(readme) > 500:  doc += 15
        if len(readme) > 1500: doc += 15
        if "install" in readme.lower(): doc += 15
        if "usage"   in readme.lower(): doc += 10
        if "license" in readme.lower(): doc += 5
        strengths.append("README is present")
    else:
        weaknesses.append("No README file found")
        missing.append("Add a README with setup instructions")

    # Testing
    has_tests = any(t in code_paths for t in ["test", "spec", "__tests__"])
    has_ci    = bool(workflows)
    test = (60 if has_tests else 0) + (40 if has_ci else 0)
    if has_tests: strengths.append("Unit tests found")
    else:         weaknesses.append("No unit tests found"); missing.append("Add unit tests")
    if has_ci:    strengths.append("CI/CD pipeline configured")
    else:         missing.append("Add GitHub Actions")

    # DevOps
    has_docker = "dockerfile" in file_types or "docker-compose" in code_paths
    has_env    = ".env.example" in code_paths or "env.example" in code_paths
    devops = (40 if has_ci else 0) + (30 if has_docker else 0) + \
             (15 if has_env else 0) + (15 if ".gitignore" in code_paths else 0)
    if has_docker: strengths.append("Docker configured")
    else:          missing.append("Add Dockerfile")
    if not has_env: missing.append("Add .env.example")

    # Code quality
    code = 40 + (20 if commits > 10 else 0) + (15 if commits > 50 else 0) + \
           (15 if len(code_files) > 5 else 0) + (10 if r.get("license") else 0)

    # Architecture
    good = ["src","lib","utils","models","routes","services","controllers","api","tests","config"]
    matched = [p for p in good if p in folders.lower()]
    arch = 30 + min(len(matched) * 8, 50)
    if len(matched) >= 3: strengths.append(f"Good structure: {', '.join(matched[:3])}")
    elif len(matched) < 2: weaknesses.append("Flat project structure — organise into folders")

    overall = round(
        min(code, 100)  * 0.25 +
        min(doc,  100)  * 0.20 +
        min(test, 100)  * 0.20 +
        min(devops,100) * 0.15 +
        min(arch, 100)  * 0.20
    )
    recruiter = min(round(overall * 0.9 + (5 if commits > 20 else 0)), 100)

    v = "strong" if overall >= 80 else "solid with room to improve" if overall >= 60 else "needs significant improvement"
    return {
        "overall":          overall,
        "recruiter":        recruiter,
        "code_quality":     min(code,  100),
        "documentation":    min(doc,   100),
        "testing":          min(test,  100),
        "devops":           min(devops,100),
        "architecture":     min(arch,  100),
        "summary":          f"{r.get('full_name','This repo')} scored {overall}/100 and is {v}.",
        "strengths":        strengths[:5],
        "weaknesses":       weaknesses[:5],
        "missing_practices":missing[:5],
    }


# ── Single LLM call — all descriptions + roadmap in one go ─

MEGA_PROMPT = """You are a senior engineer reviewing a GitHub repository. Be concise and specific.

{context}

Return ONLY this JSON (no markdown, no extra text):
{{
  "descriptions": {{
    "overall": "2 sentence overall assessment of this specific repository",
    "code_quality": "2 sentence code quality review",
    "documentation": "2 sentence documentation review",
    "testing": "2 sentence testing and reliability review",
    "devops": "2 sentence DevOps and deployment review",
    "architecture": "2 sentence project structure review",
    "recruiter": "2 sentence recruiter perspective on this developer"
  }},
  "recruiter": {{
    "hiring_recommendation": "Strong Yes / Yes / Maybe / No",
    "seniority_level": "Junior / Mid-level / Senior",
    "confidence_score": {overall},
    "green_flags": ["up to 3 specific good things"],
    "red_flags": ["up to 3 specific concerns"]
  }},
  "roadmap": {{
    "developer_level": "Junior / Mid-level / Senior",
    "primary_focus_area": "single most important area to improve",
    "motivational_message": "one encouraging sentence",
    "expected_score_after": {expected},
    "week_1": {{"title": "title", "tasks": ["task1","task2","task3"]}},
    "week_2": {{"title": "title", "tasks": ["task1","task2","task3"]}},
    "week_3": {{"title": "title", "tasks": ["task1","task2","task3"]}},
    "week_4": {{"title": "title", "tasks": ["task1","task2","task3"]}},
    "resources": [{{"title": "name", "type": "article/course/book", "reason": "why"}}]
  }}
}}"""


def _llm_analysis(repo_data: dict, scores: dict) -> dict:
    import ollama
    from config import settings

    context = _compact_context(repo_data, scores)
    prompt  = MEGA_PROMPT.format(
        context=context,
        overall=scores["overall"],
        expected=min(scores["overall"] + 22, 100),
    )

    try:
        resp = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": 1200, "num_ctx": 4096},
        )
        raw = resp["message"]["content"].strip()

        # Strip markdown fences if present
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()

        data = json.loads(raw)
        logger.success("LLM analysis complete")
        return _build_result(scores, data, repo_data)

    except Exception as e:
        logger.error(f"LLM failed ({e}), using rule-based fallback")
        return _fallback_result(scores, repo_data)


def _compact_context(r: dict, s: dict) -> str:
    tree  = r.get("file_tree", {})
    wf    = ", ".join(w.get("name","") for w in r.get("workflows",[])) or "None"
    code  = " ".join(f["path"] for f in r.get("code_files",[]))
    has_t = any(t in code.lower() for t in ["test","spec","__tests__"])
    has_d = "dockerfile" in code.lower() or "docker-compose" in code.lower()
    return (
        f"Repo: {r.get('full_name','')} | Lang: {r.get('language','')} | "
        f"Stars: {r.get('stars',0)} | Commits: {r.get('total_commits',0)} | "
        f"Files: {r.get('total_files',0)}\n"
        f"Has README: {'Yes' if r.get('readme') else 'No'} | "
        f"Has Tests: {'Yes' if has_t else 'No'} | "
        f"CI/CD: {wf} | Docker: {'Yes' if has_d else 'No'}\n"
        f"Folders: {', '.join(tree.get('top_folders',[])[:8])}\n"
        f"Scores: overall={s['overall']} code={s['code_quality']} "
        f"docs={s['documentation']} tests={s['testing']} "
        f"devops={s['devops']} arch={s['architecture']}"
    )


def _build_result(scores: dict, data: dict, repo_data: dict = None) -> dict:
    desc    = data.get("descriptions", {})
    rec     = data.get("recruiter", {})
    rm      = data.get("roadmap", {})

    scores["summary"] = desc.get("overall", scores["summary"])

    code_file_paths = [f["path"] for f in (repo_data or {}).get("code_files", [])]

    recruiter_feedback = {
        "hiring_recommendation": rec.get("hiring_recommendation", "Maybe"),
        "seniority_level":       rec.get("seniority_level", "Mid-level"),
        "confidence_score":      rec.get("confidence_score", scores["overall"]),
        "green_flags":           rec.get("green_flags", []),
        "red_flags":             rec.get("red_flags", []),
        "written_descriptions":  desc,
        "code_file_paths":       code_file_paths,
    }

    mentor_roadmap = {
        "developer_level":      rm.get("developer_level", "Mid-level"),
        "primary_focus_area":   rm.get("primary_focus_area", "Testing"),
        "motivational_message": rm.get("motivational_message", "Keep building!"),
        "expected_score_after": rm.get("expected_score_after", min(scores["overall"]+22, 100)),
        "roadmap": {
            "week_1": rm.get("week_1", {"title": "Add Tests",    "tasks": ["Write unit tests", "Set up pytest", "60% coverage"]}),
            "week_2": rm.get("week_2", {"title": "Improve Docs", "tasks": ["Improve README", "Add docstrings", "Add examples"]}),
            "week_3": rm.get("week_3", {"title": "Add CI/CD",    "tasks": ["GitHub Actions", "Auto-test PRs", "Add linting"]}),
            "week_4": rm.get("week_4", {"title": "Refactor",     "tasks": ["Better structure", "Type hints", "Error handling"]}),
        },
        "resources": rm.get("resources", [
            {"title": "pytest documentation", "type": "article", "reason": "Learn testing best practices"},
            {"title": "GitHub Actions guide", "type": "course",  "reason": "Set up CI/CD pipeline"},
        ]),
    }

    return {
        "scores":             scores,
        "recruiter_feedback": recruiter_feedback,
        "mentor_roadmap":     mentor_roadmap,
    }


def _fallback_result(scores: dict, r: dict) -> dict:
    """Pure rule-based fallback — no LLM needed, always works."""
    o    = scores["overall"]
    rn   = r.get("full_name", "this repository")
    lang = r.get("language", "Unknown")
    cm   = r.get("total_commits", 0)
    good = o >= 70

    desc = {
        "overall":      f"{rn} scored {o}/100. {'The project demonstrates solid engineering practices.' if good else 'The project needs improvements in testing, docs, and DevOps.'}",
        "code_quality": f"Code quality scored {scores['code_quality']}/100. {'The {lang} codebase is organised and follows reasonable conventions.' if scores['code_quality'] >= 60 else 'The code needs better organisation, type hints, and error handling.'}",
        "documentation":f"Documentation scored {scores['documentation']}/100. {'A README is present with useful information.' if scores['documentation'] >= 50 else 'No README found — this makes it very hard for others to use this project.'}",
        "testing":      f"Testing scored {scores['testing']}/100. {'Tests are present which helps catch bugs early.' if scores['testing'] >= 60 else 'No unit tests found. Adding tests is the single highest-impact improvement you can make.'}",
        "devops":       f"DevOps scored {scores['devops']}/100. {'CI/CD and Docker are configured for automated deployments.' if scores['devops'] >= 60 else 'No CI/CD or Docker setup found. Adding GitHub Actions would immediately improve reliability.'}",
        "architecture": f"Architecture scored {scores['architecture']}/100. {'Good folder structure with clear separation of concerns.' if scores['architecture'] >= 60 else 'The project structure is flat. Organising into modules like routes, models, and utils would help.'}",
        "recruiter":    f"{'This developer shows strong practices — this repo would pass a portfolio review.' if good else 'This repo shows potential but needs more polish before being portfolio-ready.'} Score: {o}/100.",
    }

    return {
        "scores": scores,
        "recruiter_feedback": {
            "hiring_recommendation": "Yes" if o >= 70 else "Maybe" if o >= 50 else "No",
            "seniority_level":       "Senior" if o >= 80 else "Mid-level" if o >= 60 else "Junior",
            "confidence_score":      o,
            "green_flags":           scores["strengths"][:3],
            "red_flags":             scores["weaknesses"][:3],
            "written_descriptions":  desc,
        },
        "mentor_roadmap": {
            "developer_level":      "Mid-level" if o >= 60 else "Junior",
            "primary_focus_area":   "Testing & CI/CD",
            "motivational_message": "Every great developer started somewhere — keep building!",
            "expected_score_after": min(o + 22, 100),
            "roadmap": {
                "week_1": {"title": "Add Tests",    "tasks": ["Write unit tests for core features", "Set up pytest", "Aim for 60% code coverage"]},
                "week_2": {"title": "Improve Docs", "tasks": ["Rewrite README with clear setup guide", "Add docstrings to all functions", "Add usage examples"]},
                "week_3": {"title": "Add CI/CD",    "tasks": ["Add GitHub Actions workflow", "Auto-run tests on every PR", "Add flake8 linting"]},
                "week_4": {"title": "Refactor",     "tasks": ["Organise into proper folder structure", "Add type hints to all functions", "Add proper error handling"]},
            },
            "resources": [
                {"title": "pytest documentation", "type": "article", "reason": "Learn testing best practices"},
                {"title": "GitHub Actions guide", "type": "course",  "reason": "Set up CI/CD pipeline"},
                {"title": "Clean Code by Robert Martin", "type": "book", "reason": "Write better, maintainable code"},
            ],
        },
    }
