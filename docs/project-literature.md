# Project Literature

## Purpose

This project is a document-grounded conversational RAG assistant. It lets a user upload PDF or text documents, chunk and embed them, store them in a vector database, and then ask questions through a chat interface that remembers earlier turns.

The design goal is not just "question answering." The deeper goal is:

- grounded answers instead of free-form guessing
- support for follow-up questions
- visibility into what was indexed
- a simple admin interface for monitoring the knowledge base

## What Problem It Solves

A plain LLM chat app forgets your documents unless you paste them into every prompt. A basic retrieval app can answer one question, but often fails on follow-ups like:

- `Explain more`
- `What about the previous point?`
- `Summarize that section again`

This project solves that by combining:

- document ingestion
- chunk-based retrieval
- vector similarity search
- conversation history
- a prompt that forces document-grounded answers

## Big Picture Architecture

```text
PDF / text files
  -> LangChain loaders
  -> recursive chunking
  -> embeddings
  -> Chroma vector store
  -> retriever
  -> prompt with chat history
  -> LLM answer
  -> source-backed response in UI
```

The system has two major surfaces:

- Backend: FastAPI app that handles ingestion, indexing, retrieval, and chat
- Frontend: React app with an admin monitor and a user chat page

## Repository Tour

### Backend

- [config.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/config.py)
  - environment variables
  - storage paths
  - chunk settings
  - model configuration

- [langchain_rag.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/langchain_rag.py)
  - document loaders
  - chunking logic
  - embedding provider setup
  - vector store creation
  - conversational RAG chain assembly

- [service.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/service.py)
  - main application service
  - upload handling
  - corpus build flow
  - corpus detail reads
  - retrieval preview
  - chat flow

- [history.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/history.py)
  - file-backed chat history
  - session persistence

- [main.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/main.py)
  - FastAPI routes
  - CORS
  - error handling

- [schemas.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/schemas.py)
  - request and response models

### Frontend

- [App.jsx](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/frontend/src/App.jsx)
  - routing between admin and chat
  - upload form
  - admin data fetches
  - chat interactions

- [styles.css](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/frontend/src/styles.css)
  - layout
  - cards
  - panels
  - current visual styling

### Data layout

- `data/incoming/`
  - raw uploaded documents by corpus

- `data/corpora/`
  - manifest and admin-friendly metadata

- `data/chroma/`
  - vector index storage

- `data/sessions/`
  - chat session history

## Backend Flow In Detail

## 1. Upload and ingestion

The admin page sends a multipart request to:

- `POST /api/corpora/upload-build`

The route reads each uploaded file into memory and then calls the service layer in a threadpool. The threadpool matters because corpus building is slow and synchronous:

- file write
- PDF parse
- chunk generation
- embeddings
- vector insertion

Without the threadpool, this long-running task would block the async request loop.

## 2. Documents are loaded

Document loading happens in [langchain_rag.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/langchain_rag.py).

Supported formats:

- `.pdf`
- `.txt`
- `.text`
- `.md`

Loaders used:

- `PyPDFLoader` for PDFs
- `TextLoader` for text documents

Each loaded document is normalized with metadata such as:

- source path
- source file name
- source type
- page number if present

This metadata is important because it later appears in:

- chunk previews
- source citations
- admin inspection panels

## 3. Text is split into chunks

Chunking uses `RecursiveCharacterTextSplitter`.

Current defaults:

- `chunk_size = 1000`
- `chunk_overlap = 200`

Why overlap exists:

- it keeps nearby context together
- it reduces answer quality loss at section boundaries

Each chunk is assigned a `chunk_id`, which becomes useful for:

- admin inspection
- debugging retrieval results
- source display in the UI

## 4. Embeddings are generated

Embedding provider selection happens in [langchain_rag.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/langchain_rag.py).

The project supports:

- OpenAI
- Ollama
- Hugging Face
- local demo hashing

Your current primary path has been:

- OpenAI embeddings: `text-embedding-3-small`

This means chunk text is sent to OpenAI, converted into vectors, and then stored in Chroma.

## 5. Vector store is built

The vector database used is Chroma.

What Chroma stores:

- the chunk text
- embeddings
- chunk metadata

Important note:

The corpus build is only "real" once Chroma has accepted the chunk vectors. If the upload succeeds but no vectors are stored, you do not have a usable RAG corpus.

## 6. Admin metadata is written

The app writes a lightweight admin-facing record in `data/corpora/<corpus_name>/`.

Files created:

- `manifest.json`
- `documents.json`
- `chunks.json`

These files make it possible for the admin UI to display:

- uploaded file summaries
- loaded document counts
- chunk counts
- sample text previews

without querying the vector database directly for every panel.

## Chat Flow In Detail

## 1. User asks a question

The chat UI sends:

- `POST /api/chat`

with:

- question
- corpus name
- session id

## 2. Session history is loaded

The app reads prior chat turns from [history.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/history.py).

This gives the system memory of:

- earlier user questions
- earlier assistant answers

That is what enables follow-up questions.

## 3. History-aware retrieval chain is built

The project uses a conversational RAG chain built from:

- a contextualization prompt
- a retriever
- a grounded answer prompt

The contextualization prompt rewrites ambiguous follow-up questions into standalone queries before retrieval.

Example:

