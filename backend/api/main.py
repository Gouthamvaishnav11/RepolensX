from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger

from config import settings
from models.database import create_tables
from api.routes import auth, users, repos, chat, reports, compare


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting RepoLens X API...")
    await create_tables()
    logger.success("✅ RepoLens X API is ready!")
    yield
    logger.info("🛑 Shutting down RepoLens X API...")


app = FastAPI(
    title="RepoLens X API",
    description="Multi-Agent RAG-Based AI Developer Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,    prefix="/api")
app.include_router(users.router,   prefix="/api")
app.include_router(repos.router,   prefix="/api")
app.include_router(chat.router,    prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(compare.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.APP_NAME, "version": "1.0.0"}


@app.get("/")
async def root():
    return {"message": "Welcome to RepoLens X API 🔍", "docs": "/docs"}
