FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl unzip \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-reflex.txt .
RUN pip install --no-cache-dir -r requirements-reflex.txt

COPY . .

ENV REFLEX_ENV=prod
ENV PORT=8000

RUN reflex init --loglevel error || true
RUN reflex export --frontend-only --no-zip || true

EXPOSE 8000

CMD reflex run --env prod --backend-only --backend-host 0.0.0.0 --backend-port 8000