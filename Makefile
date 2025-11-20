SHELL := /bin/bash

# Paths
SRC_DIR := src
DIST_DIR := dist
EXEC_DIR := executable
PORTABLE_DIR := dist-portable

# uv-managed virtualenv in project root
VENV_BIN := .venv/bin
VENVPY := $(VENV_BIN)/python

# Docker
INFRA_DIR := infra
DOCKER_DIR := $(INFRA_DIR)/docker
DOCKERFILE := $(DOCKER_DIR)/Dockerfile
COMPOSE_FILE := $(DOCKER_DIR)/docker-compose.yml
DOCKER_IMAGE ?= bintexttools:latest
# Prefer Docker Compose v2 if available, otherwise fallback to docker-compose
COMPOSE_CMD := $(shell docker compose version >/dev/null 2>&1 && echo "docker compose" || echo "docker-compose")

.PHONY: help init venv init-sync format format-check lint lint-fix test check build clean distclean docker-build compose-up compose-down build-exe clean-exe build-portable clean-portable web web-dev

help:
	@echo "Available targets:"
	@echo "  init           Create uv .venv and install from pyproject (dev and web extras)"
	@echo "  venv           Create uv .venv only (no install)"
	@echo "  init-sync      Create uv .venv and 'uv sync --extra dev --extra web'"
	@echo "  format         Format code with Black"
	@echo "  format-check   Check formatting (no changes)"
	@echo "  lint           Run Ruff linter (check only)"
	@echo "  lint-fix       Run Ruff linter and fix issues"
	@echo "  test           Run pytest tests"
	@echo "  check          Run format-check, lint, and test"
	@echo "  build          Build package (wheel + sdist)"
	@echo "  clean          Remove Python cache/build artifacts"
	@echo "  distclean      Clean plus remove dist/build/egg-info and .venv"
	@echo "  docker-build   Build Docker image ($(DOCKER_IMAGE)) from $(DOCKERFILE)"
	@echo "  compose-up     Start services via $(COMPOSE_CMD) using $(COMPOSE_FILE) (detached)"
	@echo "  compose-down   Stop and remove services via $(COMPOSE_CMD)"
	@echo "  web            Run FastAPI web application (production mode)"
	@echo "  web-dev        Run FastAPI web application (development mode with reload)"
	@echo "  build-exe      Build Python executable using PyInstaller"
	@echo "  clean-exe      Remove executable build artifacts"
	@echo "  build-portable Create portable folder with all packages and app installed"
	@echo "  clean-portable Remove portable build folder"

init: $(VENVPY)
	@echo "Environment ready in .venv"

venv: $(VENVPY)
	@echo "Virtualenv created at .venv"

$(VENVPY):
	uv venv --python 3.14
	uv pip install -e .[dev,web]

init-sync:
	uv venv --python 3.14 --clear && uv sync --extra dev --extra web

format: $(VENVPY)
	$(VENV_BIN)/black $(SRC_DIR) tests $(INFRA_DIR)/web

format-check: $(VENVPY)
	$(VENV_BIN)/black --check --diff $(SRC_DIR) tests $(INFRA_DIR)/web

lint: $(VENVPY)
	$(VENV_BIN)/ruff check $(SRC_DIR) tests $(INFRA_DIR)/web

lint-fix: $(VENVPY)
	$(VENV_BIN)/ruff check --fix $(SRC_DIR) tests $(INFRA_DIR)/web

test: $(VENVPY)
	$(VENV_BIN)/pytest tests -v

check: format-check lint test

build: $(VENVPY)
	$(VENV_BIN)/python -m build

clean:
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type f -name '*.py[co]' -delete
	@find . -type d -name '.mypy_cache' -prune -exec rm -rf {} +
	@find . -type d -name '.pytest_cache' -prune -exec rm -rf {} +
	@find . -type d -name '.ruff_cache' -prune -exec rm -rf {} +

clean-env:
	@rm -rf .venv

distclean: clean clean-env
	@rm -rf build dist *.egg-info

# Docker targets
docker-build:
	docker build -f $(DOCKERFILE) -t $(DOCKER_IMAGE) .

compose-up:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) up -d

compose-down:
	$(COMPOSE_CMD) -f $(COMPOSE_FILE) down

# Web application targets
web: $(VENVPY)
	cd infra/web && PYTHONPATH=../../src:. ../../$(VENV_BIN)/uvicorn app.main:app --host 0.0.0.0 --port 8000

web-dev: $(VENVPY)
	cd infra/web && PYTHONPATH=../../src:. ../../$(VENV_BIN)/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Executable build targets