- user asks: `Explain more about the previous point`
- system rewrites it based on prior chat history
- retriever searches using the rewritten meaning

This is the core difference between a plain retriever and a conversational retriever.

## 4. Retrieved chunks are stuffed into the prompt

The answer prompt uses:

- a system instruction
- `MessagesPlaceholder("chat_history")`
- the current user input
- retrieved context

Its central rule is:

- answer only from the retrieved context
- say `I don't know.` if the answer is not supported

That is how the project tries to reduce hallucination.

## 5. Response and sources are returned

The backend returns:

- answer text
- source chunks
- updated chat history
- session id

The frontend then renders:

- the answer in the chat window
- the source snippets in a grounding panel

## Admin UI Behavior

The admin page is meant to answer five questions:

1. What corpus am I working with?
2. What files were ingested?
3. How many documents/pages were loaded?
4. How many chunks were created?
5. What chunks would be retrieved for a sample query?

That is why the admin page includes:

- corpus list
- latest build summary
- document previews
- chunk explorer
- retrieval preview
- session list

## User UI Behavior

The user page is intentionally simpler.

It focuses on:

- selecting a corpus
- tracking a session
- asking questions
- seeing grounded sources

The user page is chat-first. The admin page is inspection-first.

## Why The Project Felt Tricky During Debugging

Several issues in this project can look like "RAG not working" even when different layers are failing for different reasons.

### 1. Successful upload does not always mean successful indexing

The file may be saved to disk, but:

- parsing might fail
- embedding might fail
- Chroma insertion might fail

The upload request only truly succeeds when the vector store step completes.

### 2. UI state can look stale even when backend files are correct

The corpus may exist in:

- `data/corpora/...`
- `data/chroma/...`

but the frontend can still look empty if:

- it is using stale local state
- it failed to fetch backend details
- CORS blocked the request
- the wrong frontend port is open

### 3. Reusing the same corpus name hides "new RAG" creation

If you always upload into `document-qa`, the UI does not create a new row every time. It updates the same corpus.

So "nothing new appeared" can really mean:

- the same corpus was rebuilt in place

### 4. Chroma telemetry warnings are noisy but often unrelated

Warnings like:

- `Failed to send telemetry event ClientStartEvent...`

look scary, but they are often not the root problem. The real issue may be:

- env config
- OpenAI client config
- response model bugs
- frontend fetch failures

## Key Configuration Ideas

The project depends heavily on `.env`.

Important settings:

- `RAG_APP_EMBEDDING_PROVIDER`
- `RAG_APP_EMBEDDING_MODEL`
- `RAG_APP_LLM_PROVIDER`
- `RAG_APP_OPENAI_MODEL`
- `OPENAI_API_KEY`
- `RAG_APP_CHUNK_SIZE`
- `RAG_APP_CHUNK_OVERLAP`

One subtle but important lesson from debugging:

- blank env values can still be read as strings
- an empty `RAG_APP_OPENAI_BASE_URL` can break the OpenAI client

So configuration parsing matters almost as much as model selection.

## Important Current Design Limits

This project is functional, but not yet fully production-grade.

### 1. No WebSockets

There is no real-time backend push channel.

The project uses:

- plain HTTP requests

So long uploads/indexing jobs feel static unless the UI adds enough status text.

### 2. No background job system

Ingestion happens inside the request lifecycle.

That means:

- the request can take a long time
- large PDFs feel slow
- there is no true progress percentage

### 3. Local persistence only

Chroma and metadata are stored locally in the repo data directory. That is good for local development, but not yet a distributed production setup.

### 4. Session history is file-based

Chat memory is saved as JSON files, which is easy to understand and debug, but not ideal for multi-user scaling.

## How To Study This Project Effectively

A good reading order is:

1. [README.md](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/README.md)
2. [config.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/config.py)
3. [schemas.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/schemas.py)
4. [langchain_rag.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/langchain_rag.py)
5. [service.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/service.py)
6. [main.py](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/app/main.py)
7. [App.jsx](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/frontend/src/App.jsx)

Why this order works:

- config tells you what the app expects
- schemas tell you what it moves around
- LangChain code tells you how RAG is built
- service ties the use cases together
- FastAPI shows the external surface
- React shows the human-facing behavior

## Good Questions To Ask While Reading

- Where exactly does a PDF page become a chunk?
- Where does a chunk become an embedding?
- Where are embeddings persisted?
- Where does chat history enter retrieval?
- Where does the app enforce "I don't know" behavior?
- What part of the system is local vs remote?
- Which failures are backend failures and which are UI reflection failures?

## Suggested Future Improvements

If this project continues, the highest-value next steps are:

- add background ingestion jobs
- add real progress states
- add SSE or WebSocket streaming for chat/build feedback
- add stronger admin diagnostics
- add explicit "updated existing corpus" messaging
- add evaluation scripts for retrieval quality
- add a database-backed session store
- support multiple named corpora more explicitly in the UI

## Final Mental Model

This is best understood as four connected systems:

1. Ingestion system
   - load files
   - chunk text
   - embed and store

2. Retrieval system
   - search vector store
   - retrieve supporting chunks

3. Conversational system
   - carry history
   - rewrite follow-ups
   - answer grounded in context

4. Admin visibility system
   - expose corpus stats
   - show document/chunk previews
   - make indexing state understandable

When the app feels broken, one of those four systems is usually the real failing layer.
