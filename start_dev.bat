@echo off
echo Starting RepoLens X Development...

echo Starting Docker containers...
docker-compose up -d postgres redis chromadb

echo Waiting for services...
timeout /t 5

echo Starting Backend...
start "Backend" cmd /k "cd backend && Backup\Scripts\activate && set PYTHONPATH=%cd% && uvicorn api.main:app --reload --port 8080"

echo Starting Celery...
start "Celery" cmd /k "cd backend && Backup\Scripts\activate && set PYTHONPATH=%cd% && celery -A tasks.celery_app worker --loglevel=info --pool=solo"

echo Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo All services started!
echo Frontend: http://localhost:5173
echo Backend:  http://localhost:8080
echo API Docs: http://localhost:8080/docs
