import ollama
import json
from loguru import logger
from config import settings


CODE_PROMPT = """You are a senior software architect reviewing a GitHub repository's code quality and architecture.

## Repository: {repo_name}
## Language: {language}
## Total Files: {total_files}
## Commits: {total_commits}

## Folder Structure:
{folder_structure}

## Key Code Files Found:
{code_files_list}

## File Types:
{file_types}

## Retrieved Code Context:
{code_context}

Analyze the code quality and architecture. Respond in this EXACT JSON format (no markdown):
{{
  "code_quality_score": <number 0-100>,
  "architecture_score": <number 0-100>,
  "follows_solid_principles": true/false,
  "has_separation_of_concerns": true/false,
  "has_proper_folder_structure": true/false,
  "has_error_handling": true/false,
  "has_type_hints": true/false,
  "has_comments_docstrings": true/false,
  "detected_patterns": ["list of design patterns found"],
  "architecture_style": "monolithic/mvc/layered/microservices/unknown",
  "code_smells": ["list of code issues detected"],
  "positive_practices": ["list of good practices found"],
  "refactoring_suggestions": ["top 3 refactoring suggestions"],
  "complexity_rating": "low/medium/high",
  "summary": "2-3 sentence code quality review"
}}"""


class CodeUnderstandingAgent:
    """
    Agent 3 — Code Understanding RAG Agent
    Retrieves and analyzes code quality, patterns, and architecture.
    """

    def run(self, repo_data: dict, repo_id: str = None) -> dict:
        logger.info("💻 Code Understanding Agent running...")

        file_tree = repo_data.get("file_tree", {})
        code_files = repo_data.get("code_files", [])

        # Get RAG context if repo_id provided
        code_context = ""
        if repo_id:
            try:
                from rag.retriever import RAGRetriever
                retriever = RAGRetriever()
                chunks = retriever.hybrid_search(repo_id, "main application code architecture patterns", top_k=4)
                code_context = "\n".join(c["content"][:500] for c in chunks)
            except Exception as e:
                logger.warning(f"RAG context fetch failed: {e}")

        # Build files list
        files_list = "\n".join(
            f"- {f['path']}" for f in code_files[:20]
        )

        # Folder structure
        folders = "\n".join(file_tree.get("top_folders", [])[:12])

        # File types
        file_types = ", ".join(
            f".{k}({v})" for k, v in list(file_tree.get("file_types", {}).items())[:8]
        )

        prompt = CODE_PROMPT.format(
            repo_name=repo_data.get("full_name", ""),
            language=repo_data.get("language", "Unknown"),
            total_files=repo_data.get("total_files", 0),
            total_commits=repo_data.get("total_commits", 0),
            folder_structure=folders or "Flat structure",
            code_files_list=files_list or "No code files",
            file_types=file_types or "Unknown",
            code_context=code_context[:1500] or "No context available",
        )

        try:
            response = ollama.chat(
                model=settings.OLLAMA_MODEL,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.2, "num_predict": 600},
            )
            content = response["message"]["content"].strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            logger.success("✅ Code Understanding Agent complete")
            return result

        except Exception as e:
            logger.error(f"Code Understanding Agent error: {e}")
            return self._fallback(repo_data)

    def _fallback(self, repo_data: dict) -> dict:
        file_tree = repo_data.get("file_tree", {})
        folders = " ".join(file_tree.get("top_folders", []))
        commits = repo_data.get("total_commits", 0)

        good_patterns = ["src", "lib", "utils", "models", "routes", "services", "controllers", "api", "tests"]
        matched = [p for p in good_patterns if p in folders.lower()]

        arch_score = 30 + min(len(matched) * 8, 50)
        code_score = 40 + (20 if commits > 10 else 0) + (20 if commits > 50 else 0) + min(len(matched) * 5, 20)

        return {
            "code_quality_score": min(code_score, 100),
            "architecture_score": min(arch_score, 100),
            "follows_solid_principles": len(matched) >= 3,
            "has_separation_of_concerns": "routes" in folders or "controllers" in folders,
            "has_proper_folder_structure": len(matched) >= 2,
            "has_error_handling": False,
            "has_type_hints": False,
            "has_comments_docstrings": False,
            "detected_patterns": [],
            "architecture_style": "layered" if len(matched) >= 3 else "monolithic",
            "code_smells": ["Cannot determine without deeper analysis"],
            "positive_practices": [f"Uses {p} folder" for p in matched[:3]],
            "refactoring_suggestions": ["Add type hints", "Add error handling", "Improve folder organization"],
            "complexity_rating": "medium",
            "summary": f"Code scored {min(code_score, 100)}/100. Architecture scored {min(arch_score, 100)}/100 with {len(matched)} good folder patterns detected.",
        }
