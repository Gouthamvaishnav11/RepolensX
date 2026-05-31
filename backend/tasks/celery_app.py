import sys
import os

# Fix module path — must be first
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from celery import Celery
from config import settings

celery_app = Celery(
    "repolens",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["tasks.analysis_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    broker_connection_retry_on_startup=True,
)

@celery_app.task(name="tasks.celery_app.analyze_repository_task", bind=True)
def analyze_repository_task(self, repo_id: str, user_id: str):
    from tasks.analysis_tasks import run_full_analysis
    return run_full_analysis(repo_id, user_id)