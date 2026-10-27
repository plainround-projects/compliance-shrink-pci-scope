# Dockerfile

## What it is

A **Dockerfile** is a text file of instructions that `docker build` follows to make an image. Each instruction (`FROM`, `COPY`, `RUN`, ...) adds a
layer. The last ones say how the container starts (`CMD`) and how to check that it is healthy (`HEALTHCHECK`).

## Why this repository uses it

One image serves the provider and the merchant (and the naive app if you choose it): the environment variable `APP` picks which. The same hardening
applies to all: pinned base image, hash-checked dependencies, an unprivileged user, a health check and graceful shutdown.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Dockerfile` | The only one. |
| `docker-compose.yml` | `build: .` builds it for both services. |
| `Makefile` `docker-build`, `ci.yml` job `image` | Build it. |

## How it works underneath

`docker build` runs the instructions in order and caches each layer; an instruction is rebuilt only if it or the files it uses changed. So
**order matters**: put the dependency list before the source. The result is an image; Compose or `docker run` starts a container from it.

## Walkthrough of this repository's use

`Dockerfile`:

```dockerfile
FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
```

`FROM image@sha256:...` pins the exact base image (Python 3.12.8, slim Debian bookworm). A tag can move; a digest cannot.

`Dockerfile`:

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

Environment for the build and run: no `.pyc` files, unbuffered output (logs appear at once), no pip cache, no pip version nag.

`Dockerfile`:

```dockerfile
WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock
```

`requirements.lock` is copied and installed **first** with `--require-hashes`, so that layer is rebuilt only when the lock file changes.

`Dockerfile`:

```dockerfile
COPY pyproject.toml README.md ./
COPY src ./src
COPY sql ./sql
RUN pip install --no-deps .
```

Then the project (`pyproject.toml`, `README.md`, `src`, and `sql` because the merchant reads `sql/001_schema.sql` at start-up) and `pip install --no-deps .`.

`Dockerfile`:

```dockerfile
RUN useradd --system --uid 10001 --create-home app && mkdir -p /app/state && chown app /app/state
USER app
```

Creates an unprivileged user and a state folder it owns (`mkdir -p /app/state && chown app /app/state`), then `USER app`: every later instruction and
the running container use it. `--create-home` gives the user a home folder; the root file system is read-only at run time (see
`docker-compose.md`), so the state folder is a mounted volume.

`Dockerfile`:

```dockerfile
ENV APP=merchant PORT=5000
EXPOSE 5000
```

Defaults: run the merchant on port 5000. `EXPOSE 5000` documents the port.

`Dockerfile`:

```dockerfile
HEALTHCHECK --interval=30s --timeout=20s --start-period=30s --retries=3 CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/healthz' if os.environ['APP'] != 'naive' else f'http://127.0.0.1:{os.environ[\"PORT\"]}/', timeout=3)"]
```

Docker runs the check every 30 s, waits up to 20 s, ignores failures for the first 30 s, and marks the container unhealthy after 3 failures.
The command is a Python one-liner using `urllib.request.urlopen`: it asks `/healthz` (or `/` for the naive app, which has no health route), so the image
needs no `curl`.

`Dockerfile`:

```dockerfile
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:$PORT --workers $([ \"$APP\" = provider ] && echo 1 || echo 2) --threads 8 --timeout 30 --graceful-timeout 20 --no-control-socket \"pci_scope.interfaces.factories:$APP()\""]
```

The start command is explained in `gunicorn.md`.

### The complete file `Dockerfile`, line by line

`Dockerfile` lines 1 to 3:

```dockerfile
# The three apps as one image: pinned base, hash-pinned dependencies, a non-root user, a health check, gunicorn.
# Run a service by choosing the app: `provider` (one worker, its state is in memory), `merchant` or `naive`.
FROM python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
```

> **In plain words.** A Dockerfile is a list of instructions that `docker build` runs in order to make an **image**: a packaged file system plus a start command. Each instruction adds a **layer**, and Docker reuses a layer when nothing it depends on changed, so the order matters.

- `FROM` starts the image from this base image (the `@sha256:` part pins the exact version): `python:3.12.8-slim-bookworm@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0`.

`Dockerfile` lines 5 to 8:

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
```

- `ENV` sets environment variables for the build and for the running container: `PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1`. `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, `PIP_NO_CACHE_DIR=1`, `PIP_DISABLE_PIP_VERSION_CHECK=1`.

`Dockerfile` lines 10 to 12:

```dockerfile
WORKDIR /app
COPY requirements.lock ./
RUN pip install --require-hashes -r requirements.lock
```

- `WORKDIR` sets the folder that later instructions run in: `/app`.
- `COPY` copies files from the build folder into the image: `requirements.lock ./`.
- `RUN` runs a command while the image is built: `pip install --require-hashes -r requirements.lock`. It runs pip, the package installer, subcommand `install` with `--require-hashes` (refuse any package without a pinned hash), `-r requirements.lock` (read the list from the named file).

`Dockerfile` lines 14 to 17:

```dockerfile
COPY pyproject.toml README.md ./
COPY src ./src
COPY sql ./sql
RUN pip install --no-deps .
```

- `COPY` copies files from the build folder into the image: `pyproject.toml README.md ./`.
- `COPY` copies files from the build folder into the image: `src ./src`.
- `COPY` copies files from the build folder into the image: `sql ./sql`.
- `RUN` runs a command while the image is built: `pip install --no-deps .`. It runs pip, the package installer, subcommand `install` with `--no-deps` (do not install or resolve dependencies), `.`.

`Dockerfile` lines 19 to 20:

```dockerfile
RUN useradd --system --uid 10001 --create-home app && mkdir -p /app/state && chown app /app/state
USER app
```

- `RUN` runs a command while the image is built: `useradd --system --uid 10001 --create-home app && mkdir -p /app/state && chown app /app/state`. It runs useradd, which creates an operating-system user with `--system` (a system account), `--uid 10001` (numeric user id), `--create-home` (create a home folder), `app`; if that works, it runs mkdir, which creates a folder with `-p` (make parent folders), `/app/state`; if that works, it runs chown, which changes who owns a file with `app`, `/app/state`.
- `USER` makes later instructions and the running container use this user: `app`.

`Dockerfile` lines 22 to 25:

```dockerfile
ENV APP=merchant PORT=5000
EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=20s --start-period=30s --retries=3 CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ[\"PORT\"]}/healthz' if os.environ['APP'] != 'naive' else f'http://127.0.0.1:{os.environ[\"PORT\"]}/', timeout=3)"]
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:$PORT --workers $([ \"$APP\" = provider ] && echo 1 || echo 2) --threads 8 --timeout 30 --graceful-timeout 20 --no-control-socket \"pci_scope.interfaces.factories:$APP()\""]
```

- `ENV` sets environment variables for the build and for the running container: `APP=merchant PORT=5000`. `APP=merchant`, `PORT=5000`.
- `EXPOSE` documents the port the app listens on: `5000`.
- `HEALTHCHECK` tells Docker how to test that the container works: `--interval=30s --timeout=20s --start-period=30s --retries=3 CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen(f'http:…`. `--interval` is the time between checks, `--timeout` how long one may take, `--start-period` the grace time after start, `--retries` the failures allowed in a row.
- `CMD` sets the command that runs when a container starts: `["sh", "-c", "exec gunicorn --bind 0.0.0.0:$PORT --workers $([ \"$APP\" = provider ] && echo 1 || echo 2) --threads 8 --timeout 30 --gracef…`. The JSON list form (exec form) runs the program directly, with no shell in between.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output follows from the files quoted above and from the README's verified runs.

```bash
make docker-build
```
Builds the image.

```bash
docker run --rm --entrypoint id compliance-shrink-pci-scope:dev
```
Prints `uid=10001(app) gid=... groups=...`: the image runs as the unprivileged user.

```bash
grep -n "^[A-Z]" Dockerfile
```
Lists the instructions (this one needs no Docker).

```bash
docker history compliance-shrink-pci-scope:dev | head -8
```
Lists the layers, newest first.

## Mistakes people make

- **Copying the source before installing dependencies**, which reinstalls everything on each code change.
- **A moving tag** instead of a digest.
- **Running as root.**
- **Using shell form for `CMD` without `exec`**, so signals do not reach gunicorn.
- **Forgetting files the app reads at run time** (`sql/`), which then fail only in the container.

## Check yourself

1. Why is `requirements.lock` installed before `src` is copied?
   **Answer:** To cache the dependency layer.
2. What does `@sha256:` pin?
   **Answer:** The exact base image.
3. Why is `sql/` copied into the image?
   **Answer:** The merchant reads `sql/001_schema.sql` at start-up.
4. What does `HEALTHCHECK` do?
   **Answer:** Runs a command on a schedule and marks the container healthy or unhealthy.
5. Why does the health check use Python and not curl?
   **Answer:** The image has Python already; no extra tool is needed.

## Further reading

- Dockerfile reference: <https://docs.docker.com/reference/dockerfile/>
- Build best practices: <https://docs.docker.com/build/building/best-practices/>
- Official Python image: <https://hub.docker.com/_/python>
