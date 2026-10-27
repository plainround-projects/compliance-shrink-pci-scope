# GitHub Actions

## What it is

**Continuous integration (CI)** means a server runs your checks each time you push. **GitHub Actions** is GitHub's CI service. A **workflow** is a YAML
file in `.github/workflows/`. It names the events that start it and the **jobs** to run. A **job** is a list of **steps** on a fresh virtual machine (a
**runner**). Jobs run in parallel unless one waits for another.

## Why this repository uses it

The README promises that the checks, the scenario and the image build all pass. CI is the independent witness: it builds from a clean checkout. The scenario
job also saves the evidence pack as a downloadable artifact.

## Where it appears

| File | What it does with this technology |
| --- | --- |
| .github/workflows/ci.yml | Jobs `check`, `scenario`, `image`. |
| `Makefile` | The jobs call `make` targets (and `docker build`). |

## How it works underneath

1. You push a commit or open a pull request. GitHub reads every file in `.github/workflows/`.
2. For each job it starts a clean Ubuntu runner. Steps run in order: `uses:` runs a packaged action pinned by a tag like `@v4`, `run:` runs a shell
   command. A failing step fails the job.
3. An **artifact** is a file a job saves (`actions/upload-artifact`) so you can download it later.

## Walkthrough of this repository's use

`.github/workflows/ci.yml`:

```yaml
name: ci

on: [push, pull_request]

jobs:
  check:
    name: Format, lint, types, import rules, unit tests with coverage, dependency audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: make check
      - run: make audit
```

- `on: [push, pull_request]`: run on every push and pull request.
- Job `check`: set up Python 3.12 (quoted, so YAML keeps it as text), then `make check` (lint, types, import rules, unit tests with coverage) and `make audit`.

`.github/workflows/ci.yml`:

```yaml
  scenario:
    name: The scenario against real local servers, the evidence pack and its verification
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: make test-e2e
      - run: make run
      - run: make verify
      - uses: actions/upload-artifact@v4
        with:
          name: evidence
          path: evidence/
```

- Job `scenario` runs the end-to-end test against real local servers (`make test-e2e`), then the whole demo (`make run`), then `make verify` (the pack is
  checked against the requirements), and uploads the `evidence/` folder as the artifact `evidence`.

`.github/workflows/ci.yml`:

```yaml
  image:
    name: The image builds
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
```

Job `image` builds the Docker image. It uses `docker build` directly (the runner has Docker), so a broken Dockerfile fails CI.

### The complete file `.github/workflows/ci.yml`, line by line

`.github/workflows/ci.yml` lines 1 to 1:

```yaml
name: ci
```

> **In plain words.** YAML is a settings format that uses indentation (spaces, never tabs) to show what belongs to what. `key: value` sets a value, `- item` is one entry of a list, `&name` names a block and `*name` reuses it, and `#` starts a comment.

- A setting `name` (a label shown in the interface) is `ci`.

`.github/workflows/ci.yml` lines 3 to 3:

```yaml
on: [push, pull_request]
```

- A setting `on` (the events that start the workflow) is `[push, pull_request]`.

`.github/workflows/ci.yml` lines 5 to 15:

```yaml
jobs:
  check:
    name: Format, lint, types, import rules, unit tests with coverage, dependency audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: make check
      - run: make audit
```

- A setting `jobs` (the jobs to run) starts a group; the more indented lines below belong to it.
- A setting `check` starts a group; the more indented lines below belong to it.
- A setting `name` (a label shown in the interface) is `Format, lint, types, import rules, unit tests with coverage, dependency audit`.
- A setting `runs-on` (the kind of machine) is `ubuntu-latest`.
- A setting `steps` (the steps of the job, in order) starts a group; the more indented lines below belong to it.
- `uses` (runs a packaged action): the action `actions/checkout@v4`; the part after `@` is the version tag.
- `uses` (runs a packaged action): the action `actions/setup-python@v5`; the part after `@` is the version tag.
- A setting `with` (inputs for the action) starts a group; the more indented lines below belong to it.
- A setting `python-version` (the Python version to install) is `"3.12"`.
- `run` (a shell command to run): runs Make with `check`.
- `run` (a shell command to run): runs Make with `audit`.

