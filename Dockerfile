# Base stage - Install dependencies
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app/

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /uvx /bin/

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

# uv Cache
ENV UV_LINK_MODE=copy

# Install dependencies (without bytecode compilation to avoid timeouts)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev --no-compile-bytecode

# Copy application code
COPY ./pyproject.toml ./uv.lock ./alembic.ini ./logging.ini /app/
COPY ./src /app/src
COPY ./scripts /app/scripts
COPY ./alembic /app/alembic

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --no-compile-bytecode

# Runtime stage - Minimal image
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app/

# Install only runtime dependencies (curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment and application from base
COPY --from=base /app/.venv /app/.venv
COPY --from=base /app/pyproject.toml /app/uv.lock /app/alembic.ini /app/logging.ini /app/
COPY --from=base /app/src /app/src
COPY --from=base /app/alembic /app/alembic
COPY --from=base /app/scripts /app/scripts

# Create logs directory and make entrypoint executable
RUN mkdir -p /app/logs && \
    chmod +x /app/scripts/entrypoint.sh && \
    # Fix Windows line endings (CRLF -> LF)
    sed -i 's/\r$//' /app/scripts/entrypoint.sh && \
    # Verify the file exists
    ls -la /app/scripts/entrypoint.sh

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["run-server"]
