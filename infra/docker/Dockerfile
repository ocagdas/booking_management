FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY . .

RUN if [ -f pyproject.toml ]; then pip install -e ".[dev]"; else echo "No pyproject.toml yet; Sprint 1 scaffold has not been created."; fi

CMD ["sh", "-c", "if [ -f app/main.py ]; then uvicorn app.main:app --host 0.0.0.0 --port 8000; else echo 'Sprint 1 app scaffold has not been created yet.'; sleep infinity; fi"]
