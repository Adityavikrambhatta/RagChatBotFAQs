# Requirements Document

## Project Name

RAG ChatBot FAQs

## Purpose

Build a local-first chatbot that answers support and FAQ questions using a Retrieval-Augmented Generation workflow over:

- error-message CSV files
- Excel spreadsheets containing issue and resolution data
- PDF user manuals
- optional text and Markdown support notes

The system should help users find accurate answers to product issues by grounding every response in the uploaded support corpus.

## Problem Statement

Support teams often rely on scattered spreadsheets, manuals, and tribal knowledge to answer user-reported issues. This creates slow response times, inconsistent answers, and difficulty reusing existing documentation.

The goal of this project is to provide a searchable, grounded, and locally runnable chatbot that:

- understands user questions about product issues
- retrieves relevant evidence from uploaded support files
- returns a concise answer with citations
- can be refreshed whenever new files are provided

## Goals

- Provide grounded answers based only on uploaded support content
- Support repeated corpus creation from new file sets
- Work locally on a developer machine without requiring cloud infrastructure
- Support both technical and non-technical workflows through API and UI
- Preserve traceability back to spreadsheet rows and PDF pages

## Users

### Primary users

- support engineers
- implementation teams
- internal product specialists

### Secondary users

- QA teams
- documentation owners
- operations users investigating repeat issues

## In Scope

- local ingestion of `.csv`, `.xlsx`, `.xls`, `.pdf`, `.txt`, and `.md`
- normalization of spreadsheet rows into error knowledge records
- chunking and indexing of PDF and text content
- creation of named corpora from uploaded files or local folders
- hybrid retrieval using vector similarity and keyword/error-code matching
- grounded chat API
- browser frontend for upload, corpus build, corpus selection, and chat
- optional local LLM generation through Ollama

## Out Of Scope

- multi-user authentication and role management
- enterprise deployment and horizontal scaling
- OCR for scanned PDFs in the first release
- workflow automation beyond corpus build and chat
- analytics dashboards and support ticket integration

## Functional Requirements

### FR-1 File ingestion

The system must accept support files in CSV, Excel, PDF, TXT, and Markdown formats.

### FR-2 Spreadsheet normalization

The system must convert spreadsheet rows into searchable knowledge items with structured metadata where possible, including:

- error code
- error message
- resolution
- sheet name
- row number
- source file name

### FR-3 Manual ingestion

The system must extract text from PDF manuals and split them into retrieval chunks while preserving page-level metadata.

### FR-4 Corpus creation

The system must create a named corpus from a given set of files and store:

- vector embeddings
- chunk metadata
- build manifest

### FR-5 Corpus rebuild

The system must support rebuilding a corpus when the underlying files change.

### FR-6 Upload-based build

The system must allow browser users to upload one or more files and build a corpus without needing to manually place files in server directories.

### FR-7 Local-folder build

The system must support CLI and API-based corpus creation from an existing local folder path.

### FR-8 Chat retrieval

The system must accept a user question and retrieve relevant chunks from the selected corpus.

### FR-9 Hybrid ranking

The system must combine semantic retrieval with keyword and error-code matching to improve relevance for support scenarios.

### FR-10 Grounded answers

The system must generate or synthesize answers only from retrieved content and avoid unsupported claims.

### FR-11 Citations

The system must return citations with each answer, including source file and available location metadata such as page, sheet, or row.

### FR-12 Multiple corpora

The system must support more than one corpus and allow the user to choose which corpus to query.

### FR-13 Health and status visibility

The system must expose health information and show the current backend mode in the UI.

## Non-Functional Requirements

### NFR-1 Local-first operation

The solution should run on a local development machine with persistent local storage.

### NFR-2 Explainability

Every answer should be traceable to retrieved evidence.

### NFR-3 Maintainability

The codebase should be modular, with clear separation between ingestion, retrieval, generation, API, and UI layers.

### NFR-4 Extensibility

The solution should allow future additions such as OCR, new file types, evaluation tooling, and production deployment paths.

### NFR-5 Responsiveness

The UI should remain usable on desktop and mobile widths.

### NFR-6 Safe fallback behavior

If no local LLM is configured, the system should still produce evidence-based extractive answers.

## Data Requirements

Each indexed chunk should preserve enough metadata for answer traceability. The preferred metadata model includes:

- `source_file`
- `source_path`
- `source_type`
- `sheet_name`
- `row_number`
- `page_number`
- `error_code`
- `error_message`
- `resolution`

## API Requirements

The system must expose endpoints for:

- health check
- corpus listing
- corpus build from path
- corpus build from uploaded files
- chat query

## UI Requirements

The frontend must provide:

- a form to upload files
- a corpus naming field
- controls for rebuild behavior
- a list of existing corpora
- a chat interface
- a citations panel
- recent question history

## Assumptions

- most spreadsheet files contain semi-structured support data rather than completely arbitrary tables
- PDF files are primarily text-based and not scanned images
- a local machine has enough resources to run embeddings and optionally a local LLM
- users want corpus-level separation, such as one corpus per product or support domain

## Constraints

- the application should remain usable without paid external services
- the first version should prefer simple local persistence rather than distributed services
- the first version should avoid overcomplicated orchestration or agent behavior

## Success Criteria

- a user can upload CSV, Excel, and PDF files from the frontend and build a corpus
- the corpus can be queried through the UI and API
- questions containing exact error codes return the relevant support record
- questions phrased more generally can still retrieve relevant troubleshooting content
- answers include citations to the originating files
- the system runs locally with documented setup steps

## Acceptance Criteria

### AC-1 Corpus build

Given a valid set of support files, when the user builds a corpus, then the system stores indexed chunks and returns build statistics.

### AC-2 Spreadsheet answer

Given a spreadsheet row with an error code and resolution, when the user asks about that error, then the system returns an answer grounded in that row.

### AC-3 Manual answer

Given a PDF manual containing troubleshooting text, when the user asks a related question, then the system can cite the relevant manual passage.

### AC-4 Frontend workflow

Given a running backend and frontend, when a user uploads files and asks a question, then they can complete the workflow without using the CLI.

### AC-5 Fallback generation

Given no configured local chat model, when a user asks a question, then the system still returns an extractive grounded answer.

## Current Implementation Mapping

The current codebase already covers the core first-release requirements:

- ingestion and normalization in [ingestion.py](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/app/ingestion.py)
- corpus management in [service.py](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/app/service.py)
- API endpoints in [main.py](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/app/main.py)
- frontend workflow in [App.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/App.jsx)

## Future Enhancements

- configurable spreadsheet column mapping per corpus
- OCR support for scanned manuals
- automated retrieval evaluation suite
- authentication and hosted deployment path
- exportable answer audit logs
