import asyncio
from typing import Optional
from loguru import logger
from utils.github_client import GitHubClient


# File extensions worth reading
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go",
    ".rs", ".cpp", ".c", ".cs", ".rb", ".php", ".swift",
    ".kt", ".scala", ".r", ".sql", ".sh", ".yaml", ".yml",
    ".json", ".toml", ".env.example", ".dockerfile",
}

DOC_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "coverage", ".pytest_cache",
    "vendor", "target", "bin", "obj",
}

MAX_FILE_SIZE = 50_000   # 50KB per file max
MAX_FILES     = 80       # max code files to read


class IngestionAgent:
    """
    Agent 1 — Repository Ingestion Agent

    Fetches everything from a GitHub repository:
    - Repository metadata
    - Source code files (up to MAX_FILES)
    - README and documentation
    - Commit history
    - Issues and PRs
    - CI/CD workflows
    - Languages breakdown
    """

    def __init__(self, github_token: Optional[str] = None):
        self.github = GitHubClient(token=github_token)

    async def run(self, owner: str, name: str) -> dict:
        """
        Main ingestion pipeline.
        Returns a structured dict of all repository knowledge.
        """
        logger.info(f"🔍 Ingestion Agent starting for {owner}/{name}")

        # Run all fetches concurrently for speed
        (
            repo_info,
            readme,
            file_tree,
            commits,
            issues,
            pull_requests,
            languages,
            workflows,
            contributors,
            topics,
        ) = await asyncio.gather(
            self.github.get_repo(owner, name),
            self.github.get_readme(owner, name),
            self.github.get_file_tree(owner, name),
            self.github.get_commits(owner, name),
            self.github.get_issues(owner, name),
            self.github.get_pull_requests(owner, name),
            self.github.get_languages(owner, name),
            self.github.get_workflows(owner, name),
            self.github.get_contributors(owner, name),
            self.github.get_topics(owner, name),
        )

        logger.info(f"  📁 File tree: {len(file_tree)} entries")
        logger.info(f"  📝 Commits: {len(commits)}")
        logger.info(f"  🐛 Issues: {len(issues)}")

        # Filter and fetch code files
        code_files = await self._fetch_code_files(owner, name, file_tree)
        doc_files  = await self._fetch_doc_files(owner, name, file_tree)

        # Build structured output
        repo_data = {
            # Metadata
            "owner":          owner,
            "name":           name,
            "full_name":      f"{owner}/{name}",
            "description":    repo_info.get("description", ""),
            "language":       repo_info.get("language", ""),
            "stars":          repo_info.get("stargazers_count", 0),
            "forks":          repo_info.get("forks_count", 0),
            "open_issues":    repo_info.get("open_issues_count", 0),
            "default_branch": repo_info.get("default_branch", "main"),
            "created_at":     repo_info.get("created_at", ""),
            "updated_at":     repo_info.get("updated_at", ""),
            "license":        repo_info.get("license", {}).get("name", "") if repo_info.get("license") else "",
            "topics":         topics,
            "has_wiki":       repo_info.get("has_wiki", False),
            "has_pages":      repo_info.get("has_pages", False),

            # Content
            "readme":         readme,
            "code_files":     code_files,
            "doc_files":      doc_files,
            "file_tree":      self._summarize_tree(file_tree),

            # Activity
            "commits":        self._summarize_commits(commits),
            "issues":         self._summarize_issues(issues),
            "pull_requests":  self._summarize_prs(pull_requests),
            "contributors":   self._summarize_contributors(contributors),

            # Tech stack
            "languages":      languages,
            "workflows":      self._summarize_workflows(workflows),

            # Stats
            "total_files":    len([f for f in file_tree if f.get("type") == "blob"]),
            "total_commits":  len(commits),
            "total_issues":   len(issues),
            "total_prs":      len(pull_requests),
        }

        logger.success(f"✅ Ingestion complete: {len(code_files)} code files, {len(commits)} commits")
        return repo_data

    # ── Private Helpers ───────────────────────────────────

    async def _fetch_code_files(self, owner: str, name: str, tree: list) -> list:
        """Fetch content of important code files."""
        candidates = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            if any(skip in path for skip in SKIP_DIRS):
                continue
            ext = "." + path.rsplit(".", 1)[-1] if "." in path else ""
            if ext.lower() in CODE_EXTENSIONS:
                size = item.get("size", 0)
                if size <= MAX_FILE_SIZE:
                    candidates.append(path)

        # Prioritize important files
        candidates = self._prioritize_files(candidates)[:MAX_FILES]

        logger.info(f"  📄 Fetching {len(candidates)} code files...")

        # Fetch concurrently in batches of 10
        files = []
        for i in range(0, len(candidates), 10):
            batch = candidates[i:i+10]
            contents = await asyncio.gather(*[
                self.github.get_file_content(owner, name, path)
                for path in batch
            ])
            for path, content in zip(batch, contents):
                if content.strip():
                    files.append({"path": path, "content": content})

        return files

    async def _fetch_doc_files(self, owner: str, name: str, tree: list) -> list:
        """Fetch documentation files."""
        doc_paths = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
            if ext in DOC_EXTENSIONS and len(doc_paths) < 20:
                doc_paths.append(path)

        files = []
        for path in doc_paths:
            content = await self.github.get_file_content(owner, name, path)
            if content.strip():
                files.append({"path": path, "content": content})
        return files

    def _prioritize_files(self, paths: list) -> list:
        """Sort files by importance."""
        priority = []
        secondary = []
        low = []

        important_names = {
            "main", "app", "index", "server", "api",
            "config", "settings", "models", "routes",
            "database", "auth", "utils", "helpers",
            "dockerfile", "docker-compose",
        }

        for path in paths:
            filename = path.rsplit("/", 1)[-1].lower().replace(".", "")
            if any(imp in filename for imp in important_names):
                priority.append(path)
            elif path.count("/") <= 2:
                secondary.append(path)
            else:
                low.append(path)

        return priority + secondary + low

    def _summarize_tree(self, tree: list) -> dict:
        """Build folder structure summary."""
        folders = set()
        extensions = {}
        for item in tree:
            path = item.get("path", "")
            if "/" in path:
                folders.add(path.rsplit("/", 1)[0])
            if "." in path:
                ext = path.rsplit(".", 1)[-1].lower()
                extensions[ext] = extensions.get(ext, 0) + 1

        return {
            "top_folders": sorted(list(folders))[:30],
            "file_types":  dict(sorted(extensions.items(), key=lambda x: -x[1])[:15]),
            "total_items": len(tree),
        }

    def _summarize_commits(self, commits: list) -> list:
        """Extract commit messages and metadata."""
        result = []
        for c in commits[:100]:
            commit = c.get("commit", {})
            result.append({
                "message":    commit.get("message", "")[:200],
                "author":     commit.get("author", {}).get("name", ""),
                "date":       commit.get("author", {}).get("date", ""),
            })
        return result

    def _summarize_issues(self, issues: list) -> list:
        return [
            {
                "title": i.get("title", "")[:150],
                "state": i.get("state", ""),
                "labels": [l.get("name") for l in i.get("labels", [])],
            }
            for i in issues[:50]
        ]

    def _summarize_prs(self, prs: list) -> list:
        return [
            {
                "title":  pr.get("title", "")[:150],
                "state":  pr.get("state", ""),
                "merged": pr.get("merged_at") is not None,
            }
            for pr in prs[:30]
        ]

    def _summarize_contributors(self, contributors: list) -> list:
        return [
            {
                "login":         c.get("login", ""),
                "contributions": c.get("contributions", 0),
            }
            for c in contributors[:10]
        ]

    def _summarize_workflows(self, workflows: list) -> list:
        return [
            {
                "name":  w.get("name", ""),
                "state": w.get("state", ""),
                "path":  w.get("path", ""),
            }
            for w in workflows
        ]
