from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from models.database import get_db
from models.db_models import User, Repository, ChatMessage, AnalysisStatusEnum
from models.schemas import ChatRequest, ChatResponse
from api.middleware.auth import get_current_user

router = APIRouter(prefix="/chat", tags=["AI Chat"])


@router.post("/{repo_id}", response_model=ChatResponse)
async def chat_with_repo(
    repo_id: UUID,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Ask AI questions about a repository using RAG."""

    # Verify repo belongs to user and is analyzed
    result = await db.execute(
        select(Repository).where(
            Repository.id == repo_id,
            Repository.user_id == current_user.id,
        )
    )
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    if repo.status != AnalysisStatusEnum.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Repository analysis not complete. Please wait."
        )

    # Save user message
    user_msg = ChatMessage(
        repository_id=repo_id,
        user_id=current_user.id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)
    await db.flush()

    # Run RAG query (will be fully implemented Day 4)
    try:
        from rag.retriever import query_repository
        response_text, sources = await query_repository(
            repo_id=str(repo_id),
            question=request.message,
            conversation_history=request.conversation_history,
        )
    except Exception as e:
        response_text = f"RAG pipeline not yet initialized. Error: {str(e)}"
        sources = []

    # Save assistant message
    assistant_msg = ChatMessage(
        repository_id=repo_id,
        user_id=current_user.id,
        role="assistant",
        content=response_text,
        sources=[s.__dict__ if hasattr(s, '__dict__') else s for s in sources],
    )
    db.add(assistant_msg)
    await db.commit()

    return ChatResponse(
        message=response_text,
        sources=sources,
        repo_id=repo_id,
    )


@router.get("/{repo_id}/history")
async def get_chat_history(
    repo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    """Get chat history for a repository."""
    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.repository_id == repo_id,
            ChatMessage.user_id == current_user.id,
        )
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return [
        {
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in messages
    ]
