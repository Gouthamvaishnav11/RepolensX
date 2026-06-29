# 🔍 RepoLens X

### Multi-Agent RAG-Based AI Developer Intelligence & Repository Evaluation Platform

> **"Turn any GitHub repository into a recruiter-ready, AI-analyzed, deeply understood engineering profile."**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-cyan.svg)](https://reactjs.org/)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![Ollama](https://img.shields.io/badge/LLM-Ollama%20(Local)-purple.svg)](https://ollama.com/)

---

## 📌 Table of Contents

- [Problem Statement](#-problem-statement)
- [What is RepoLens X](#-what-is-repolens-x)
- [Live Demo Architecture](#-system-architecture)
- [Multi-Agent System](#-multi-agent-system)
- [RAG Pipeline](#-rag-pipeline)
- [Features](#-features)
- [Free Tech Stack (100% Open Source)](#-free-tech-stack--100-open-source-forever)
- [Project Structure](#-project-structure)
- [Installation & Setup](#-installation--setup)
- [Environment Variables](#-environment-variables)
- [API Endpoints](#-api-endpoints)
- [Use Cases](#-use-cases)
- [Roadmap](#-roadmap)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧠 Problem Statement

In modern software hiring, recruiters increasingly rely on GitHub repositories to evaluate technical skills, coding practices, and project experience. However:

- ❌ Evaluation is **manual, inconsistent, and time-consuming**
- ❌ Students lack **personalized mentorship** on why their projects appear weak
- ❌ No tool explains **how recruiters actually evaluate** a GitHub profile
- ❌ Static code analyzers provide **no contextual or architectural reasoning**
- ❌ LLM-only systems **hallucinate** without repository-specific memory

**RepoLens X solves all of this** using a Multi-Agent RAG architecture.

---

## 🚀 What is RepoLens X

RepoLens X is an **AI-powered GitHub Repository Intelligence Platform** that:

- Ingests and understands any GitHub repository deeply
- Stores all repository knowledge in a **Vector Database** (RAG)
- Uses **7 specialized AI agents** that collaborate through an orchestrator
- Simulates how a **senior recruiter** would evaluate your project
- Generates a **personalized developer growth roadmap**
- Answers natural language questions about any repository
- Tracks your progress over time across multiple repositories

> Not just a code checker — a full **AI Engineering Mentor + Recruiter Simulator**.

---

## 🏗️ System Architecture

```
                        ┌─────────────────────────────┐
                        │         User Query           │
                        └────────────┬────────────────┘
                                     │
                        ┌────────────▼────────────────┐
                        │     Orchestrator Agent       │
                        │   (LangGraph / CrewAI)       │
                        └──┬──────┬──────┬──────┬─────┘
                           │      │      │      │
              ┌────────────▼┐  ┌──▼───┐ ┌▼────┐ ┌▼──────────┐
              │  Repo        │  │Recru-│ │Ment-│ │Testing &  │
              │  Ingestion   │  │iter  │ │or   │ │DevOps     │
              │  Agent       │  │Agent │ │Agent│ │Agent      │
              └────────────┬┘  └──┬───┘ └┬────┘ └┬──────────┘
                           │      │       │       │
                        ┌──▼──────▼───────▼───────▼──┐
                        │      RAG Retrieval Layer    │
                        │  (Semantic + BM25 + Rerank) │
                        └────────────┬────────────────┘
                                     │
                        ┌────────────▼────────────────┐
                        │       Vector Database        │
                        │         (ChromaDB)           │
                        └────────────┬────────────────┘
                                     │
                        ┌────────────▼────────────────┐
                        │    GitHub Knowledge Base     │
                        │  Code, Commits, PRs, Docs    │
                        └────────────┬────────────────┘
                                     │
                        ┌────────────▼────────────────┐
                        │   Local LLM via Ollama       │
                        │   (Mistral / LLaMA3 / Gemma) │
                        └────────────┬────────────────┘
                                     │
                        ┌────────────▼────────────────┐
                        │    Grounded Final Output     │
                        └─────────────────────────────┘
```

---

## 🤖 Multi-Agent System

### Agent 1 — Repository Ingestion Agent
- Fetches GitHub repository via GitHub API
- Clones repo and extracts: code files, README, commits, issues, pull requests, CI/CD workflows, test files
- Outputs structured repository knowledge for downstream agents

### Agent 2 — Chunking & Embedding Agent
- Splits code files, documentation, commit messages, and architecture notes into semantic chunks
- Generates vector embeddings using **BGE-M3** (free, local, powerful)
- Stores all vectors into **ChromaDB** (100% free, runs locally forever)

### Agent 3 — Code Understanding RAG Agent
- Retrieves repository-specific context for any query
- Understands folder structure, dependency relationships, service layers, design patterns
- Example: *"Does this project follow clean architecture?"*

### Agent 4 — Recruiter Evaluation Agent
- Acts as a senior technical recruiter
- Evaluates: engineering maturity, production readiness, maintainability, scalability, collaboration practices
- Outputs: hiring confidence score (0–100), recruiter-style written feedback, employability insights

### Agent 5 — Documentation Intelligence Agent
- Performs RAG on README, wikis, inline comments, API docs
- Detects: missing setup instructions, unclear onboarding, absent contribution guides

### Agent 6 — Testing & DevOps Agent
- Retrieves CI/CD and testing information from the repo
- Evaluates: GitHub Actions, Docker setup, unit tests, integration tests, deployment readiness

### Agent 7 — Personalized Mentor Agent
- Creates a customized learning roadmap per developer
- Performs skill-gap analysis based on evaluated repositories
- Example output: *"To become interview-ready for backend roles, improve API validation, testing, and deployment practices."*

---

## 📚 RAG Pipeline

```
GitHub Repo
    │
    ▼
[Ingestion Agent] ──► Raw Files: .py, .js, .md, commits, PRs
    │
    ▼
[Chunking Agent] ──► Semantic Chunks (500 tokens, 50 overlap)
    │
    ▼
[Embedding Agent] ──► BGE-M3 Embeddings (local, free)
    │
    ▼
[ChromaDB] ──► Persistent Vector Store (local, no limits)
    │
    ▼
[Hybrid Retriever] ──► Semantic Search + BM25 Keyword Search
    │
    ▼
[Re-ranker] ──► Cross-encoder reranking (BGE-Reranker)
    │
    ▼
[Context Injection] ──► Top-K chunks passed to LLM
    │
    ▼
[Local LLM via Ollama] ──► Grounded, hallucination-free response
```

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔗 Submit GitHub URL | Paste any public or private GitHub repo URL |
| 📊 Repository Analysis | Full 7-agent analysis of code, docs, tests, CI/CD |
| 🤖 AI Chat | Ask natural language questions about the repository |
| 🧑‍💼 Recruiter Score | Hiring confidence score with detailed written feedback |
| 🗺️ Growth Roadmap | Personalized developer improvement plan |
| 🔁 Compare Repos | Side-by-side comparison with industry-standard projects |
| 📄 Download Report | Export full analysis as PDF |
| 🌐 Public Score Link | Share your repo score publicly |
| 📈 Track Progress | View score history over time |
| 👤 Profile & Preferences | User account with saved repos and settings |

---

## 🛠️ Free Tech Stack — 100% Open Source Forever

> Every tool below is **completely free**, **open-source**, and has **no usage limits** when self-hosted.

### 🧠 LLM Layer — FREE & LOCAL (No API bills ever)

| Tool | Purpose | Why Free Forever |
|---|---|---|
| **[Ollama](https://ollama.com/)** | Run LLMs locally | 100% local, no limits |
| **Mistral 7B** | Default LLM | Open-source Apache 2.0 |
| **LLaMA 3.1 8B** | Alternative LLM | Meta open-source |
| **Gemma 2 9B** | Alternative LLM | Google open-source |
| **CodeLlama** | Code-specialized LLM | Meta open-source |

### 📦 RAG Framework

| Tool | Purpose | Why Free Forever |
|---|---|---|
| **[LangChain](https://langchain.com/)** | RAG orchestration | MIT License, open-source |
| **[LlamaIndex](https://llamaindex.ai/)** | Document indexing | MIT License, open-source |
| **[LangGraph](https://langchain-ai.github.io/langgraph/)** | Multi-agent orchestration | MIT License |

### 🗄️ Vector Database — FREE & LOCAL

| Tool | Purpose | Why Free Forever |
|---|---|---|
| **[ChromaDB](https://trychroma.com/)** | Vector storage & retrieval | Apache 2.0, self-hosted |
| **[FAISS](https://faiss.ai/)** | Fast vector search | MIT License, Meta |

### 🔢 Embeddings — FREE & LOCAL

| Tool | Purpose | Why Free Forever |
|---|---|---|
| **[BGE-M3](https://huggingface.co/BAAI/bge-m3)** | Multilingual embeddings | Apache 2.0, runs locally |
| **[sentence-transformers](https://sbert.net/)** | Embedding framework | Apache 2.0 |
| **[BGE-Reranker](https://huggingface.co/BAAI/bge-reranker-v2-m3)** | Result re-ranking | Apache 2.0 |

### ⚙️ Backend

| Tool | Purpose | Why Free Forever |
|---|---|---|
| **[FastAPI](https://fastapi.tiangolo.com/)** | REST API backend | MIT License |
| **[Celery](https://celeryproject.org/)** | Async task queue | BSD License |
| **[Redis](https://redis.io/)** | Task broker & cache | BSD License, self-hosted |
| **[PostgreSQL](https://www.postgresql.org/)** | Main database | PostgreSQL License (free) |
| **[SQLAlchemy](https://sqlalchemy.org/)** | ORM | MIT License |
| **[Tree-sitter](https://tree-sitter.github.io/)** | Code parsing | MIT License |

### 🎨 Frontend

| Tool | Purpose | Why Free Forever |
|---|---|---|
| **[React 18](https://reactjs.org/)** | UI framework | MIT License |
| **[Tailwind CSS](https://tailwindcss.com/)** | Styling | MIT License |
| **[Shadcn/UI](https://ui.shadcn.com/)** | Component library | MIT License |
| **[Recharts](https://recharts.org/)** | Data visualization | MIT License |
| **[Vite](https://vitejs.dev/)** | Build tool | MIT License |

### 🐳 Infrastructure — Self-Hosted

| Tool | Purpose | Why Free Forever |
|---|---|---|
| **[Docker](https://docker.com/)** | Containerization | Free tier / open-source |
| **[Docker Compose](https://docs.docker.com/compose/)** | Multi-container setup | Free |
| **[MinIO](https://min.io/)** | File storage (S3-compatible) | AGPLv3, self-hosted |
| **[Nginx](https://nginx.org/)** | Reverse proxy | BSD License |

### 🔐 Authentication

| Tool | Purpose | Why Free Forever |
|---|---|---|
| **[Auth.js / NextAuth](https://authjs.dev/)** | Auth framework | ISC License |
| **[GitHub OAuth](https://docs.github.com/en/apps/oauth-apps)** | Login with GitHub | Free |

---

## 📁 Project Structure

```
repolens-x/
│
├── backend/
│   ├── agents/
│   │   ├── orchestrator.py          # Master agent controller
│   │   ├── ingestion_agent.py       # GitHub repo fetcher
│   │   ├── embedding_agent.py       # Chunking + embedding
│   │   ├── code_rag_agent.py        # Code understanding RAG
│   │   ├── recruiter_agent.py       # Hiring evaluation agent
│   │   ├── documentation_agent.py   # Docs intelligence agent
│   │   ├── devops_agent.py          # Testing & CI/CD agent
│   │   └── mentor_agent.py          # Growth roadmap agent
│   │
│   ├── rag/
│   │   ├── chunker.py               # Semantic text splitting
│   │   ├── embedder.py              # BGE-M3 embeddings
│   │   ├── vector_store.py          # ChromaDB interface
│   │   ├── retriever.py             # Hybrid search retriever
│   │   └── reranker.py              # Cross-encoder reranking
│   │
│   ├── api/
│   │   ├── main.py                  # FastAPI entry point
│   │   ├── routes/
│   │   │   ├── repos.py             # Repo submission routes
│   │   │   ├── analysis.py          # Analysis result routes
│   │   │   ├── chat.py              # AI chat routes
│   │   │   ├── reports.py           # PDF download routes
│   │   │   └── users.py             # Profile routes
│   │   └── middleware/
│   │       ├── auth.py
│   │       └── rate_limit.py
│   │
│   ├── models/
│   │   ├── repository.py
│   │   ├── analysis.py
│   │   └── user.py
│   │
│   ├── tasks/
│   │   └── celery_tasks.py          # Background job queue
│   │
│   ├── utils/
│   │   ├── github_client.py         # GitHub API wrapper
│   │   ├── pdf_generator.py         # Report PDF export
│   │   └── scoring.py               # Score computation
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── RepoSubmit.jsx
│   │   │   ├── AnalysisReport.jsx
│   │   │   ├── RecruiterScore.jsx
│   │   │   ├── MentorRoadmap.jsx
│   │   │   ├── ChatInterface.jsx
│   │   │   └── ProgressTracker.jsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Analysis.jsx
│   │   │   ├── Compare.jsx
│   │   │   └── Profile.jsx
│   │   │
│   │   ├── hooks/
│   │   ├── store/
│   │   └── App.jsx
│   │
│   ├── package.json
│   └── Dockerfile
│
├── vector_store/                    # ChromaDB persistent data
├── models/                          # Downloaded Ollama models
├── storage/                         # MinIO file storage
│
├── docker-compose.yml               # Full stack setup
├── .env.example
└── README.md
```

---

## ⚙️ Installation & Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- Git
- 8GB+ RAM recommended (for local LLM)

### Step 1 — Clone the Repository

```bash
git clone https://github.com/yourusername/repolens-x.git
cd repolens-x
```

### Step 2 — Install Ollama & Pull Models

```bash
# Install Ollama (Linux/Mac)
curl -fsSL https://ollama.com/install.sh | sh

# Pull the LLM models (choose one or more)
ollama pull mistral          # Recommended (fast, smart)
ollama pull llama3.1         # Best quality
ollama pull codellama        # Best for code tasks
ollama pull gemma2           # Lightweight option

# Pull embedding model
ollama pull nomic-embed-text
```

### Step 3 — Start Full Stack with Docker Compose

```bash
cp .env.example .env
# Edit .env with your GitHub token and settings

docker-compose up --build
```

### Step 4 — Manual Setup (Without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Start Redis (required for Celery)
redis-server

# Start Celery worker
celery -A tasks.celery_tasks worker --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

### Step 5 — Access the App

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8080 |
| API Docs (Swagger) | http://localhost:8080/docs |
| ChromaDB | http://localhost:8001 |
| MinIO Console | http://localhost:9001 |

---

## 🔐 Environment Variables

```env
# GitHub API
GITHUB_TOKEN=your_github_personal_access_token

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_EMBED_MODEL=nomic-embed-text

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/repolens

# Redis
REDIS_URL=redis://localhost:6379/0

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8001
CHROMA_PERSIST_DIR=./vector_store

# MinIO Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=repolens-reports

# Auth
SECRET_KEY=your_super_secret_key_here
GITHUB_CLIENT_ID=your_github_oauth_app_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_app_secret

# App Settings
DEBUG=True
ALLOWED_ORIGINS=http://localhost:5173
```

---

## 📡 API Endpoints

```
POST   /api/repos/submit              → Submit GitHub repository URL
GET    /api/repos/{repo_id}/status    → Check analysis status
GET    /api/repos/{repo_id}/report    → Get full analysis report
GET    /api/repos/{repo_id}/score     → Get recruiter score
POST   /api/chat/{repo_id}            → Ask AI questions about repo
GET    /api/repos/{repo_id}/roadmap   → Get mentor growth roadmap
POST   /api/repos/compare             → Compare two repositories
GET    /api/reports/{repo_id}/pdf     → Download PDF report
GET    /api/repos/public/{repo_id}    → View public score page
GET    /api/users/me/history          → Get user repo history
GET    /api/users/me/progress         → Track progress over time
PUT    /api/users/me/preferences      → Update user preferences
```

---

## 💬 Use Cases / Example Queries

You can ask the AI chat anything about a repository:

```
"Why is my architecture weak?"
"What backend engineering practices are missing?"
"How would a Google recruiter evaluate this project?"
"Is this repository production-ready?"
"What skills does this repo demonstrate?"
"Compare my repo with a senior engineer's project."
"What is missing to make this interview-ready?"
"Generate a 3-month improvement roadmap for this repo."
"Which files hurt maintainability the most?"
"Does this project follow SOLID principles?"
```

---

## 🗺️ Roadmap

### Phase 1 — Core (MVP)
- [x] Project architecture design
- [ ] GitHub API integration
- [ ] Repository ingestion pipeline
- [ ] ChromaDB vector store setup
- [ ] Basic RAG with Ollama (local LLM)
- [ ] FastAPI backend skeleton
- [ ] React frontend skeleton

### Phase 2 — Agents
- [ ] Orchestrator Agent (LangGraph)
- [ ] Ingestion Agent
- [ ] Embedding Agent
- [ ] Code Understanding RAG Agent
- [ ] Recruiter Evaluation Agent
- [ ] Documentation Intelligence Agent
- [ ] Testing & DevOps Agent
- [ ] Mentor Roadmap Agent

### Phase 3 — Advanced Features
- [ ] Hybrid retrieval (BM25 + semantic)
- [ ] Cross-encoder reranking
- [ ] PDF report generation
- [ ] Public score sharing link
- [ ] Repository comparison engine
- [ ] Progress tracking dashboard

### Phase 4 — Production
- [ ] Docker Compose full deployment
- [ ] Nginx reverse proxy
- [ ] User authentication (GitHub OAuth)
- [ ] Rate limiting & security hardening
- [ ] Performance optimization
- [ ] Unit and integration tests

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the **MIT License** — you are free to use, modify, distribute, and build on this project forever with no restrictions.

See the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

Built with ❤️ as a portfolio project demonstrating:

- Multi-Agent AI Systems
- Retrieval-Augmented Generation (RAG)
- LLM Orchestration
- Vector Databases
- Full-Stack AI Application Development

---

## ⭐ Star this repo if it helped you!

> *"RepoLens X — Where repositories become intelligence."*
