# Docker Compose

## What it is

Docker Compose reads one YAML file that lists **services** (containers), their images, ports, environment and volumes, and starts them together with
`docker compose up`. YAML **anchors** (`&name`) and **aliases** (`*name`) let you reuse a block, and the **merge key** `<<:` copies a mapping into another.

## Why this repository uses it

The provider and the merchant need the same hardening and mostly the same environment. One shared block keeps them identical; each service adds
only what is different (its app, its port, its volume).

## Where it appears

| File | What it does with this technology |
| --- | --- |
| `docker-compose.yml` | Two services, one named volume. |
| `.env` | Compose reads it to fill the `${...}` placeholders (the keys and the webhook secret). |
| `Makefile` | Does not call Compose; the README shows `docker compose up --build`. |

## How it works underneath

Compose reads `.env` in the project folder to substitute `${VARIABLE}`, then asks the Docker engine to create a network, a volume and the containers.
Services reach each other by name on the private network (`http://provider:5001`). A top-level key starting with `x-` is an **extension**: Compose
ignores it, so it is a safe place to define an anchor.

## Walkthrough of this repository's use

`docker-compose.yml`:

```yaml
x-common: &common
  build: .
  read_only: true
  tmpfs: ["/tmp"]
  cap_drop: [ALL]
  security_opt: ["no-new-privileges:true"]
  environment: &env
    PROVIDER_SECRET_KEY: ${PROVIDER_SECRET_KEY:?set it in .env}
    PROVIDER_PUBLISHABLE_KEY: ${PROVIDER_PUBLISHABLE_KEY:?set it in .env}
    WEBHOOK_SECRET: ${WEBHOOK_SECRET:?set it in .env}
    PROVIDER_BASE_URL: http://provider:5001
    PROVIDER_PUBLIC_URL: http://127.0.0.1:5001
    MERCHANT_BASE_URL: http://merchant:5000
```

- `x-common: &common` names this block `common`. It holds what both services share:
  - `build: .` builds the image from the `Dockerfile` here.
  - `read_only: true`: the root file system cannot be written to; `tmpfs: ["/tmp"]` gives an in-memory scratch folder.
  - `cap_drop: [ALL]`: remove every Linux capability from the process; `security_opt: ["no-new-privileges:true"]`: it can never gain privileges.
  - `environment: &env` defines the shared environment and names it `env`. `${PROVIDER_SECRET_KEY:?set it in .env}` uses the variable or **stops with that
    message** if it is not set. `PROVIDER_BASE_URL: http://provider:5001` is the provider's address *inside* the network; `PROVIDER_PUBLIC_URL` is the
    address the browser uses.

`docker-compose.yml`:

```yaml
services:
  provider:
    <<: *common
    environment:
      <<: *env
      APP: provider
      PORT: "5001"
    ports:
      - "127.0.0.1:5001:5001"
```

`<<: *common` copies the shared block into the service. Because a merge key does not merge nested mappings, `environment:` is repeated
with `<<: *env` (the shared variables) plus `APP: provider` and `PORT: "5001"`. `ports: "127.0.0.1:5001:5001"` publishes the port on the host's local address only.

`docker-compose.yml`:

```yaml
  merchant:
    <<: *common
    depends_on:
      - provider
    environment:
      <<: *env
      APP: merchant
      PORT: "5000"
      DATABASE_PATH: /app/state/merchant.db
    volumes:
      - merchant-state:/app/state
    ports:
      - "127.0.0.1:5000:5000"

volumes:
```

The merchant depends on the provider (`depends_on`), sets `DATABASE_PATH` inside the container, and mounts the named volume `merchant-state` at
`/app/state` so its database survives a restart while the rest of the file system is read-only.

### The complete file `docker-compose.yml`, line by line

`docker-compose.yml` lines 1 to 16:

```yaml
# The provider and the merchant as two containers. The browser talks to both on localhost; the merchant reaches the
# provider by its service name. Open http://127.0.0.1:5000 after `docker compose up --build`.
# The naive checkout is not here on purpose: run it with `make serve-naive`, test card only.
x-common: &common
  build: .
  read_only: true
  tmpfs: ["/tmp"]
  cap_drop: [ALL]
  security_opt: ["no-new-privileges:true"]
  environment: &env
    PROVIDER_SECRET_KEY: ${PROVIDER_SECRET_KEY:?set it in .env}
    PROVIDER_PUBLISHABLE_KEY: ${PROVIDER_PUBLISHABLE_KEY:?set it in .env}
    WEBHOOK_SECRET: ${WEBHOOK_SECRET:?set it in .env}
    PROVIDER_BASE_URL: http://provider:5001
    PROVIDER_PUBLIC_URL: http://127.0.0.1:5001
    MERCHANT_BASE_URL: http://merchant:5000
```

> **In plain words.** YAML is a settings format that uses indentation (spaces, never tabs) to show what belongs to what. `key: value` sets a value, `- item` is one entry of a list, `&name` names a block and `*name` reuses it, and `#` starts a comment.

