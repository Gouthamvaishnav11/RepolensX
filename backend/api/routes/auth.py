from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx
import secrets

from models.database import get_db
from models.db_models import User, UserPreferences
from models.schemas import TokenResponse, GitHubCallbackRequest
from utils.auth_utils import create_access_token, create_refresh_token, decode_token
from config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/github/login")
async def github_login():
    """Redirect user to GitHub OAuth login page."""
    state = secrets.token_urlsafe(32)
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=read:user,user:email,repo"
        f"&state={state}"
    )
    return {"auth_url": github_auth_url, "state": state}


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str = None,
    db: AsyncSession = Depends(get_db)
):
    """Handle GitHub OAuth callback and return JWT tokens."""

    # Step 1: Exchange code for GitHub access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )

    token_data = token_response.json()
    github_access_token = token_data.get("access_token")

    if not github_access_token:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed. Invalid code.")

    # Step 2: Fetch GitHub user profile
    async with httpx.AsyncClient() as client:
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"token {github_access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        github_user = user_response.json()

        # Also fetch user emails if email not public
        email_response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"token {github_access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
        )
        emails = email_response.json()

    # Get primary email
    primary_email = github_user.get("email")
    if not primary_email and isinstance(emails, list):
        for email_obj in emails:
            if email_obj.get("primary"):
                primary_email = email_obj.get("email")
                break

    # Step 3: Upsert user in DB
    github_id = str(github_user["id"])
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if not user:
        # New user — create
        user = User(
            github_id=github_id,
            username=github_user.get("login"),
            email=primary_email,
            name=github_user.get("name"),
            avatar_url=github_user.get("avatar_url"),
        )
        db.add(user)
        await db.flush()

        # Create default preferences
        prefs = UserPreferences(user_id=user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(user)
    else:
        # Existing user — update profile
        user.username = github_user.get("login", user.username)
        user.email = primary_email or user.email
        user.name = github_user.get("name", user.name)
        user.avatar_url = github_user.get("avatar_url", user.avatar_url)
        await db.commit()
        await db.refresh(user)

    # Step 4: Create JWT tokens
    token_payload = {"sub": str(user.id), "github_id": user.github_id}
    access_token = create_access_token(token_payload)
    refresh_token = create_refresh_token(token_payload)

    # Step 5: Redirect to frontend with tokens
    frontend_url = f"http://localhost:5173/auth/callback"
    return RedirectResponse(
        url=f"{frontend_url}?access_token={access_token}&refresh_token={refresh_token}"
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """Get new access token using refresh token."""
    payload = decode_token(refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    token_payload = {"sub": str(user.id), "github_id": user.github_id}
    new_access_token = create_access_token(token_payload)
    new_refresh_token = create_refresh_token(token_payload)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
