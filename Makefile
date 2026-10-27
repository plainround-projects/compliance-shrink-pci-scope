# make up | run | test | lint | audit | check | down   (make help lists all)
PYTHON ?= $(shell command -v python3.13 || command -v python3.12 || command -v python3)
VENV := .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
CLI := $(VENV)/bin/pci-scope

-include .env
export

.PHONY: help install env up db run verify scope scan queries serve-provider serve-merchant serve-naive docker-build test \
        test-e2e lint format audit check down clean

help: ## list the targets
	@grep -hE '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | sed -E 's/:.*## /\t/' | sort

$(STAMP): requirements-dev.lock pyproject.toml
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install -q --require-hashes -r requirements-dev.lock
	$(VENV)/bin/pip install -q --no-deps -e .
	touch $@

install: $(STAMP) ## create .venv from the hash-pinned lock file

env:
	@[ -f .env ] || { cp .env.example .env; echo "created .env from .env.example"; }

up: env $(STAMP) ## prepare the environment (there are no services to start)

db: $(STAMP) ## create the merchant's order table with sql/001_schema.sql and the sample rows of sql/002_seed.sql
	$(CLI) db

run: up ## the lesson's scenario: naive checkout, redesign, proof, scope, evidence pack, verification
	$(CLI) demo

verify: $(STAMP) ## check that every requirement maps to evidence and every file says what it should
	$(CLI) verify

scope: $(STAMP) ## print the cardholder data environment before and after, and what changed
	$(CLI) scope

scan: $(STAMP) ## search a folder for card numbers: make scan PATHS="state evidence"
	$(CLI) scan $(PATHS)

queries: db ## run sql/003_queries.sql against the sample database
	sqlite3 $(DATABASE_PATH) < sql/003_queries.sql

serve-provider: $(STAMP) ## run the local payment provider on its port
	$(CLI) serve provider

serve-merchant: $(STAMP) ## run the redesigned merchant on its port
	$(CLI) serve merchant

serve-naive: $(STAMP) ## run the naive checkout (to be measured, test card only)
	$(CLI) serve naive

docker-build: ## build the image of the three apps
	docker build -t compliance-shrink-pci-scope:dev .

test: $(STAMP) ## unit tests with coverage (domain and application must stay at 95% or more)
	$(PY) -m pytest tests/unit --cov=pci_scope --cov-report=term
	$(PY) -m coverage report --include='src/pci_scope/domain/*,src/pci_scope/application/*' --fail-under=95

test-e2e: $(STAMP) ## the scenario against real local servers (provider, merchant, naive)
	$(PY) -m pytest tests/e2e -m e2e

lint: $(STAMP) ## ruff check, ruff format check, mypy, import-linter
	$(VENV)/bin/ruff check .
	$(VENV)/bin/ruff format --check .
	$(VENV)/bin/mypy
	$(VENV)/bin/lint-imports

format: $(STAMP) ## apply ruff's formatting and safe fixes
	$(VENV)/bin/ruff check --fix .
	$(VENV)/bin/ruff format .

audit: $(STAMP) ## check the locked dependencies for known vulnerabilities
	$(VENV)/bin/pip-audit --no-deps --disable-pip -r requirements-dev.lock

check: lint test ## everything CI runs apart from the audit

down: ## remove generated output (nothing is running)
	rm -rf build

clean: down
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .coverage htmlcov
