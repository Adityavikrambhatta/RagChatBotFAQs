# Detailed Project Plan

## Goal

Build a local-first chatbot that answers support and FAQ questions using:

- error-message CSV files
- Excel spreadsheets with troubleshooting data
- PDF user manuals

The chatbot must answer only from indexed evidence and expose a repeatable way to rebuild the RAG corpus whenever new files are dropped in.

## Scope

### In scope

- local ingestion of CSV, XLSX, XLS, PDF, TXT, and Markdown files
- corpus build command for new file drops
- Chroma-based local vector storage
- hybrid retrieval for exact error codes, fuzzy message matches, and semantic matches
- chat API for grounded answers with citations
- optional fully local generation with Ollama

### Out of scope for the first milestone

- authentication and user accounts
- background workers and async job queues
- production deployment
- advanced OCR for scanned PDFs
- agent workflows and tool-calling

## Proposed architecture

### 1. Ingestion and normalization

Each file type is normalized into chunk records with rich metadata.

#### Tabular files

Each row is transformed into a single knowledge item:

- `error_code`
- `error_message`
- `resolution`
- `sheet_name`
- `row_number`
- `source_file`

This is especially useful because most user questions will be close to one of:

- an exact error code
- a near-exact user-visible error string
- a “how do I fix this” question

#### PDF manuals

PDFs are parsed page by page and chunked into passages. Metadata includes:

- `source_file`
- `page_number`
- `source_type=pdf_page`

### 2. Corpus builder

The builder is the repeatable mechanism that turns a folder of raw files into a named corpus.

Input:

- corpus name
- local directory path
- optional force rebuild flag

Output:

- Chroma collection
- manifest file with file hashes and build stats

Behavior:

- if file hashes did not change and the collection exists, skip the rebuild
- if any file changed, rebuild the corpus cleanly

### 3. Retrieval

The system combines two retrieval strategies.

#### Vector retrieval

- semantic embedding search over chunks
- captures paraphrased and intent-based user questions

#### Keyword retrieval

- exact/near-exact matching for error strings
- boosted matching for error codes
- fuzzy matching for spreadsheet rows and short troubleshooting phrases

The final ranking is a weighted merge of both strategies.

### 4. Answer generation

Two supported modes:

#### Preferred mode

- Ollama local model generates the final answer from retrieved context

#### Fallback mode

- extractive answer synthesis from the top hits

Either way, the answer should:

- stay grounded in the retrieved context
- mention likely cause if available
- provide recommended resolution if available
- include source citations

## Build phases

## Phase 1: Core ingestion and indexing

Deliverables:

- project scaffold
- config and local data directories
- CSV/XLSX/PDF ingestion
- Chroma storage
- manifest-based corpus builds

Success criteria:

- user can point the app to a local folder and build a corpus
- the build output reports indexed file and chunk counts

## Phase 2: Retrieval and grounded answers

Deliverables:

- hybrid retriever
- local chat API
- answer formatting with citations

Success criteria:

- questions using an error code return the relevant spreadsheet row
- troubleshooting questions can also pull from the manual

## Phase 3: Quality tuning

Deliverables:

- retrieval test set from real support tickets
- improved column heuristics
- tuned chunk sizes and top-k defaults

Success criteria:

- top result is correct for the majority of benchmarked questions
- answers avoid unsupported claims

## Phase 4: UX improvements

Deliverables:

- simple web UI or Streamlit chat
- upload flow
- corpus selector
- build progress feedback

Success criteria:

- non-technical users can refresh a corpus and ask questions without touching the CLI

## Phase 5: Production hardening

Deliverables:

- structured logging
- larger test coverage
- containerization
- incremental indexing
- OCR support for scanned manuals

## Recommended local workflow

1. Create a folder per corpus under `data/incoming/`.
2. Copy all raw support files into that folder.
3. Run `build-corpus`.
4. Start the API.
5. Ask questions against that corpus.
6. Re-run `build-corpus` when files change.

## Example directory layout

```text
data/
  incoming/
    product-support/
      errors.csv
      known_issues.xlsx
      user_manual.pdf
  corpora/
    product-support/
      manifest.json
  chroma/
```

## Risks and mitigations

### Risk: messy spreadsheet schemas

Mitigation:

- normalize by heuristics first
- later add per-corpus field mapping config if needed

### Risk: poor PDF text extraction

Mitigation:

- start with `pypdf`
- upgrade to `PyMuPDF` or OCR only if real manuals require it

### Risk: semantic retrieval misses exact error codes

Mitigation:

- preserve `error_code`
- explicit keyword boost in ranking

### Risk: hallucinated answers

Mitigation:

- strict grounding prompt
- fallback extractive mode when no chat model is configured

## Immediate next tasks

1. Add a simple browser chat UI.
2. Add PDF fixtures and retrieval tests.
3. Add file-upload based corpus build from the UI.
4. Add field mapping config for unusual Excel layouts.