build-exe: $(VENVPY)
	@echo "Installing PyInstaller..."
	uv pip install pyinstaller
	@echo "Building executables..."
	@echo "Building bin2text executable..."
	uv run pyinstaller \
		--name bin2text \
		--onefile \
		--hidden-import click \
		--hidden-import pydantic_settings \
		--collect-all click \
		--collect-all pydantic_settings \
		$(SRC_DIR)/bintexttools/bin2text.py
	@echo "Building text2bin executable..."
	uv run pyinstaller \
		--name text2bin \
		--onefile \
		--hidden-import click \
		--hidden-import pydantic_settings \
		--collect-all click \
		--collect-all pydantic_settings \
		$(SRC_DIR)/bintexttools/text2bin.py
	@echo "Executables built in $(DIST_DIR)/"
	@echo "Run them with: ./$(DIST_DIR)/bin2text or ./$(DIST_DIR)/text2bin"

clean-exe:
	@rm -rf build
	@rm -rf $(DIST_DIR)/bin2text* $(DIST_DIR)/text2bin*
	@rm -f bin2text.spec text2bin.spec

# Portable build targets
build-portable:
	@echo "Creating portable environment..."
	@rm -rf $(PORTABLE_DIR)
	@mkdir -p $(PORTABLE_DIR)
	@echo "Creating virtual environment..."
	python3.14 -m venv $(PORTABLE_DIR)/.venv
	@echo "Installing dependencies and application..."
	@PORTABLE_ABS=$$(cd $(PORTABLE_DIR) && pwd) && \
	$$PORTABLE_ABS/.venv/bin/pip install --upgrade pip setuptools wheel && \
	$$PORTABLE_ABS/.venv/bin/pip install .
	@echo "Creating run scripts..."
	@echo '#!/bin/bash' > $(PORTABLE_DIR)/bin2text.sh
	@echo 'SCRIPT_DIR="$$(cd "$$(dirname "$${BASH_SOURCE[0]}")" && pwd)"' >> $(PORTABLE_DIR)/bin2text.sh
	@echo 'cd "$$SCRIPT_DIR"' >> $(PORTABLE_DIR)/bin2text.sh
	@echo '.venv/bin/bin2text "$$@"' >> $(PORTABLE_DIR)/bin2text.sh
	@chmod +x $(PORTABLE_DIR)/bin2text.sh
	@echo '#!/bin/bash' > $(PORTABLE_DIR)/text2bin.sh
	@echo 'SCRIPT_DIR="$$(cd "$$(dirname "$${BASH_SOURCE[0]}")" && pwd)"' >> $(PORTABLE_DIR)/text2bin.sh
	@echo 'cd "$$SCRIPT_DIR"' >> $(PORTABLE_DIR)/text2bin.sh
	@echo '.venv/bin/text2bin "$$@"' >> $(PORTABLE_DIR)/text2bin.sh
	@chmod +x $(PORTABLE_DIR)/text2bin.sh
	@echo "Creating README..."
	@echo '# Portable BinTextTools' > $(PORTABLE_DIR)/README.txt
	@echo '' >> $(PORTABLE_DIR)/README.txt
	@echo 'This folder contains a portable installation of bintexttools.' >> $(PORTABLE_DIR)/README.txt
	@echo 'All dependencies are installed in the .venv subdirectory.' >> $(PORTABLE_DIR)/README.txt
	@echo '' >> $(PORTABLE_DIR)/README.txt
	@echo 'To use the tools:' >> $(PORTABLE_DIR)/README.txt
	@echo '  ./bin2text.sh [options]' >> $(PORTABLE_DIR)/README.txt
	@echo '  ./text2bin.sh [options]' >> $(PORTABLE_DIR)/README.txt
	@echo '' >> $(PORTABLE_DIR)/README.txt
	@echo 'Or manually:' >> $(PORTABLE_DIR)/README.txt
	@echo '  .venv/bin/bin2text [options]' >> $(PORTABLE_DIR)/README.txt
	@echo '  .venv/bin/text2bin [options]' >> $(PORTABLE_DIR)/README.txt
	@echo '' >> $(PORTABLE_DIR)/README.txt
	@echo 'To copy to another server:' >> $(PORTABLE_DIR)/README.txt
	@echo '  1. Copy this entire folder to the target server' >> $(PORTABLE_DIR)/README.txt
	@echo '  2. Ensure Python 3.14 is available on the target server' >> $(PORTABLE_DIR)/README.txt
	@echo '  3. Run the tools using the scripts above' >> $(PORTABLE_DIR)/README.txt
	@echo '' >> $(PORTABLE_DIR)/README.txt
	@echo "Portable environment created in $(PORTABLE_DIR)"
	@echo "You can copy this folder to another server and run the tools"

clean-portable:
	@rm -rf $(PORTABLE_DIR)

