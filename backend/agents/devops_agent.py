import ollama
import json
from loguru import logger
from config import settings


DEVOPS_PROMPT = """You are a DevOps and QA expert reviewing a GitHub repository's testing and deployment setup.

## Repository Info:
Name: {repo_name}
Language: {language}

## File Structure:
{file_structure}

## CI/CD Workflows Found:
{workflows}

## Code Files (test-related):
{test_files}

## File Types Present:
{file_types}

Analyze the testing and DevOps setup. Respond in this EXACT JSON format (no markdown):
{{
  "testing_score": <number 0-100>,
  "devops_score": <number 0-100>,
  "has_unit_tests": true/false,
  "has_integration_tests": true/false,
  "has_ci_cd": true/false,
  "has_docker": true/false,
  "has_docker_compose": true/false,
  "has_env_example": true/false,
  "has_gitignore": true/false,
  "has_linting": true/false,
  "ci_cd_tools": ["list of CI/CD tools detected"],
  "test_frameworks": ["list of test frameworks detected"],
  "missing_practices": ["list of missing DevOps practices"],
  "recommendations": ["specific recommendations"],
  "production_readiness": "not-ready/basic/moderate/production-ready",
  "summary": "2-3 sentence DevOps review"
}}"""


class DevOpsAgent:
    """
    Agent 6 — Testing & DevOps Agent
    Evaluates CI/CD, testing setup, Docker, deployment readiness.
    """

    def run(self, repo_data: dict) -> dict:
        logger.info("⚙️ DevOps Agent running...")

        file_tree = repo_data.get("file_tree", {})
        workflows = repo_data.get("workflows", [])
        code_files = repo_data.get("code_files", [])

        # Find test-related files
        test_files = [f["path"] for f in code_files
                      if any(t in f["path"].lower() for t in ["test", "spec", "__tests__"])]

        # Workflows summary
        workflows_summary = "\n".join(
            f"- {w.get('name', '')}: {w.get('path', '')}" for w in workflows
        ) or "No workflows found"

        # File types
        file_types = ", ".join(
            f".{k}" for k in list(file_tree.get("file_types", {}).keys())[:10]
        )

        # File structure
        folders = "\n".join(file_tree.get("top_folders", [])[:15])

        prompt = DEVOPS_PROMPT.format(
            repo_name=repo_data.get("full_name", ""),
            language=repo_data.get("language", "Unknown"),
            file_structure=folders or "No folder structure",
            workflows=workflows_summary,
            test_files="\n".join(test_files[:10]) or "No test files found",
            file_types=file_types or "Unknown",
        )

        try:
            response = ollama.chat(
                model=settings.OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 500},
            )
            content = response["message"]["content"].strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            logger.success("✅ DevOps Agent complete")
            return result

        except Exception as e:
            logger.error(f"DevOps Agent error: {e}")
            return self._fallback(repo_data)

    def _fallback(self, repo_data: dict) -> dict:
        file_tree = repo_data.get("file_tree", {})
        code_paths = " ".join(f["path"] for f in repo_data.get("code_files", [])).lower()
        file_types = file_tree.get("file_types", {})
        workflows = repo_data.get("workflows", [])

        has_tests = any(t in code_paths for t in ["test", "spec", "__tests__"])
        has_docker = "dockerfile" in file_types or "docker-compose" in code_paths
        has_ci = bool(workflows)
        has_env = ".env.example" in code_paths
        has_gitignore = ".gitignore" in code_paths

        test_score = (60 if has_tests else 0) + (40 if has_ci else 0)
        devops_score = (40 if has_ci else 0) + (30 if has_docker else 0) + (15 if has_env else 0) + (15 if has_gitignore else 0)

        missing = []
        if not has_tests: missing.append("Add unit tests")
        if not has_ci: missing.append("Add CI/CD pipeline")
        if not has_docker: missing.append("Add Dockerfile")
        if not has_env: missing.append("Add .env.example")

        return {
            "testing_score": min(test_score, 100),
            "devops_score": min(devops_score, 100),
            "has_unit_tests": has_tests,
            "has_integration_tests": False,
            "has_ci_cd": has_ci,
            "has_docker": has_docker,
            "has_docker_compose": "docker-compose" in code_paths,
            "has_env_example": has_env,
            "has_gitignore": has_gitignore,
            "has_linting": False,
            "ci_cd_tools": [w.get("name", "") for w in workflows],
            "test_frameworks": [],
            "missing_practices": missing,
            "recommendations": missing,
            "production_readiness": "production-ready" if devops_score >= 80 else "moderate" if devops_score >= 50 else "basic" if devops_score >= 20 else "not-ready",
            "summary": f"Testing: {test_score}/100. DevOps: {devops_score}/100. {'CI/CD configured.' if has_ci else 'No CI/CD found.'} {'Docker ready.' if has_docker else 'No Docker setup.'}",
        }
