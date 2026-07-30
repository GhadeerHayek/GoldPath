# Build stage: resolve dependencies from the same lockfile CI verifies, so the
# deployed image cannot drift from what the tests ran against.
FROM python:3.14-slim AS builder

# Pin the installer. An unpinned `pip install uv` is a supply-chain hole in an
# image we deploy to a real host.
RUN pip install --no-cache-dir "uv==0.11.32"

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev


# Runtime stage: carry over only the virtualenv and the app, leaving uv, pip
# caches, and build tooling out of the shipped image.
FROM python:3.14-slim AS runtime

LABEL org.opencontainers.image.source="https://github.com/GhadeerHayek/GoldPath"
LABEL org.opencontainers.image.description="GoldPath demo application"

# Never run the app as root. If the process is compromised, the blast radius
# stops at a user that owns nothing.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --chown=appuser:appuser app ./app

ENV PATH="/app/.venv/bin:$PATH"

USER appuser

# 8000, not 80: binding a privileged port would mean running as root. Traefik
# terminates TLS and forwards here.
EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
