# Production runtime image. Runtime configuration is intentionally supplied by
# the deployment environment; the application refuses unsafe production values.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

RUN groupadd --system agentos && useradd --system --gid agentos --home-dir /app agentos

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=agentos:agentos . ./

USER agentos
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
