# Technology notes: Shrink PCI scope

These notes teach every technology used by `compliance-shrink-pci-scope`, from zero, through this repository's own files: a checkout rebuilt so that card data never reaches the merchant's server, with a local stand-in for a payment provider, a scope calculator, a card-number scanner, a recorded browser session and an evidence pack. Each note says what the technology is, why the repository uses it, where it appears, how it works underneath, walks through the repository's own lines, and ends with commands to try, common mistakes, five questions with answers, and links to the official documentation for the pinned version. Notes that involve Docker say which commands were not run while they were written.

## Reading order

Read the language first, then the build tool, then the runtime pieces, then the tests and the checks.

1. [python.md](python.md): Python: the language the whole program is written in; read this first.
2. [python-standard-library.md](python-standard-library.md): Standard library: `enum`-free value types, `typing`, `collections.abc`, `contextlib`, `types`, `time`, `secrets`, `os`, `sys`, `shutil`, `subprocess`.
3. [python-code-application.md](python-code-application.md): Application layer: 245 lines of Python, every file quoted and explained.
4. [python-code-domain.md](python-code-domain.md): Domain layer: 506 lines of Python, every file quoted and explained.
5. [python-code-infrastructure.md](python-code-infrastructure.md): Infrastructure layer: 381 lines of Python, every file quoted and explained.
6. [python-code-interfaces.md](python-code-interfaces.md): Interfaces layer: 835 lines of Python, every file quoted and explained.
7. [python-tests-application.md](python-tests-application.md): Tests: `application` (157 lines), explained line by line.
8. [python-tests-domain.md](python-tests-domain.md): Tests: `domain` (289 lines), explained line by line.
9. [python-tests-e2e.md](python-tests-e2e.md): Tests: `e2e` (74 lines), explained line by line.
10. [python-tests-infrastructure.md](python-tests-infrastructure.md): Tests: `infrastructure` (189 lines), explained line by line.
11. [python-tests-interfaces.md](python-tests-interfaces.md): Tests: `interfaces` (264 lines), explained line by line.
12. [python-tests-shared.md](python-tests-shared.md): Tests: `shared` (57 lines), explained line by line.
13. [dataclasses.md](dataclasses.md): `dataclasses`: the small frozen value types (`Finding`, `Report`, settings, parsed documents).
14. [re.md](re.md): `re`: the patterns that find headings, labels, numbers and sentences in Markdown text.
15. [argparse.md](argparse.md): `argparse` and exit codes: how `pci-scope` reads its subcommands and reports success.
16. [pathlib.md](pathlib.md): `pathlib`: how the program reads and writes files, and refuses to leave the repository root.
17. [json.md](json.md): JSON: the provider API's bodies, webhook events, the HAR capture, the evidence manifest and the structured logs.
18. [logging.md](logging.md): `logging`: JSON log lines on standard output, and the naive app's deliberately leaky log file.
19. [urllib.md](urllib.md): `urllib`: how the merchant calls the provider, how the provider delivers webhooks, and how the scripted browser makes requests.
20. [threads-and-sockets.md](threads-and-sockets.md): `threading` and `socket`: how the end-to-end test starts real servers on free ports and stops them cleanly.
21. [hmac-and-hashing.md](hmac-and-hashing.md): Hashing and signing: signed, time-limited webhooks and the evidence manifest's SHA-256.
22. [card-number-scanning.md](card-number-scanning.md): Card-number scanning: the Luhn check, masking, and the scanner that searches logs, the database and backups.
23. [tomllib.md](tomllib.md): `tomllib`: loads `scope/before.toml`, `scope/after.toml` and `controls/requirements.toml` into typed values.
24. [sqlite.md](sqlite.md): SQLite: the merchant's order database in `state/merchant.db`, and how it is dumped as text for the scan.
25. [sql.md](sql.md): SQL: `sql/001_schema.sql` (the order table whose columns reject card numbers), `002_seed.sql`, `003_queries.sql`.
26. [http-and-rest.md](http-and-rest.md): HTTP: methods, status codes, form bodies and bearer keys, as the apps and the scripted browser use them.
27. [flask.md](flask.md): Flask: the web framework behind the merchant, provider and naive apps.
28. [flask-support-libraries.md](flask-support-libraries.md): The packages Flask brings with it; Werkzeug is also used directly (the local server and `run_simple`).
29. [gunicorn.md](gunicorn.md): gunicorn: the production WSGI server in the image; one command that picks the app and the worker count.
30. [content-security-policy.md](content-security-policy.md): CSP: the header on the merchant's page that lets only the merchant and the provider load scripts and frames.
31. [html.md](html.md): HTML: the naive form and the redesigned page, written as Python strings and served by the apps.
32. [javascript.md](javascript.md): JavaScript: the merchant's checkout script and the provider's script that mounts the hosted card frame.
33. [payment-provider-api.md](payment-provider-api.md): The provider model: a payment-intents style API with tokens, hosted fields and signed webhooks (a local stand-in).
34. [har.md](har.md): HAR: the JSON file format of the recorded browser traffic in `evidence/payment.har`.
35. [mermaid.md](mermaid.md): Mermaid: text diagrams of the cardholder data environment, generated into `evidence/scope-*.md`.
36. [docker.md](docker.md): Docker: an image of the three apps, Compose for the provider and the merchant, `.dockerignore`, and the CI image build.
37. [dockerfile.md](dockerfile.md): Dockerfile: the recipe for the single image that runs any of the three apps.
38. [docker-compose.md](docker-compose.md): Docker Compose: `docker-compose.yml`, the provider and the merchant with YAML anchors, a shared hardened base and a volume.
39. [markdown.md](markdown.md): Markdown: README, ARCHITECTURE, decision records, and the generated evidence files (`INDEX.md`, `scope-*.md`).
40. [toml.md](toml.md): TOML: the format of `pyproject.toml`.
41. [bash.md](bash.md): Shell: the small command-line programs (`grep`, `sed`, `sort`, `cp`, `rm`, `touch`, `command -v`) that the Makefile recipes run.
42. [make.md](make.md): Make: `Makefile`, the one place that names every command (`make run`, `make test`, `make lint`).
43. [venv-and-pip.md](venv-and-pip.md): venv and pip: the private `.venv/` folder and the installer that fills it from the lock file.
44. [setuptools.md](setuptools.md): setuptools and `pyproject.toml` packaging: how `src/pci_scope` becomes an installable project with a `pci-scope` command.
45. [hash-pinned-lock-files.md](hash-pinned-lock-files.md): Lock files: `requirements-dev.lock` and `requirements.lock`, the exact packages and file hashes pip installs.
46. [env-files.md](env-files.md): Settings: the provider keys, the webhook secret and the paths, read from the environment (`.env.example` lists them).
47. [pytest.md](pytest.md): pytest: runs the the tests under `tests/`; one integration test per "Done when" line.
48. [pytest-cov.md](pytest-cov.md): Coverage: measures which lines the tests ran; `make test` fails under 95 percent in `domain/` and `application/`.
49. [ruff.md](ruff.md): ruff: the linter and formatter (`ruff check`, `ruff format --check`) with rules chosen in `pyproject.toml`.
50. [mypy.md](mypy.md): mypy: the static type checker, in strict mode, over `src/` and `tests/`.
51. [import-linter.md](import-linter.md): import-linter: enforces the layer rule `interfaces -> infrastructure -> application -> domain` (`lint-imports`).
52. [pip-audit.md](pip-audit.md): pip-audit: checks the pinned packages against vulnerability databases (`make audit`).
53. [editorconfig.md](editorconfig.md): EditorConfig: `.editorconfig`, the editor settings (encoding, line endings, tabs or spaces) shared by everyone.
54. [git.md](git.md): Git: the history of the repository (the commits) and `.gitignore`, the list of files it should not track.
55. [github-actions.md](github-actions.md): GitHub Actions: `.github/workflows/ci.yml`, three jobs: checks, the scenario with its evidence pack, and the image build.
56. [yaml.md](yaml.md): YAML: the file format of `.github/workflows/ci.yml`.

## If you have ten minutes

Read these three, in this order:

- [payment-provider-api.md](payment-provider-api.md): The provider model: a payment-intents style API with tokens, hosted fields and signed webhooks (a local stand-in).
- [card-number-scanning.md](card-number-scanning.md): Card-number scanning: the Luhn check, masking, and the scanner that searches logs, the database and backups.
- [html.md](html.md): HTML: the naive form and the redesigned page, written as Python strings and served by the apps.
