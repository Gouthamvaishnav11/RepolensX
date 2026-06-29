from typing import List
from loguru import logger
import chromadb
import ollama
from config import settings

CHUNK_SIZE    = 500
CHUNK_OVERLAP = 50
MAX_FILES     = 35
MAX_FILE_SIZE = 25_000
BATCH_SIZE    = 8


def _split_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Simple fast text splitter — no heavy LangChain import."""
    chunks, start = [], 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return [c.strip() for c in chunks if c.strip()]


class EmbeddingAgent:
    def __init__(self):
        self.chroma = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=int(settings.CHROMA_PORT),
        )

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [
            ollama.embeddings(model=settings.OLLAMA_EMBED_MODEL, prompt=t[:1200])["embedding"]
            for t in texts
        ]

    def _collection(self, repo_id: str):
     name = f"repo_{repo_id.replace('-', '_')}"
     try:
         self.chroma.delete_collection(name)
     except Exception:
        pass
     try:
          return self.chroma.create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"},
        )
     except Exception:
        # Fallback — no metadata (older ChromaDB versions)
        return self.chroma.create_collection(name=name)

    def run(self, repo_data: dict, repo_id: str) -> str:
        logger.info(f"Embedding: {repo_id}")
        col = self._collection(repo_id)
        chunks, ids, metas = [], [], []

        # 1. README
        readme = repo_data.get("readme", "")
        if readme:
            for i, c in enumerate(_split_text(readme[:6000])):
                chunks.append(c)
                ids.append(f"readme_{i}")
                metas.append({"source": "readme", "file_path": "README.md", "chunk_index": i})

        # 2. Code files — priority order, skip duplicates
        seen_paths = set()
        for f in repo_data.get("code_files", [])[:MAX_FILES]:
            path = f.get("path", "")
            if path in seen_paths:
                continue
            seen_paths.add(path)
            content = f.get("content", "")[:MAX_FILE_SIZE]
            if not content.strip():
                continue
            for i, c in enumerate(_split_text(f"# {path}\n{content}", size=450, overlap=40)):
                safe_path = path.replace("/", "_").replace(".", "_")
                chunks.append(c)
                ids.append(f"code_{safe_path}_{i}")
                metas.append({"source": "code", "file_path": path, "chunk_index": i})

        # 3. Project structure (always useful for RAG)
        structure = _build_structure_text(repo_data)
        for i, c in enumerate(_split_text(structure)):
            chunks.append(c)
            ids.append(f"struct_{i}")
            metas.append({"source": "structure", "file_path": "project_structure", "chunk_index": i})

        # 4. Commit history — condensed single chunk
        commits = repo_data.get("commits", [])
        if commits:
            commit_text = "# Commit History\n" + "\n".join(
                f"{c.get('date','')} {c.get('author','')}: {c.get('message','').splitlines()[0][:80]}"
                for c in commits[:40]
            )
            chunks.append(commit_text[:2000])
            ids.append("commits_0")
            metas.append({"source": "commits", "file_path": "git_history", "chunk_index": 0})

        logger.info(f"  Total chunks: {len(chunks)}")

        # Store in batches
        for i in range(0, len(chunks), BATCH_SIZE):
            bt = chunks[i:i+BATCH_SIZE]
            bi = ids[i:i+BATCH_SIZE]
            bm = metas[i:i+BATCH_SIZE]
            embs = self._embed_batch(bt)
            col.add(documents=bt, embeddings=embs, ids=bi, metadatas=bm)
            logger.info(f"  Batch {i//BATCH_SIZE+1}/{(len(chunks)-1)//BATCH_SIZE+1}")

        name = f"repo_{repo_id.replace('-', '_')}"
        logger.success(f"Embedding done: {len(chunks)} chunks → {name}")
        return name


def _build_structure_text(r: dict) -> str:
    tree = r.get("file_tree", {})
    return (
        f"Project: {r.get('full_name','')}\n"
        f"Description: {r.get('description','')[:150]}\n"
        f"Language: {r.get('language','')}\n"
        f"Stars: {r.get('stars',0)} Forks: {r.get('forks',0)}\n"
        f"Files: {r.get('total_files',0)} Commits: {r.get('total_commits',0)}\n"
        f"Topics: {', '.join(r.get('topics',[]))}\n"
        f"Languages: {', '.join(list(r.get('languages',{}).keys())[:6])}\n"
        f"Folders: {', '.join(tree.get('top_folders',[])[:12])}\n"
        f"File types: {', '.join(f'.{k}:{v}' for k,v in list(tree.get('file_types',{}).items())[:8])}\n"
        f"CI/CD: {', '.join(w.get('name','') for w in r.get('workflows',[]))}\n"
    )
