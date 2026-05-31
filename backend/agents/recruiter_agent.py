import ollama
from loguru import logger
from config import settings


RECRUITER_PROMPT = """You are a senior technical recruiter at a top tech company (Google, Microsoft, or a leading AI startup).
You are evaluating a GitHub repository to decide if this developer is worth interviewing.

## Repository Data:
{repo_summary}

## Retrieved Code Context:
{code_context}

Evaluate this repository as a recruiter would. Be honest, direct, and specific.

Respond in this EXACT JSON format (no markdown, no extra text):
{{
  "hiring_recommendation": "Strong Yes / Yes / Maybe / No",
  "confidence_score": <number 0-100>,
  "seniority_level": "Junior / Mid-level / Senior / Staff",
  "key_observations": [
    "observation 1",
    "observation 2",
    "observation 3"
  ],
  "red_flags": [
    "red flag 1"
  ],
  "green_flags": [
    "green flag 1"
  ],
  "interview_topics": [
    "topic to test in interview"
  ],
  "written_feedback": "2-3 sentence recruiter-style written feedback about this developer"
}}"""


class RecruiterAgent:
    """
    Agent 4 — Recruiter Evaluation Agent
    Acts like a senior technical recruiter evaluating hiring readiness.
    """

    def run(self, repo_data: dict, rag_context: str = "") -> dict:
        logger.info("🧑‍💼 Recruiter Agent running...")

        repo_summary = self._build_summary(repo_data)

        prompt = RECRUITER_PROMPT.format(
            repo_summary=repo_summary,
            code_context=rag_context[:2000] if rag_context else "No code context available",
        )

        try:
            response = ollama.chat(
                model=settings.OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.2, "num_predict": 600},
            )
            content = response["message"]["content"].strip()

            # Clean JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            import json
            result = json.loads(content)
            logger.success("✅ Recruiter Agent complete")
            return result

        except Exception as e:
            logger.error(f"Recruiter Agent error: {e}")
            return self._fallback(repo_data)

    def _build_summary(self, repo_data: dict) -> str:
        return f"""
Repository: {repo_data.get('full_name', '')}
Language: {repo_data.get('language', 'Unknown')}
Stars: {repo_data.get('stars', 0)}
Commits: {repo_data.get('total_commits', 0)}
Files: {repo_data.get('total_files', 0)}
Has README: {'Yes' if repo_data.get('readme') else 'No'}
Has Tests: {'Yes' if any('test' in f['path'].lower() for f in repo_data.get('code_files', [])) else 'No'}
Has CI/CD: {'Yes' if repo_data.get('workflows') else 'No'}
Languages: {', '.join(list(repo_data.get('languages', {}).keys())[:5])}
Contributors: {len(repo_data.get('contributors', []))}
Topics: {', '.join(repo_data.get('topics', []))}
Description: {repo_data.get('description', 'None')}
Folder Structure: {', '.join(repo_data.get('file_tree', {}).get('top_folders', [])[:8])}
"""

    def _fallback(self, repo_data: dict) -> dict:
        commits = repo_data.get('total_commits', 0)
        has_tests = any('test' in f['path'].lower() for f in repo_data.get('code_files', []))
        has_ci = bool(repo_data.get('workflows'))
        score = 40 + (20 if commits > 10 else 0) + (20 if has_tests else 0) + (20 if has_ci else 0)
        return {
            "hiring_recommendation": "Yes" if score >= 60 else "Maybe",
            "confidence_score": score,
            "seniority_level": "Mid-level" if score >= 60 else "Junior",
            "key_observations": ["Repository analyzed with basic scoring"],
            "red_flags": [] if has_tests else ["No tests found"],
            "green_flags": ["Code is present"] if repo_data.get('code_files') else [],
            "interview_topics": ["System design", "Testing practices"],
            "written_feedback": f"This repository shows {'good' if score >= 60 else 'basic'} engineering practices with {commits} commits.",
        }
