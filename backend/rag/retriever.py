from typing import Tuple, List, Dict
from loguru import logger
import chromadb
import ollama
from config import settings

# Module-level singleton — created once, reused forever
_retriever = None


class RAGRetriever:
    def __init__(self):
        self.chroma = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=int(settings.CHROMA_PORT),
        )
        self._embed_cache: Dict[str, List[float]] = {}

    def _embed(self, text: str) -> List[float]:
        key = text[:80]
        if key not in self._embed_cache:
            self._embed_cache[key] = ollama.embeddings(
                model=settings.OLLAMA_EMBED_MODEL,
                prompt=text[:1000],
            )["embedding"]
            if len(self._embed_cache) > 100:
                # Evict oldest entry
                self._embed_cache.pop(next(iter(self._embed_cache)))
        return self._embed_cache[key]

    def _collection(self, repo_id: str):
        return self.chroma.get_collection(f"repo_{repo_id.replace('-', '_')}")

    def search(self, repo_id: str, query: str, top_k: int = 5) -> List[Dict]:
        try:
            col = self._collection(repo_id)
            count = col.count()
            if count == 0:
                return []
            results = col.query(
                query_embeddings=[self._embed(query)],
                n_results=min(top_k, count),
                include=["documents", "metadatas", "distances"],
            )
            return [
                {
                    "content":   doc,
                    "file_path": meta.get("file_path", ""),
                    "source":    meta.get("source", ""),
                    "score":     round(1 - dist, 3),
                }
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return []


def get_retriever() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever


async def query_repository(
    repo_id: str,
    question: str,
    conversation_history: List[Dict] = None,
) -> Tuple[str, List[Dict]]:
    try:
        chunks = get_retriever().search(repo_id, question, top_k=5)
        if not chunks:
            return "No relevant information found in this repository.", []

        context = "\n\n".join(
            f"[{c['file_path']}]\n{c['content']}" for c in chunks
        )

        history = ""
        if conversation_history:
            for m in conversation_history[-4:]:
                role = "User" if m.get("role") == "user" else "Assistant"
                history += f"{role}: {m.get('content','')}\n"

        prompt = (
            "You are a code reviewer answering questions about a GitHub repository.\n"
            "Use the context below. Be specific and concise (max 200 words).\n\n"
            f"Context:\n{context[:2500]}\n\n"
            f"{f'Chat history:{chr(10)}{history}' if history else ''}"
            f"Question: {question}\n\nAnswer:"
        )

        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.2, "num_predict": 400, "num_ctx": 3000},
        )
        answer = response["message"]["content"].strip()
        sources = [
            {
                "file_path":       c["file_path"],
                "content_preview": c["content"][:100] + "...",
                "relevance_score": c["score"],
            }
            for c in chunks[:3]
        ]
        return answer, sources

    except Exception as e:
        logger.error(f"query_repository error: {e}")
        return f"Error: {str(e)}", []
