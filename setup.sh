#!/bin/bash
# ============================================================
# RepoLens X — Day 1 Setup Script
# Run: chmod +x setup.sh && ./setup.sh
# ============================================================

set -e

echo "🔍 RepoLens X — Day 1 Setup"
echo "================================"

# Check prerequisites
echo ""
echo "📋 Checking prerequisites..."

check_cmd() {
    if command -v $1 &> /dev/null; then
        echo "  ✅ $1 found: $(command -v $1)"
    else
        echo "  ❌ $1 NOT found. Please install: $2"
        exit 1
    fi
}

check_cmd python3 "https://python.org"
check_cmd node "https://nodejs.org"
check_cmd docker "https://docker.com"
check_cmd git "https://git-scm.com"

echo ""
echo "📦 Setting up .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  ✅ Created .env from .env.example"
    echo "  ⚠️  Please edit .env with your GitHub OAuth credentials"
else
    echo "  ✅ .env already exists"
fi

echo ""
echo "🐳 Starting Docker services (PostgreSQL + Redis + ChromaDB + MinIO)..."
docker compose up -d postgres redis chromadb minio
echo "  ✅ Services starting..."

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 10

echo ""
echo "🐍 Installing Python dependencies..."
cd backend
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate 2>/dev/null || . venv/bin/activate
pip install -r requirements.txt --quiet
echo "  ✅ Python dependencies installed"
cd ..

echo ""
echo "🌐 Installing Node dependencies..."
cd frontend
npm install --silent
echo "  ✅ Node dependencies installed"
cd ..

echo ""
echo "🦙 Checking Ollama..."
if command -v ollama &> /dev/null; then
    echo "  ✅ Ollama found"
    echo "  📥 Pulling mistral model (this may take a few minutes)..."
    ollama pull mistral
    echo "  📥 Pulling nomic-embed-text embedding model..."
    ollama pull nomic-embed-text
else
    echo "  ⚠️  Ollama not found. Install from: https://ollama.com"
    echo "  After installing, run:"
    echo "    ollama pull mistral"
    echo "    ollama pull nomic-embed-text"
fi

echo ""
echo "✅ Day 1 Setup Complete!"
echo "================================"
echo ""
echo "🚀 To start the app:"
echo ""
echo "  Terminal 1 (Backend):"
echo "    cd backend && source venv/bin/activate && uvicorn api.main:app --reload"
echo ""
echo "  Terminal 2 (Celery Worker):"
echo "    cd backend && source venv/bin/activate && celery -A tasks.celery_app worker --loglevel=info"
echo ""
echo "  Terminal 3 (Frontend):"
echo "    cd frontend && npm run dev"
echo ""
echo "  OR run everything with Docker:"
echo "    docker compose up --build"
echo ""
echo "📖 Access:"
echo "  Frontend:  http://localhost:5173"
echo "  API:       http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "  MinIO:     http://localhost:9001"
echo ""
echo "⚠️  IMPORTANT: Edit .env with your GitHub OAuth App credentials!"
echo "  Create at: https://github.com/settings/developers -> OAuth Apps"
echo "  Homepage URL: http://localhost:5173"
echo "  Callback URL: http://localhost:8000/api/auth/github/callback"
