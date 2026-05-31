from typing import Tuple, List, Dict, Any
from loguru import logger
import chromadb
from chromadb.config import Settings as ChromaSettings
import ollama
from rank_bm25 import BM25Okapi
from config import settings


class RAGRetriever:
    def __init__(self):
        self.chroma = chromadb.HttpClient(
          host=settings.CHROMA_HOST,
          port=int(settings.CHROMA_PORT),
        )
       

    def _embed_query(self, query: str) -> List[float]:
        response = ollama.embeddings(model=settings.OLLAMA_EMBED_MODEL, prompt=query[:1000])
        return response["embedding"]

    def _get_collection(self, repo_id: str):
        collection_name = f"repo_{repo_id.replace('-', '_')}"
        return self.chroma.get_collection(collection_name)

    def semantic_search(self, repo_id: str, query: str, top_k: int = 8) -> List[Dict]:
        try:
            collection = self._get_collection(repo_id)
            query_embedding = self._embed_query(query)
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection.count()),
                include=["documents", "metadatas", "distances"],
            )
            chunks = []
            for doc, meta, dist in zip(results["documents"][0], results["metadatas"][0], results["distances"][0]):
                chunks.append({
                    "content": doc,
                    "file_path": meta.get("file_path", ""),
                    "source": meta.get("source", ""),
                    "relevance_score": round(1 - dist, 3),
                })
            return chunks
        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return []

    def bm25_search(self, repo_id: str, query: str, top_k: int = 5) -> List[Dict]:
        try:
            collection = self._get_collection(repo_id)
            all_docs = collection.get(include=["documents", "metadatas"])
            documents = all_docs["documents"]
            metadatas = all_docs["metadatas"]
            if not documents:
                return []
            tokenized_corpus = [doc.lower().split() for doc in documents]
            bm25 = BM25Okapi(tokenized_corpus)
            scores = bm25.get_scores(query.lower().split())
            top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
            results = []
            for idx in top_indices:
                if scores[idx] > 0:
                    results.append({
                        "content": documents[idx],
                        "file_path": metadatas[idx].get("file_path", ""),
                        "source": metadatas[idx].get("source", ""),
                        "relevance_score": round(float(scores[idx]) / 10, 3),
                    })
            return results
        except Exception as e:
            logger.error(f"BM25 search error: {e}")
            return []

    def hybrid_search(self, repo_id: str, query: str, top_k: int = 6) -> List[Dict]:
        semantic = self.semantic_search(repo_id, query, top_k=top_k)
        bm25 = self.bm25_search(repo_id, query, top_k=top_k // 2)
        seen = set()
        merged = []
        for chunk in semantic + bm25:
            key = chunk["content"][:100]
            if key not in seen:
                seen.add(key)
                merged.append(chunk)
        merged.sort(key=lambda x: x["relevance_score"], reverse=True)
        return merged[:top_k]


_retriever = None

def get_retriever() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever


async def query_repository(repo_id: str, question: str, conversation_history: List[Dict] = None) -> Tuple[str, List[Dict]]:
    try:
        retriever = get_retriever()
        chunks = retriever.hybrid_search(repo_id, question, top_k=6)
        if not chunks:
            return "I couldn't find relevant information in this repository.", []

        context = ""
        for i, chunk in enumerate(chunks):
            context += f"\n--- Source {i+1}: {chunk['file_path']} ---\n"
            context += chunk["content"] + "\n"

        history_text = ""
        if conversation_history:
            for msg in conversation_history[-4:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                history_text += f"{role}: {msg.get('content', '')}\n"

        prompt = f"""You are an expert software engineer analyzing a GitHub repository.
Use ONLY the retrieved context below to answer the question. Be specific and actionable.

## Retrieved Repository Context:
{context}

## Previous Conversation:
{history_text}

## Question:
{question}

## Answer:"""

        response = ollama.chat(
            model=settings.OLLAMA_MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.3, "num_predict": 800},
        )

        answer = response["message"]["content"].strip()
        sources = [
            {"file_path": c["file_path"], "content_preview": c["content"][:150] + "...", "relevance_score": c["relevance_score"]}
            for c in chunks[:4]
        ]
        return answer, sources

    except Exception as e:
        logger.error(f"RAG query error: {e}")
        return f"Error: {str(e)}", []
