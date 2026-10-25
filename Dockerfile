# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app

# Install build tools needed by some Python dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# The package install needs the source, so this layer rebuilds on code changes;
# the pip cache mount keeps those rebuilds from downloading the wheels again.
COPY pyproject.toml README.md ./
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/pip pip install .

# Runtime assets read relative to the working directory (static UI, raw policies)
COPY . .

EXPOSE 8000

CMD ["uvicorn", "telecopilot.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