`.github/workflows/ci.yml` lines 17 to 31:

```yaml
  scenario:
    name: The scenario against real local servers, the evidence pack and its verification
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: make test-e2e
      - run: make run
      - run: make verify
      - uses: actions/upload-artifact@v4
        with:
          name: evidence
          path: evidence/
```

- A setting `scenario` starts a group; the more indented lines below belong to it.
- A setting `name` (a label shown in the interface) is `The scenario against real local servers, the evidence pack and its verification`.
- A setting `runs-on` (the kind of machine) is `ubuntu-latest`.
- A setting `steps` (the steps of the job, in order) starts a group; the more indented lines below belong to it.
- `uses` (runs a packaged action): the action `actions/checkout@v4`; the part after `@` is the version tag.
- `uses` (runs a packaged action): the action `actions/setup-python@v5`; the part after `@` is the version tag.
- A setting `with` (inputs for the action) starts a group; the more indented lines below belong to it.
- A setting `python-version` (the Python version to install) is `"3.12"`.
- `run` (a shell command to run): runs Make with `test-e2e`.
- `run` (a shell command to run): runs Make with `run`.
- `run` (a shell command to run): runs Make with `verify`.
- `uses` (runs a packaged action): the action `actions/upload-artifact@v4`; the part after `@` is the version tag.
- A setting `with` (inputs for the action) starts a group; the more indented lines below belong to it.
- A setting `name` (a label shown in the interface) is `evidence`.
- A setting `path` (the file or folder) is `evidence/`.

`.github/workflows/ci.yml` lines 33 to 38:

```yaml
  image:
    name: The image builds
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t compliance-shrink-pci-scope:ci .
```

- A setting `image` (the image to run) starts a group; the more indented lines below belong to it.
- A setting `name` (a label shown in the interface) is `The image builds`.
- A setting `runs-on` (the kind of machine) is `ubuntu-latest`.
- A setting `steps` (the steps of the job, in order) starts a group; the more indented lines below belong to it.
- `uses` (runs a packaged action): the action `actions/checkout@v4`; the part after `@` is the version tag.
- `run` (a shell command to run): runs Docker with the subcommand `build` with `-t compliance-shrink-pci-scope:ci` (tag (name) the image / tuples only, by program), `.`.

## Try it yourself

```bash
sed -n 1,16p .github/workflows/ci.yml
```
Prints the first job.

```bash
grep -nE "^  [a-z]+:$|uses:|run:" .github/workflows/ci.yml
```
Lists the jobs, actions and commands.

```bash
make check && make audit && make test-e2e && make run > /dev/null && make verify
```
What the first two jobs do after setting up Python (the audit needs network access; `test-e2e` and `run` start local servers on free ports). The last
command prints `OK: ...  0 problem(s)`.

```bash
ls .github/workflows
```
Prints `ci.yml`.

## Mistakes people make

- **Different commands in CI and locally.** The jobs call `make` targets.
- **Unquoted version numbers** like `3.10` in YAML.
- **Forgetting `actions/checkout`**, so later steps see an empty folder.
- **Treating a green CI as proof of the lesson.** It proves the checks run; the README says what each check proves.

## Check yourself

1. How many jobs are there?
   **Answer:** Three: `check`, `scenario` and `image`.
2. What does the `scenario` job upload?
   **Answer:** The `evidence/` folder, as the artifact `evidence`.
3. Why does the `image` job use `docker build` and not `make`?
   **Answer:** It checks the Dockerfile directly on a runner that has Docker.
4. Why are the jobs separate?
   **Answer:** They are independent and run in parallel.
5. What does `make verify` check?
   **Answer:** That every requirement maps to evidence and every file says what it should.

## Further reading

- GitHub Actions documentation: <https://docs.github.com/en/actions>
- Workflow syntax: <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions>
