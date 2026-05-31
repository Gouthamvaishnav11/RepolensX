import httpx
import base64
from typing import Optional
from loguru import logger
from config import settings


class GitHubClient:
    """
    Wrapper around GitHub REST API.
    Fetches all repository data needed for analysis.
    """

    BASE_URL = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{self.BASE_URL}{endpoint}"
        async with httpx.AsyncClient(timeout=30) as client:
            res = await client.get(url, headers=self.headers, params=params)
            if res.status_code == 404:
                raise ValueError(f"GitHub resource not found: {endpoint}")
            if res.status_code == 403:
                raise ValueError("GitHub API rate limit exceeded or token invalid")
            res.raise_for_status()
            return res.json()

    async def get_paginated(self, endpoint: str, max_pages: int = 5) -> list:
        results = []
        page = 1
        while page <= max_pages:
            data = await self.get(endpoint, params={"per_page": 100, "page": page})
            if not data:
                break
            results.extend(data)
            if len(data) < 100:
                break
            page += 1
        return results

    # ── Repository Info ───────────────────────────────────
    async def get_repo(self, owner: str, name: str) -> dict:
        return await self.get(f"/repos/{owner}/{name}")

    # ── README ────────────────────────────────────────────
    async def get_readme(self, owner: str, name: str) -> str:
        try:
            data = await self.get(f"/repos/{owner}/{name}/readme")
            content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            return content
        except Exception:
            return ""

    # ── File Tree ─────────────────────────────────────────
    async def get_file_tree(self, owner: str, name: str) -> list:
        try:
            data = await self.get(
                f"/repos/{owner}/{name}/git/trees/HEAD",
                params={"recursive": "1"}
            )
            return data.get("tree", [])
        except Exception:
            return []

    # ── File Content ──────────────────────────────────────
    async def get_file_content(self, owner: str, name: str, path: str) -> str:
        try:
            data = await self.get(f"/repos/{owner}/{name}/contents/{path}")
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            return data.get("content", "")
        except Exception:
            return ""

    # ── Commits ───────────────────────────────────────────
    async def get_commits(self, owner: str, name: str, max_pages: int = 3) -> list:
        try:
            return await self.get_paginated(f"/repos/{owner}/{name}/commits", max_pages)
        except Exception:
            return []

    # ── Issues ────────────────────────────────────────────
    async def get_issues(self, owner: str, name: str) -> list:
        try:
            return await self.get_paginated(
                f"/repos/{owner}/{name}/issues",
                max_pages=2
            )
        except Exception:
            return []

    # ── Pull Requests ─────────────────────────────────────
    async def get_pull_requests(self, owner: str, name: str) -> list:
        try:
            return await self.get_paginated(
                f"/repos/{owner}/{name}/pulls",
                max_pages=2
            )
        except Exception:
            return []

    # ── Languages ────────────────────────────────────────
    async def get_languages(self, owner: str, name: str) -> dict:
        try:
            return await self.get(f"/repos/{owner}/{name}/languages")
        except Exception:
            return {}

    # ── Workflows (CI/CD) ─────────────────────────────────
    async def get_workflows(self, owner: str, name: str) -> list:
        try:
            data = await self.get(f"/repos/{owner}/{name}/actions/workflows")
            return data.get("workflows", [])
        except Exception:
            return []

    # ── Contributors ──────────────────────────────────────
    async def get_contributors(self, owner: str, name: str) -> list:
        try:
            return await self.get_paginated(
                f"/repos/{owner}/{name}/contributors",
                max_pages=1
            )
        except Exception:
            return []

    # ── Topics ────────────────────────────────────────────
    async def get_topics(self, owner: str, name: str) -> list:
        try:
            data = await self.get(f"/repos/{owner}/{name}/topics")
            return data.get("names", [])
        except Exception:
            return []
