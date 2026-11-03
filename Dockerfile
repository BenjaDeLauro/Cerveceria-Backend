FROM python:3.14-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.13.6 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

RUN groupadd --gid 10001 django \
    && useradd --uid 10001 --gid django --no-create-home django \
    && mkdir -p /app/data /app/media \
    && chown django:django /app/data /app/media

COPY --chown=django:django . .
USER django

EXPOSE 8000
ENTRYPOINT ["python", "docker/entrypoint.py"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"]
