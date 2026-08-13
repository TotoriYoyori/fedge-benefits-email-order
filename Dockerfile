FROM python:3.13-slim

WORKDIR /app

# --------------- INSTALL UV
COPY --from=ghcr.io/astral-sh/uv:0.11.7 /uv /uvx /bin/

# --------------- SET UP NON-ROOT USER (SECURITY PATTERN)
RUN groupadd --system --gid 999 nonroot \
    && useradd --system --gid 999 --uid 999 --create-home nonroot

# --------------- RECOMMENDED UV OPTIMIZATION
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_DEV=1

# --------------- PACKAGE DEPENDENCIES
COPY uv.lock pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/uv \
 uv sync --locked --no-install-project

# --------------- INSTALL PROJECT
COPY --chown=nonroot:nonroot . .

RUN --mount=type=cache,target=/root/.cache/uv \
 uv sync --locked

# --------------- PLACE EXE PATH
ENV PATH="/app/.venv/bin:$PATH"

# --------------- BOOT
ENTRYPOINT []

USER nonroot

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.main:app --host 0.0.0.0 --port 8000"]
