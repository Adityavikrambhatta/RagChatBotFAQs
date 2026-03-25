# RAG ChatBot FAQs

Local-first RAG chatbot for support FAQs, spreadsheet-based error catalogs, and PDF user manuals.

## What this project does

- Ingests `.csv`, `.xlsx`, `.xls`, `.pdf`, `.txt`, and `.md`
- Converts spreadsheet rows into FAQ/error knowledge records
- Chunks PDF/manual content and stores everything in a local Chroma vector database
- Uses hybrid retrieval:
  - semantic vector search
  - keyword and error-code matching
- Answers user questions through a FastAPI API
- Includes a React/Vite frontend for corpus upload, build, and chat
- Can run fully local with Ollama for generation, or fall back to extractive answers if no chat model is configured

## Architecture

1. Source ingestion
   - CSV and Excel rows become structured error records
   - PDF pages are extracted and chunked
2. Corpus build
   - A named corpus is built from a local folder
   - File hashes are stored in a manifest
   - If the same files are provided again, the build can be skipped
3. Retrieval
   - Hybrid merge of vector similarity and fuzzy keyword matching
   - Error codes receive a high retrieval boost
4. Answering
   - Ollama-backed local generation if configured
   - Fallback extractive answer when no local LLM is configured

## Detailed delivery plan

The full execution plan is documented in [docs/project-plan.md](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/docs/project-plan.md).

### Phase 1: Foundation

- Create a clean Python project with FastAPI, Chroma, pandas, and PDF parsing
- Define a local data layout:
  - `data/incoming/`
  - `data/corpora/`
  - `data/chroma/`
- Build a corpus CLI so new file drops can be converted into a fresh RAG index

### Phase 2: Knowledge normalization

- Map spreadsheet rows into a common schema:
  - `error_code`
  - `error_message`
  - `module`
  - `category`
  - `cause`
  - `resolution`
  - `sheet_name`
  - `row_number`
- Preserve source metadata so answers can cite the exact file, sheet, row, or page
- Add file-hash manifests so the system knows when a rebuild is necessary

### Phase 3: Retrieval quality

- Combine semantic retrieval with direct error-code and fuzzy message matching
- Tune chunk size for manuals and long troubleshooting guides
- Add evaluation examples from real support tickets
- Improve ranking rules for:
  - exact error code
  - near-identical error message
  - troubleshooting steps in the PDF manual

### Phase 4: Chat experience

- Expose API endpoints for:
  - corpus build
  - corpus listing
  - chat
- Add a UI in the next iteration if needed
- Return grounded answers with citations only

### Phase 5: Hardening

- Add tests for file normalization and retrieval
- Add logging and ingestion summaries
- Support multiple corpora for different products or modules
- Add incremental refresh and background jobs if corpus size grows

## Local setup

```bash
cd /Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
cp .env.example .env
```

## Build a corpus

Put your files in a folder like:

```text
data/incoming/product-support/
  errors.csv
  troubleshooting.xlsx
  user_manual.pdf
```

Then run:

```bash
python -m app.cli build-corpus \
  --corpus-name product-support \
  --input-dir ./data/incoming/product-support
```

## Start the API

```bash
python -m app.cli serve
```

Open Swagger UI at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Start the frontend

The frontend defaults to talking to the backend at `http://127.0.0.1:8010`.

```bash
cd /Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend
npm install
npm run dev
```

Open the app at [http://127.0.0.1:5173](http://127.0.0.1:5173)

If your API runs on a different port, start the frontend with:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000 npm run dev
```

## Optional: run with Ollama locally

If you want local generation and optionally local embeddings:

1. Install Ollama
2. Pull models, for example:

```bash
ollama pull llama3.1
ollama pull nomic-embed-text
```

3. Update `.env`:

```bash
RAG_APP_OLLAMA_CHAT_MODEL=llama3.1
RAG_APP_EMBEDDING_BACKEND=ollama
RAG_APP_OLLAMA_EMBED_MODEL=nomic-embed-text
```

The Ollama embeddings API supports local embedding generation over HTTP: [docs](https://docs.ollama.com/api/embed)

## API endpoints

- `GET /api/health`
- `GET /api/corpora`
- `POST /api/corpora/build`
- `POST /api/corpora/upload-build`
- `POST /api/chat`

## Example chat request

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "corpus_name": "product-support",
    "question": "How do I fix ERR-101 login failed?"
  }'
```

## Notes

- Chroma local persistence is a good fit for embedded/local workflows: [docs](https://cookbook.chromadb.dev/core/clients/)
- FastAPI file and JSON request handling docs: [FastAPI](https://fastapi.tiangolo.com/tutorial/request-files/)
- Pandas remains the simplest path for CSV/XLSX ingestion: [pandas](https://pandas.pydata.org/docs/)
