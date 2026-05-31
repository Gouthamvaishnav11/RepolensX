@echo off
cd C:\Users\gouth\Downloads\repolensX\backend
call venv\Scripts\activate
set PYTHONPATH=C:\Users\gouth\Downloads\repolensX\backend
celery -A tasks.celery_app worker --loglevel=info --pool=solo
pause