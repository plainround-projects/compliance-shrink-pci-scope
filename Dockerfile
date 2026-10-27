# The three apps as one image: pinned base, hash-pinned dependencies, a non-root user, a health check, gunicorn.
# Run a service by choosing the app: `provider` (one worker, its state is in memory), `merchant` or `naive`.
FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock

COPY pyproject.toml README.md ./
COPY src ./src
COPY sql ./sql
RUN pip install --no-deps .

RUN useradd --system --uid 10001 --create-home app && mkdir -p /app/state && chown app /app/state
USER app

ENV APP=merchant PORT=5000
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/healthz' if os.environ['APP'] != 'naive' else f'http://127.0.0.1:{os.environ[\"PORT\"]}/', timeout=3)"]
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:$PORT --workers $([ \"$APP\" = provider ] && echo 1 || echo 2) --threads 8 --timeout 30 --graceful-timeout 20 \"pci_scope.interfaces.factories:$APP()\""]
