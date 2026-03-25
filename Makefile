PYTHON := ./.venv312/bin/python
PIP := ./.venv312/bin/pip

.PHONY: setup serve test build-sample

setup:
	python3.12 -m venv .venv312
	$(PIP) install --upgrade pip
	$(PIP) install -e '.[dev]'

serve:
	$(PYTHON) -m app.cli serve

test:
	PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 $(PYTHON) -m pytest tests/test_ingestion.py

build-sample:
	RAG_APP_EMBEDDING_BACKEND=hash $(PYTHON) -m app.cli build-corpus --corpus-name sample-support --input-dir ./data/incoming/sample-support
