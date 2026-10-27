# Docker

## What it is

A **container** is a running program that sees its own private file system and network, built from an **image** (a packaged file system plus
a start command). Docker builds images and runs containers. **Docker Compose** describes several containers in one file.

## Why this repository uses it

The scenario itself does **not** need Docker (it runs real servers in the test process). Docker is optional here: it shows the apps as they would
run in production, with a pinned image, a non-root user, a read-only file system and a health check. CI builds the image to prove the Dockerfile works.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `Dockerfile` | One image for all three apps (see `dockerfile.md`). |
| `docker-compose.yml` | The provider and the merchant as two containers (see `docker-compose.md`). |
| `.dockerignore` | What stays out of the build context. |
| `Makefile` `docker-build` | `docker build -t compliance-shrink-pci-scope:dev .` |
| .github/workflows/ci.yml | The `image` job builds the image. |

## How it works underneath

An **image** is made of read-only **layers**, one per Dockerfile instruction, cached when unchanged. A **container** adds a thin writable
layer and runs one main process (process 1). A **volume** is storage that outlives the container. On a Mac, Docker runs a small Linux
virtual machine, which is why its memory and CPU limits matter. The **build context** is the folder sent to the builder; `.dockerignore`
removes files from it.

## Walkthrough of this repository's use

`Makefile`:

```make
docker-build: ## build the image of the three apps
	docker build -t compliance-shrink-pci-scope:dev .
```

`docker build -t compliance-shrink-pci-scope:dev .` builds the image from the `Dockerfile` in this folder and tags it `name:tag`.

`.github/workflows/ci.yml`:

```yaml
  image:
    name: The image builds
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
```

The CI job `image` checks out the code and builds the image with the tag `compliance-shrink-pci-scope:ci`. If the Dockerfile is broken, the job fails.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output follows from the files quoted above and from the README's verified runs.

```bash
docker --version && docker compose version
```
Prints the client versions.

```bash
make docker-build
```
Builds the image; the last lines show `naming to docker.io/library/compliance-shrink-pci-scope:dev`.

```bash
docker compose up --build -d && docker compose ps
```
Starts the provider and the merchant; `ps` lists them (health `healthy` after a short wait). Open `http://127.0.0.1:5000`.

```bash
docker compose down -v
```
Removes the containers and the volume.

## Mistakes people make

- **Leaving containers running** on a shared machine.
- **Putting `.env` or secrets in an image.** `.dockerignore` excludes them.
- **Running as root inside the container.** The image creates a user.
- **Starting the naive app in a container.** It is deliberately not in Compose: it exists to be measured, with the test card only.

## Check yourself

1. Does the scenario need Docker?
   **Answer:** No; it runs real servers inside the test process.
2. What does `docker build -t name:tag .` do?
   **Answer:** Builds an image from the Dockerfile in this folder and tags it.
3. What does the CI `image` job prove?
   **Answer:** That the Dockerfile builds.
4. What does `down -v` remove?
   **Answer:** The containers and their volumes.
5. Why is the naive app not in Compose?
   **Answer:** It is only for measuring, with the test card.

## Further reading

- Docker documentation: <https://docs.docker.com/>
- Docker Compose file reference: <https://docs.docker.com/reference/compose-file/>
- `.dockerignore`: <https://docs.docker.com/build/concepts/context/#dockerignore-files>
