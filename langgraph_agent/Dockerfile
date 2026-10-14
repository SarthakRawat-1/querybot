FROM python:3.12-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl docker.io gcc g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen

ENV PYTHONUNBUFFERED=1 MPLBACKEND=Agg PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

CMD ["langgraph", "dev", "--host", "0.0.0.0", "--port", "8000", "--no-browser"]
