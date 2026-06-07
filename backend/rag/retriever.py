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
            logger.info(f"Collection document count: {count}")
            logger.info(f"Search query: {query}")

            if count == 0:
                logger.warning(f"No documents found for repository {repo_id}")
                return []
            
            results = col.query(
                query_embeddings=[self._embed(query)],
                n_results=min(top_k, count),
                include=["documents", "metadatas", "distances"],
            )

            retrieved_chunks = [
                {
                    "content": doc,
                    "file_path": meta.get("file_path", ""),
                    "source": meta.get("source", ""),
                    "score": round(1 - dist, 3),
                }
                for doc, meta, dist in zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0],
                )
            ]

            for chunk in retrieved_chunks[:3]:
                logger.info(
                    f"Retrieved: {chunk['file_path']} "
                    f"(score={chunk['score']})"
                )

            return retrieved_chunks
        
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
        # Retrieve relevant chunks
        chunks = get_retriever().search(
            repo_id=repo_id,
            query=question,
            top_k=10,
        )

        logger.info(f"Question: {question}")
        logger.info(f"Retrieved chunks: {len(chunks)}")

        if not chunks:
            return (
                "No relevant information found in this repository.",
                [],
            )

        # Build repository context
        context = "\n\n".join(
            f"File: {chunk['file_path']}\n"
            f"{chunk['content']}"
            for chunk in chunks
        )

        # Build conversation history
        history = ""

        if conversation_history:
            for message in conversation_history[-5:]:
                role = (
                    "User"
                    if message.get("role") == "user"
                    else "Assistant"
                )

                history += (
                    f"{role}: "
                    f"{message.get('content', '')}\n"
                )

       
        prompt = f"""
You are an expert software engineer analyzing a GitHub repository.

Rules:
- Answer ONLY using the repository context.
- Mention file names whenever relevant.
- Explain code flow clearly.
- If the answer is not present in the repository context, respond with:
  "This information is not present in the indexed repository."
- Do not make assumptions.
- Be detailed and technical.

Repository Context:
{context[:12000]}

Conversation History:
{history}

User Question:
{question}

Answer:
"""

        # Call Ollama
        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a repository analysis assistant. "
                        "Answer questions only from the provided repository context."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            options={
                "temperature": 0.1,
                "num_predict": 600,
                "num_ctx": 8192,
            },
        )

        answer = (
            response.get("message", {})
            .get("content", "")
            .strip()
        )

        # Build sources list
        sources = [
            {
                "file_path": chunk["file_path"],
                "content_preview": (
                    chunk["content"][:150] + "..."
                    if len(chunk["content"]) > 150
                    else chunk["content"]
                ),
                "relevance_score": chunk["score"],
            }
            for chunk in chunks[:5]
        ]

        return answer, sources

    except Exception as e:
        logger.exception("query_repository failed")
        return (
            f"Error while querying repository: {str(e)}",
            [],
        )