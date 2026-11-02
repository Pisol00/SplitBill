# Used by two Compose services: migrate (runs Alembic, then exits) and api.

# Install the locked dependencies, without development tools.
FROM python:3.14-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /usr/local/bin/uv
ENV UV_PYTHON_DOWNLOADS=never UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

# The runtime image has no uv, and does not run as root.
FROM python:3.14-slim
RUN useradd --create-home app
WORKDIR /app
COPY --from=build /app/.venv .venv
COPY pyproject.toml alembic.ini ./
COPY alembic alembic
COPY app app
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
