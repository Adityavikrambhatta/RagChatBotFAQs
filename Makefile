PYTHON ?= python3

.PHONY: backend frontend build-corpus

backend:
	$(PYTHON) -m app.cli serve --reload

frontend:
	cd frontend && npm run dev

build-corpus:
	$(PYTHON) -m app.cli build-corpus --corpus-name document-qa --input-dir ./data/sample_docs
