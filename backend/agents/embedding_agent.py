from typing import List, Dict
from loguru import logger
from langchain.text_splitter import RecursiveCharacterTextSplitter
import chromadb
from chromadb.config import Settings as ChromaSettings
import ollama
from config import settings


CHUNK_SIZE    = 800
CHUNK_OVERLAP = 100


class EmbeddingAgent:
    """
    Agent 2 — Chunking & Embedding Agent

    Takes raw repository data from Agent 1 and:
    1. Splits everything into semantic chunks
    2. Generates embeddings using Ollama nomic-embed-text (local, free)
    3. Stores all vectors in ChromaDB
    """

    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", " ", ""],
        )
        self.code_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=80,
            separators=["\nclass ", "\ndef ", "\nasync def ", "\n\n", "\n", " "],
        )
        self.chroma = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=int(settings.CHROMA_PORT),
        )

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama nomic-embed-text (runs locally)."""
        embeddings = []
        for text in texts:
            response = ollama.embeddings(
                model=settings.OLLAMA_EMBED_MODEL,
                prompt=text[:2000],
            )
            embeddings.append(response["embedding"])
        return embeddings

    def _get_or_create_collection(self, repo_id: str):
        """Get or create ChromaDB collection for this repo."""
        collection_name = f"repo_{repo_id.replace('-', '_')}"
        try:
            self.chroma.delete_collection(collection_name)
        except Exception:
            pass
        return self.chroma.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def run(self, repo_data: dict, repo_id: str) -> str:
        """
        Main embedding pipeline.
        Returns ChromaDB collection name.
        """
        logger.info(f"🧠 Embedding Agent starting for repo_id={repo_id}")

        collection = self._get_or_create_collection(repo_id)
        all_chunks   = []
        all_ids      = []
        all_metadata = []

        chunk_counter = 0

        # ── 1. README ─────────────────────────────────────
        readme = repo_data.get("readme", "")
        if readme:
            chunks = self.splitter.split_text(readme)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"readme_{i}")
                all_metadata.append({
                    "source": "readme",
                    "file_path": "README.md",
                    "chunk_index": i,
                })
            chunk_counter += len(chunks)
            logger.info(f"  📄 README → {len(chunks)} chunks")

        # ── 2. Code Files ─────────────────────────────────
        for file in repo_data.get("code_files", []):
            path    = file.get("path", "")
            content = file.get("content", "")
            if not content.strip():
                continue

            header = f"# File: {path}\n\n"
            chunks = self.code_splitter.split_text(header + content)

            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"code_{path.replace('/', '_')}_{i}")
                all_metadata.append({
                    "source":      "code",
                    "file_path":   path,
                    "chunk_index": i,
                    "language":    path.rsplit(".", 1)[-1] if "." in path else "unknown",
                })
            chunk_counter += len(chunks)

        logger.info(f"  💻 Code files → {chunk_counter} chunks so far")

        # ── 3. Documentation Files ────────────────────────
        for file in repo_data.get("doc_files", []):
            path    = file.get("path", "")
            content = file.get("content", "")
            if not content.strip():
                continue

            chunks = self.splitter.split_text(content)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"doc_{path.replace('/', '_')}_{i}")
                all_metadata.append({
                    "source":    "documentation",
                    "file_path": path,
                    "chunk_index": i,
                })

        # ── 4. Commit Messages ────────────────────────────
        commits = repo_data.get("commits", [])
        if commits:
            commit_text = "# Commit History\n\n"
            for c in commits[:80]:
                commit_text += f"- [{c.get('date','')[:10]}] {c.get('author','')}: {c.get('message','').splitlines()[0]}\n"

            chunks = self.splitter.split_text(commit_text)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"commits_{i}")
                all_metadata.append({
                    "source":      "commits",
                    "file_path":   "git_history",
                    "chunk_index": i,
                })

        # ── 5. Project Structure Summary ──────────────────
        tree = repo_data.get("file_tree", {})
        structure_text = self._build_structure_text(repo_data, tree)
        chunks = self.splitter.split_text(structure_text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"structure_{i}")
            all_metadata.append({
                "source":      "structure",
                "file_path":   "project_structure",
                "chunk_index": i,
            })

        # ── 6. Issues & PRs ───────────────────────────────
        issues = repo_data.get("issues", [])
        if issues:
            issues_text = "# GitHub Issues\n\n"
            for issue in issues[:30]:
                issues_text += f"- [{issue.get('state','').upper()}] {issue.get('title','')}\n"

            chunks = self.splitter.split_text(issues_text)
            for i, chunk in enumerate(chunks):
                all_chunks.append(chunk)
                all_ids.append(f"issues_{i}")
                all_metadata.append({
                    "source": "issues",
                    "file_path": "github_issues",
                    "chunk_index": i,
                })

        logger.info(f"  📦 Total chunks to embed: {len(all_chunks)}")

        # ── Embed and Store in batches ────────────────────
        batch_size = 20
        for i in range(0, len(all_chunks), batch_size):
            batch_texts    = all_chunks[i:i+batch_size]
            batch_ids      = all_ids[i:i+batch_size]
            batch_metadata = all_metadata[i:i+batch_size]

            embeddings = self._embed(batch_texts)

            collection.add(
                documents=batch_texts,
                embeddings=embeddings,
                ids=batch_ids,
                metadatas=batch_metadata,
            )
            logger.info(f"  ✅ Stored batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}")

        collection_name = f"repo_{repo_id.replace('-', '_')}"
        logger.success(f"✅ Embedding complete: {len(all_chunks)} chunks stored in ChromaDB")
        return collection_name

    def _build_structure_text(self, repo_data: dict, tree: dict) -> str:
        text = f"""# Project: {repo_data.get('full_name', '')}

## Description
{repo_data.get('description', 'No description')}

## Languages
{', '.join(f"{k}: {v} bytes" for k, v in list(repo_data.get('languages', {}).items())[:10])}

## Topics / Tags
{', '.join(repo_data.get('topics', []))}

## Repository Stats
- Stars: {repo_data.get('stars', 0)}
- Forks: {repo_data.get('forks', 0)}
- Total files: {repo_data.get('total_files', 0)}
- Total commits: {repo_data.get('total_commits', 0)}
- Open issues: {repo_data.get('total_issues', 0)}
- License: {repo_data.get('license', 'None')}

## Top Folders (Project Structure)
{chr(10).join(tree.get('top_folders', [])[:20])}

## File Types
{chr(10).join(f"- .{k}: {v} files" for k, v in list(tree.get('file_types', {}).items())[:10])}

## CI/CD Workflows
{chr(10).join(f"- {w.get('name')}: {w.get('path')}" for w in repo_data.get('workflows', []))}

## Contributors
{chr(10).join(f"- {c.get('login')}: {c.get('contributions')} commits" for c in repo_data.get('contributors', []))}
"""
        return text
