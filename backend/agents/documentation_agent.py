import ollama
import json
from loguru import logger
from config import settings


DOCS_PROMPT = """You are a technical documentation expert reviewing a GitHub repository's documentation quality.

## README Content:
{readme}

## Documentation Files Found:
{doc_files}

## Repository Info:
Name: {repo_name}
Description: {description}

Analyze the documentation quality and respond in this EXACT JSON format (no markdown):
{{
  "documentation_score": <number 0-100>,
  "has_readme": true/false,
  "has_setup_instructions": true/false,
  "has_usage_examples": true/false,
  "has_api_docs": true/false,
  "has_contribution_guide": true/false,
  "has_license": true/false,
  "readme_quality": "poor/basic/good/excellent",
  "missing_sections": ["list of missing sections"],
  "improvements": ["specific improvement suggestions"],
  "onboarding_rating": <number 1-10>,
  "summary": "2-3 sentence documentation review"
}}"""


class DocumentationAgent:
    """
    Agent 5 — Documentation Intelligence Agent
    Analyzes README, wikis, inline docs, and onboarding quality.
    """

    def run(self, repo_data: dict) -> dict:
        logger.info("📄 Documentation Agent running...")

        readme = repo_data.get("readme", "")
        doc_files = repo_data.get("doc_files", [])

        # Build doc files summary
        doc_summary = ""
        for f in doc_files[:5]:
            doc_summary += f"\n- {f['path']} ({len(f.get('content', ''))} chars)"

        prompt = DOCS_PROMPT.format(
            readme=readme[:3000] if readme else "No README found",
            doc_files=doc_summary or "No documentation files found",
            repo_name=repo_data.get("full_name", ""),
            description=repo_data.get("description", ""),
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
            logger.success("✅ Documentation Agent complete")
            return result

        except Exception as e:
            logger.error(f"Documentation Agent error: {e}")
            return self._fallback(repo_data)

    def _fallback(self, repo_data: dict) -> dict:
        readme = repo_data.get("readme", "")
        score = 0
        missing = []

        if readme:
            score += 40
            if "install" in readme.lower(): score += 15
            if "usage" in readme.lower(): score += 15
            if "license" in readme.lower(): score += 10
            if len(readme) > 1000: score += 10
            if len(readme) > 2000: score += 10
        else:
            missing.append("README.md")

        if not any("contributing" in f["path"].lower() for f in repo_data.get("doc_files", [])):
            missing.append("CONTRIBUTING.md")
        if not any("license" in f["path"].lower() for f in repo_data.get("doc_files", [])):
            missing.append("LICENSE file")

        return {
            "documentation_score": min(score, 100),
            "has_readme": bool(readme),
            "has_setup_instructions": "install" in readme.lower() if readme else False,
            "has_usage_examples": "usage" in readme.lower() if readme else False,
            "has_api_docs": False,
            "has_contribution_guide": False,
            "has_license": "license" in readme.lower() if readme else False,
            "readme_quality": "good" if score >= 70 else "basic" if score >= 40 else "poor",
            "missing_sections": missing,
            "improvements": ["Add more code examples", "Document API endpoints", "Add contribution guide"],
            "onboarding_rating": min(score // 10, 10),
            "summary": f"Documentation scored {score}/100. {'README is present but needs improvement.' if readme else 'No README found.'}",
        }
