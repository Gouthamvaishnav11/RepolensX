import ollama
import json
from loguru import logger
from config import settings


MENTOR_PROMPT = """You are a senior engineering mentor helping a developer improve their GitHub repository.
Analyze this repository and create a personalized growth roadmap.

## Repository Analysis:
{repo_summary}

## Current Scores:
- Overall: {overall}/100
- Code Quality: {code_quality}/100
- Documentation: {documentation}/100
- Testing: {testing}/100
- DevOps: {devops}/100
- Architecture: {architecture}/100

## Weaknesses Detected:
{weaknesses}

## Missing Practices:
{missing}

Create a practical 30-day improvement roadmap.

Respond in this EXACT JSON format (no markdown, no extra text):
{{
  "developer_level": "Junior / Mid-level / Senior",
  "primary_focus_area": "the most important area to improve",
  "roadmap": {{
    "week_1": {{
      "title": "week title",
      "tasks": ["task 1", "task 2", "task 3"]
    }},
    "week_2": {{
      "title": "week title",
      "tasks": ["task 1", "task 2", "task 3"]
    }},
    "week_3": {{
      "title": "week title",
      "tasks": ["task 1", "task 2", "task 3"]
    }},
    "week_4": {{
      "title": "week title",
      "tasks": ["task 1", "task 2", "task 3"]
    }}
  }},
  "resources": [
    {{"title": "resource name", "type": "article/course/book", "reason": "why this helps"}}
  ],
  "expected_score_after": <number 0-100>,
  "motivational_message": "one encouraging sentence for the developer"
}}"""


class MentorAgent:
    """
    Agent 7 — Personalized Mentor Agent
    Creates developer growth roadmap and skill-gap analysis.
    """

    def run(self, repo_data: dict, scores: dict) -> dict:
        logger.info("🎓 Mentor Agent running...")

        repo_summary = f"""
Repository: {repo_data.get('full_name', '')}
Language: {repo_data.get('language', 'Unknown')}
Total Files: {repo_data.get('total_files', 0)}
Total Commits: {repo_data.get('total_commits', 0)}
Has Tests: {'Yes' if any('test' in f['path'].lower() for f in repo_data.get('code_files', [])) else 'No'}
Has CI/CD: {'Yes' if repo_data.get('workflows') else 'No'}
Has Docker: {'Yes' if any('docker' in f['path'].lower() for f in repo_data.get('code_files', [])) else 'No'}
Folder Structure: {', '.join(repo_data.get('file_tree', {}).get('top_folders', [])[:6])}
"""

        prompt = MENTOR_PROMPT.format(
            repo_summary=repo_summary,
            overall=scores.get('overall', 0),
            code_quality=scores.get('code_quality', 0),
            documentation=scores.get('documentation', 0),
            testing=scores.get('testing', 0),
            devops=scores.get('devops', 0),
            architecture=scores.get('architecture', 0),
            weaknesses='\n'.join(f"- {w}" for w in scores.get('weaknesses', [])),
            missing='\n'.join(f"- {m}" for m in scores.get('missing_practices', [])),
        )

        try:
            response = ollama.chat(
                model=settings.OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.3, "num_predict": 800},
            )
            content = response["message"]["content"].strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            logger.success("✅ Mentor Agent complete")
            return result

        except Exception as e:
            logger.error(f"Mentor Agent error: {e}")
            return self._fallback(scores)

    def _fallback(self, scores: dict) -> dict:
        overall = scores.get('overall', 0)
        return {
            "developer_level": "Mid-level" if overall >= 60 else "Junior",
            "primary_focus_area": "Testing and Documentation",
            "roadmap": {
                "week_1": {"title": "Add Tests", "tasks": ["Write unit tests", "Set up pytest", "Aim for 60% coverage"]},
                "week_2": {"title": "Improve Docs", "tasks": ["Improve README", "Add docstrings", "Add setup guide"]},
                "week_3": {"title": "Add CI/CD", "tasks": ["Add GitHub Actions", "Auto-run tests", "Add linting"]},
                "week_4": {"title": "Refactor Code", "tasks": ["Improve folder structure", "Add type hints", "Remove duplication"]},
            },
            "resources": [
                {"title": "pytest documentation", "type": "article", "reason": "Learn testing"},
                {"title": "GitHub Actions guide", "type": "course", "reason": "Learn CI/CD"},
            ],
            "expected_score_after": min(overall + 25, 100),
            "motivational_message": "Every great developer started somewhere — keep building!",
        }