- `x-common` is named `&common` here so other places can reuse it with `*common`.
- A setting `build` (build the image from this folder) is `.`.
- A setting `read_only` (make the root file system read-only) is `true`.
- A setting `tmpfs` (in-memory scratch folders) is `["/tmp"]`.
- A setting `cap_drop` (Linux capabilities to remove) is `[ALL]`.
- A setting `security_opt` (extra security options) is `["no-new-privileges:true"]`.
- `environment` (environment variables) is named `&env` here so other places can reuse it with `*env`.
- A setting `PROVIDER_SECRET_KEY` is `${PROVIDER_SECRET_KEY:?set it in .env}`.
- A setting `PROVIDER_PUBLISHABLE_KEY` is `${PROVIDER_PUBLISHABLE_KEY:?set it in .env}`.
- A setting `WEBHOOK_SECRET` is `${WEBHOOK_SECRET:?set it in .env}`.
- A setting `PROVIDER_BASE_URL` is `http://provider:5001`.
- A setting `PROVIDER_PUBLIC_URL` is `http://127.0.0.1:5001`.
- A setting `MERCHANT_BASE_URL` is `http://merchant:5000`.

`docker-compose.yml` lines 18 to 39:

```yaml
services:
  provider:
    <<: *common
    environment:
      <<: *env
      APP: provider
      PORT: "5001"
    ports:
      - "127.0.0.1:5001:5001"
  merchant:
    <<: *common
    depends_on:
      - provider
    environment:
      <<: *env
      APP: merchant
      PORT: "5000"
      DATABASE_PATH: /app/state/merchant.db
    volumes:
      - merchant-state:/app/state
    ports:
      - "127.0.0.1:5000:5000"
```

- A setting `services` (the containers) starts a group; the more indented lines below belong to it.
- A setting `provider` starts a group; the more indented lines below belong to it.
- A setting `<<` is `*common`.
- A setting `environment` (environment variables) starts a group; the more indented lines below belong to it.
- A setting `<<` is `*env`.
- A setting `APP` is `provider`.
- A setting `PORT` is `"5001"`.
- A setting `ports` (ports to publish) starts a group; the more indented lines below belong to it.
- A list item `"127.0.0.1:5001:5001"`.
- A setting `merchant` starts a group; the more indented lines below belong to it.
- A setting `<<` is `*common`.
- A setting `depends_on` (start after these services) starts a group; the more indented lines below belong to it.
- A list item `provider`.
- A setting `environment` (environment variables) starts a group; the more indented lines below belong to it.
- A setting `<<` is `*env`.
- A setting `APP` is `merchant`.
- A setting `PORT` is `"5000"`.
- A setting `DATABASE_PATH` is `/app/state/merchant.db`.
- A setting `volumes` (storage that outlives the container) starts a group; the more indented lines below belong to it.
- A list item `merchant-state` is `/app/state`.
- A setting `ports` (ports to publish) starts a group; the more indented lines below belong to it.
- A list item `"127.0.0.1:5000:5000"`.

`docker-compose.yml` lines 41 to 42:

```yaml
volumes:
  merchant-state:
```

- A setting `volumes` (storage that outlives the container) starts a group; the more indented lines below belong to it.
- A setting `merchant-state` starts a group; the more indented lines below belong to it.

## Try it yourself

Not run while this note was written: the machine was out of capacity, so no container was started. The expected output follows from the files quoted above and from the README's verified runs.

```bash
docker compose config --quiet && echo "compose file is valid"
```
Checks the YAML and the variables (needs `.env`; run `make env` first).

```bash
docker compose config | sed -n 1,20p
```
Prints the file with the anchors expanded and variables replaced.

```bash
docker compose up --build -d
```
Starts both containers; open `http://127.0.0.1:5000`.

```bash
docker compose exec -T merchant id && docker compose down -v
```
Prints `uid=10001(app) ...`, then removes the containers and the volume.

## Mistakes people make

- **Forgetting that `<<:` merges only the top level**, so a nested `environment:` must be merged again.
- **Real keys in the compose file.** Values come from `.env`; a missing one stops the run.
- **Publishing ports on all interfaces.** These bind to `127.0.0.1`.
- **A writable root file system** where it is not needed.
- **Using the live keys.** The program refuses any key that is not `sk_test_...` / `pk_test_...`.

## Check yourself

1. What do `&common` and `*common` do?
   **Answer:** Name a block and reuse it elsewhere.
2. What does `<<:` do?
   **Answer:** Merges a mapping into this one (top level only).
3. What does `${VAR:?message}` do?
   **Answer:** Uses the variable, or stops with the message if it is not set.
4. Why does the merchant mount a volume?
   **Answer:** Its database must survive a restart although the root file system is read-only.
5. How does the merchant reach the provider?
   **Answer:** By service name: `http://provider:5001`.

## Further reading

- Compose file reference: <https://docs.docker.com/reference/compose-file/>
- Fragments and extensions (anchors, `x-`): <https://docs.docker.com/reference/compose-file/fragments/>
- Interpolation: <https://docs.docker.com/reference/compose-file/interpolation/>
