from typing import TypedDict, Optional, Dict, Any
from loguru import logger


class AgentState(TypedDict):
    """State shared across all agents in the pipeline."""
    repo_id:      str
    repo_data:    Dict[str, Any]
    scores:       Dict[str, Any]
    code_result:  Optional[Dict]
    docs_result:  Optional[Dict]
    devops_result: Optional[Dict]
    recruiter_result: Optional[Dict]
    mentor_result: Optional[Dict]
    final_scores: Optional[Dict]
    errors:       list


class AgentOrchestrator:
    """
    Master Orchestrator — runs all 7 agents in the correct order.

    Pipeline:
    1. Ingestion Agent      → fetch GitHub data
    2. Embedding Agent      → chunk + store in ChromaDB
    3. Code Agent           → analyze code quality + architecture
    4. Documentation Agent  → analyze docs quality
    5. DevOps Agent         → analyze CI/CD + testing
    6. Recruiter Agent      → simulate hiring evaluation
    7. Mentor Agent         → generate growth roadmap
    """

    def run_all_agents(self, repo_data: dict, repo_id: str) -> dict:
        """Run all analysis agents and combine results."""
        logger.info(f"🤖 Orchestrator starting for {repo_data.get('full_name', repo_id)}")

        state = AgentState(
            repo_id=repo_id,
            repo_data=repo_data,
            scores={},
            code_result=None,
            docs_result=None,
            devops_result=None,
            recruiter_result=None,
            mentor_result=None,
            final_scores=None,
            errors=[],
        )

        # ── Agent 3: Code Understanding ───────────────────
        try:
            from agents.code_understanding_agent import CodeUnderstandingAgent
            state["code_result"] = CodeUnderstandingAgent().run(repo_data, repo_id)
            logger.info("✅ Agent 3 (Code) complete")
        except Exception as e:
            logger.error(f"Agent 3 error: {e}")
            state["errors"].append(f"Code agent: {e}")

        # ── Agent 5: Documentation ────────────────────────
        try:
            from agents.documentation_agent import DocumentationAgent
            state["docs_result"] = DocumentationAgent().run(repo_data)
            logger.info("✅ Agent 5 (Docs) complete")
        except Exception as e:
            logger.error(f"Agent 5 error: {e}")
            state["errors"].append(f"Docs agent: {e}")

        # ── Agent 6: DevOps ───────────────────────────────
        try:
            from agents.devops_agent import DevOpsAgent
            state["devops_result"] = DevOpsAgent().run(repo_data)
            logger.info("✅ Agent 6 (DevOps) complete")
        except Exception as e:
            logger.error(f"Agent 6 error: {e}")
            state["errors"].append(f"DevOps agent: {e}")

        # ── Compute scores from agents ────────────────────
        scores = self._compute_scores(state)
        state["scores"] = scores

        # ── Agent 4: Recruiter ────────────────────────────
        try:
            from agents.recruiter_agent import RecruiterAgent
            state["recruiter_result"] = RecruiterAgent().run(repo_data)
            scores["recruiter"] = state["recruiter_result"].get("confidence_score", scores.get("recruiter", 0))
            logger.info("✅ Agent 4 (Recruiter) complete")
        except Exception as e:
            logger.error(f"Agent 4 error: {e}")
            state["errors"].append(f"Recruiter agent: {e}")

        # ── Agent 7: Mentor ───────────────────────────────
        try:
            from agents.mentor_agent import MentorAgent
            state["mentor_result"] = MentorAgent().run(repo_data, scores)
            logger.info("✅ Agent 7 (Mentor) complete")
        except Exception as e:
            logger.error(f"Agent 7 error: {e}")
            state["errors"].append(f"Mentor agent: {e}")

        # ── Build final output ────────────────────────────
        result = self._build_final_output(state, scores)
        logger.success(f"🎉 Orchestrator complete. Overall: {scores.get('overall', 0)}/100")
        return result

    def _compute_scores(self, state: AgentState) -> dict:
        """Compute final scores from all agent results."""
        scores = {}
        strengths  = []
        weaknesses = []
        missing    = []

        # Code Quality Score
        if state["code_result"]:
            scores["code_quality"]  = state["code_result"].get("code_quality_score", 50)
            scores["architecture"]  = state["code_result"].get("architecture_score", 50)
            strengths  += state["code_result"].get("positive_practices", [])[:2]
            weaknesses += state["code_result"].get("code_smells", [])[:2]
            missing    += state["code_result"].get("refactoring_suggestions", [])[:2]
        else:
            scores["code_quality"] = 50
            scores["architecture"] = 50

        # Documentation Score
        if state["docs_result"]:
            scores["documentation"] = state["docs_result"].get("documentation_score", 50)
            missing += state["docs_result"].get("missing_sections", [])[:2]
            if state["docs_result"].get("has_readme"):
                strengths.append("README file present")
            else:
                weaknesses.append("Missing README file")
        else:
            scores["documentation"] = 50

        # Testing + DevOps Score
        if state["devops_result"]:
            scores["testing"] = state["devops_result"].get("testing_score", 50)
            scores["devops"]  = state["devops_result"].get("devops_score", 50)
            missing   += state["devops_result"].get("missing_practices", [])[:2]
            if state["devops_result"].get("has_ci_cd"):
                strengths.append("CI/CD pipeline configured")
            else:
                weaknesses.append("No CI/CD pipeline found")
            if state["devops_result"].get("has_docker"):
                strengths.append("Docker configuration found")
            if state["devops_result"].get("has_unit_tests"):
                strengths.append("Unit tests present")
            else:
                weaknesses.append("No unit tests found")
        else:
            scores["testing"] = 50
            scores["devops"]  = 50

        # Overall Score
        scores["overall"] = round(
            scores.get("code_quality",  50) * 0.25 +
            scores.get("documentation", 50) * 0.20 +
            scores.get("testing",       50) * 0.20 +
            scores.get("devops",        50) * 0.15 +
            scores.get("architecture",  50) * 0.20
        )
        scores["recruiter"] = round(scores["overall"] * 0.9)

        # Summary
        overall = scores["overall"]
        verdict = "strong and production-ready" if overall >= 80 else \
                  "solid with room for improvement" if overall >= 60 else \
                  "showing potential but needs work"

        scores["summary"] = (
            f"This repository is {verdict} with an overall score of {overall}/100. "
            f"Code quality: {scores['code_quality']}/100, "
            f"Documentation: {scores['documentation']}/100, "
            f"Testing: {scores['testing']}/100, "
            f"Architecture: {scores['architecture']}/100."
        )
        scores["strengths"]         = list(dict.fromkeys(strengths))[:6]
        scores["weaknesses"]        = list(dict.fromkeys(weaknesses))[:6]
        scores["missing_practices"] = list(dict.fromkeys(missing))[:6]

        return scores

    def _build_final_output(self, state: AgentState, scores: dict) -> dict:
        return {
            "scores":            scores,
            "code_analysis":     state["code_result"],
            "docs_analysis":     state["docs_result"],
            "devops_analysis":   state["devops_result"],
            "recruiter_feedback": state["recruiter_result"],
            "mentor_roadmap":    state["mentor_result"],
            "errors":            state["errors"],
        }
