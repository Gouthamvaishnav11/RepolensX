import asyncio
from typing import Optional
import base64
import httpx
from loguru import logger
from config import settings

CODE_EXT = {
    ".py",".js",".ts",".jsx",".tsx",".java",".go",".rs",
    ".cpp",".c",".cs",".rb",".php",".swift",".kt",".sql",
    ".sh",".yaml",".yml",".toml",
}
DOC_EXT  = {".md",".txt",".rst"}
SKIP_DIRS = {
    "node_modules",".git","__pycache__",".venv","venv",
    "dist","build",".next","coverage","vendor","target",
}
MAX_FILES     = 40
MAX_FILE_SIZE = 30_000


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str = ""):
        self.headers = {
            "Authorization": f"token {token}" if token else "",
            "Accept": "application/vnd.github.v3+json",
        }

    async def get(self, path: str, params: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{self.BASE}{path}", headers=self.headers, params=params)
            if r.status_code in (404, 403, 401):
                return {}
            r.raise_for_status()
            return r.json()

    async def get_list(self, path: str, max_pages: int = 2) -> list:
        results = []
        for page in range(1, max_pages + 1):
            data = await self.get(path, params={"per_page": 100, "page": page})
            if not data or not isinstance(data, list):
                break
            results.extend(data)
            if len(data) < 100:
                break
        return results

    async def file_content(self, owner: str, name: str, path: str) -> str:
        try:
            data = await self.get(f"/repos/{owner}/{name}/contents/{path}")
            if data and data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
        except Exception:
            pass
        return ""


class IngestionAgent:
    def __init__(self, github_token: Optional[str] = None):
        self.gh = GitHubClient(token=github_token or settings.GITHUB_TOKEN)

    async def run(self, owner: str, name: str) -> dict:
        logger.info(f"Ingestion: {owner}/{name}")

        # All GitHub API calls in parallel
        (repo_info, readme_data, tree_data, commits,
         languages, workflows, contributors, topics) = await asyncio.gather(
            self.gh.get(f"/repos/{owner}/{name}"),
            self.gh.get(f"/repos/{owner}/{name}/readme"),
            self.gh.get(f"/repos/{owner}/{name}/git/trees/HEAD", {"recursive": "1"}),
            self.gh.get_list(f"/repos/{owner}/{name}/commits", max_pages=2),
            self.gh.get(f"/repos/{owner}/{name}/languages"),
            self.gh.get(f"/repos/{owner}/{name}/actions/workflows"),
            self.gh.get_list(f"/repos/{owner}/{name}/contributors", max_pages=1),
            self.gh.get(f"/repos/{owner}/{name}/topics"),
        )

        # Decode README
        readme = ""
        if readme_data and readme_data.get("encoding") == "base64":
            readme = base64.b64decode(readme_data["content"]).decode("utf-8", errors="ignore")

        tree = tree_data.get("tree", []) if isinstance(tree_data, dict) else []
        wf_list = workflows.get("workflows", []) if isinstance(workflows, dict) else []
        topic_list = topics.get("names", []) if isinstance(topics, dict) else []

        # Fetch code files in parallel batches
        code_files = await self._fetch_code_files(owner, name, tree)

        logger.info(f"  files={len(tree)} commits={len(commits)} code_fetched={len(code_files)}")

        return {
            "owner":        owner,
            "name":         name,
            "full_name":    f"{owner}/{name}",
            "description":  (repo_info.get("description") or "")[:300],
            "language":     repo_info.get("language", ""),
            "stars":        repo_info.get("stargazers_count", 0),
            "forks":        repo_info.get("forks_count", 0),
            "license":      (repo_info.get("license") or {}).get("name", ""),
            "topics":       topic_list,
            "readme":       readme,
            "code_files":   code_files,
            "doc_files":    [],
            "file_tree":    self._tree_summary(tree),
            "commits":      self._fmt_commits(commits),
            "workflows":    [{"name": w.get("name",""), "path": w.get("path","")} for w in wf_list],
            "contributors": [{"login": c.get("login",""), "contributions": c.get("contributions",0)} for c in contributors[:8]],
            "languages":    languages if isinstance(languages, dict) else {},
            "total_files":  len([f for f in tree if f.get("type") == "blob"]),
            "total_commits": len(commits),
            "total_issues": repo_info.get("open_issues_count", 0),
        }

    async def _fetch_code_files(self, owner: str, name: str, tree: list) -> list:
        candidates = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            if any(s in path for s in SKIP_DIRS):
                continue
            ext = "." + path.rsplit(".", 1)[-1].lower() if "." in path else ""
            size = item.get("size", 0)
            if ext in CODE_EXT and size <= MAX_FILE_SIZE:
                candidates.append(path)

        candidates = self._prioritize(candidates)[:MAX_FILES]

        # Fetch in parallel batches of 8
        files = []
        for i in range(0, len(candidates), 8):
            batch = candidates[i:i+8]
            contents = await asyncio.gather(*[
                self.gh.file_content(owner, name, p) for p in batch
            ])
            for path, content in zip(batch, contents):
                if content.strip():
                    files.append({"path": path, "content": content})
        return files

    def _prioritize(self, paths: list) -> list:
        important = {"main","app","index","server","api","config","models","routes","database","auth","utils"}
        hi, lo = [], []
        for p in paths:
            fname = p.rsplit("/", 1)[-1].lower().split(".")[0]
            (hi if fname in important or p.count("/") <= 1 else lo).append(p)
        return hi + lo

    def _tree_summary(self, tree: list) -> dict:
        folders, exts = set(), {}
        for item in tree:
            path = item.get("path", "")
            if "/" in path:
                folders.add(path.rsplit("/", 1)[0])
            if "." in path:
                ext = path.rsplit(".", 1)[-1].lower()
                exts[ext] = exts.get(ext, 0) + 1
        return {
            "top_folders": sorted(folders)[:20],
            "file_types":  dict(sorted(exts.items(), key=lambda x: -x[1])[:12]),
            "total_items": len(tree),
        }

    def _fmt_commits(self, commits: list) -> list:
        out = []
        for c in commits[:60]:
            cm = c.get("commit", {})
            out.append({
                "message": cm.get("message", "")[:120],
                "author":  cm.get("author", {}).get("name", ""),
                "date":    cm.get("author", {}).get("date", "")[:10],
            })
        return out
