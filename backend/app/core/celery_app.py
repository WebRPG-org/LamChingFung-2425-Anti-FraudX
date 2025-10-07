import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=["app.ingestion.tasks"] 
)
celery_app.conf.timezone = 'Asia/Hong_Kong'