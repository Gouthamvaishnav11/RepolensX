from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import hmac
import hashlib
import httpx
import base64
from uuid import UUID

from models.database import get_db
from models.db_models import User, PlanEnum
from api.middleware.auth import get_current_user
from config import settings

router = APIRouter(prefix="/payments", tags=["Payments"])


PLANS = {
    "pro": {
        "name": "PRO Plan",
        "price_inr": 49900,   # paise (₹499)
        "price_usd": 600,     # cents ($6)
        "features": ["20 repos/month", "100 AI chat questions", "PDF reports", "Mentor roadmap"],
    },
    "team": {
        "name": "TEAM Plan",
        "price_inr": 299900,  # ₹2999
        "price_usd": 3500,    # $35
        "features": ["Unlimited repos", "Unlimited chat", "Bulk evaluation", "API access"],
    },
}


class CreateOrderRequest(BaseModel):
    plan: str  # "pro" or "team"


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    plan: str


@router.get("/plans")
async def get_plans():
    """Get all available plans and pricing."""
    return {
        "free": {
            "name": "FREE",
            "price_inr": 0,
            "price_usd": 0,
            "features": [
                "3 repos/month",
                "10 AI chat questions",
                "Basic report",
                "Public score link",
            ],
        },
        **PLANS
    }


@router.post("/create-order")
async def create_order(
    request: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
):
    """Create a Razorpay order for plan upgrade."""
    if request.plan not in PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=400,
            detail="Payment gateway not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to .env"
        )

    plan_data = PLANS[request.plan]

    # Create Razorpay order
    auth = base64.b64encode(
        f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()
    ).decode()

    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.razorpay.com/v1/orders",
            headers={"Authorization": f"Basic {auth}", "Content-Type": "application/json"},
            json={
                "amount": plan_data["price_inr"],
                "currency": "INR",
                "receipt": f"repolens_{current_user.id}_{request.plan}",
                "notes": {
                    "user_id": str(current_user.id),
                    "plan": request.plan,
                },
            },
        )

    if res.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to create payment order")

    order = res.json()
    return {
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "key_id": settings.RAZORPAY_KEY_ID,
        "plan": request.plan,
        "plan_name": plan_data["name"],
        "user_name": current_user.name or current_user.username,
        "user_email": current_user.email or "",
    }


@router.post("/verify")
async def verify_payment(
    request: VerifyPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify Razorpay payment signature and upgrade user plan."""

    if not settings.RAZORPAY_KEY_SECRET:
        # Demo mode - just upgrade the plan
        result = await db.execute(select(User).where(User.id == current_user.id))
        user = result.scalar_one_or_none()
        if user:
            user.plan = PlanEnum(request.plan)
            user.repos_analyzed_this_month = 0
            await db.commit()
        return {"success": True, "plan": request.plan, "message": "Plan upgraded successfully!"}

    # Verify Razorpay signature
    body = f"{request.razorpay_order_id}|{request.razorpay_payment_id}"
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256,
    ).hexdigest()

    if expected_signature != request.razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Upgrade user plan
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if user:
        user.plan = PlanEnum(request.plan)
        user.repos_analyzed_this_month = 0
        await db.commit()

    return {"success": True, "plan": request.plan, "message": f"Successfully upgraded to {request.plan.upper()}!"}


@router.post("/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Downgrade user back to free plan."""
    result = await db.execute(select(User).where(User.id == current_user.id))
    user = result.scalar_one_or_none()
    if user:
        user.plan = PlanEnum.FREE
        await db.commit()
    return {"success": True, "message": "Downgraded to FREE plan"}
