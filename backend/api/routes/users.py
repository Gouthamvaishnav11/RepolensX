from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.database import get_db
from models.db_models import User, UserPreferences
from models.schemas import UserResponse, UserPreferencesUpdate
from api.middleware.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return current_user


@router.put("/me/preferences")
async def update_preferences(
    updates: UserPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user preferences."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)

    if updates.email_notifications is not None:
        prefs.email_notifications = updates.email_notifications
    if updates.public_profile is not None:
        prefs.public_profile = updates.public_profile
    if updates.preferred_language is not None:
        prefs.preferred_language = updates.preferred_language

    await db.commit()
    return {"message": "Preferences updated successfully"}


@router.get("/me/stats")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user statistics."""
    from models.db_models import Repository
    result = await db.execute(
        select(Repository).where(Repository.user_id == current_user.id)
    )
    repos = result.scalars().all()

    return {
        "total_repos_analyzed": len(repos),
        "repos_this_month": current_user.repos_analyzed_this_month,
        "plan": current_user.plan,
        "plan_limits": {
            "free": {"repos_per_month": 3, "chat_questions": 10},
            "pro": {"repos_per_month": 20, "chat_questions": 100},
            "team": {"repos_per_month": -1, "chat_questions": -1},
        }.get(current_user.plan, {}),
    }
