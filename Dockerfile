# Python runtime for the DeepSight backend and worker.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements-backend.txt .

RUN pip install --upgrade pip \
    && pip install -r requirements-backend.txt

ENV YOLO_CONFIG_DIR=/tmp

COPY ml ./ml
COPY services ./services
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
