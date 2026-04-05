# RagChatBotFAQs

LangChain-based conversational RAG chatbot with a React UI for both admins and end users.

For a full study guide to the architecture, flows, tradeoffs, and debugging lessons in this codebase, read [docs/project-literature.md](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/docs/project-literature.md).

## What this repo delivers

- Answers questions from PDF and text documents
- Uses `PyPDFLoader` and `TextLoader`
- Splits large documents with `RecursiveCharacterTextSplitter`
- Stores embeddings in Chroma
- Uses a `ChatPromptTemplate` with `MessagesPlaceholder`
- Handles context-aware follow-up questions
- Grounds answers in retrieved context and returns `I don't know.` when the context is insufficient
- Includes:
  - an admin workspace to ingest documents and inspect chunks
  - a user workspace for chat-only interaction

## Architecture

```text
Documents -> LangChain loaders -> Recursive splitter -> Embeddings -> Chroma
User question + chat history -> history-aware retriever -> RAG prompt -> LLM -> grounded answer
```

## Recommended repo structure

```text
app/
  main.py
  service.py
  langchain_rag.py
  history.py
frontend/
  src/
data/
  sample_docs/
docs/
tests/
```

## Core design choices

1. Safe conversational RAG
- The answer prompt explicitly limits the model to retrieved context.
- If the retrieved context does not support the answer, the assistant replies with `I don't know.`
- Follow-up queries are handled with a history-aware retriever.

2. Scalable structure
- Corpus ingestion, retrieval, and chat history are separated into dedicated modules.
- Chunk metadata and corpus manifests are persisted for admin inspection.
- Session history is stored per session so the UI can resume conversations.

3. UI separation
- `#/admin` is for ingestion, monitoring, and chunk inspection.
- `#/chat` is for the end-user chat experience.

## Backend setup

```bash
cd /Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .[dev]
cp .env.example .env
```

### OpenAI option

Set in `.env`:

```bash
RAG_APP_LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
RAG_APP_OPENAI_MODEL=gpt-4.1-mini
RAG_APP_EMBEDDING_PROVIDER=openai
RAG_APP_EMBEDDING_MODEL=text-embedding-3-small
```

### Ollama option

Set in `.env`:

```bash
RAG_APP_LLM_PROVIDER=ollama
RAG_APP_OLLAMA_CHAT_MODEL=llama3.1
RAG_APP_EMBEDDING_PROVIDER=ollama
RAG_APP_OLLAMA_EMBED_MODEL=nomic-embed-text
```

### Default starter path

The repo is currently configured for OpenAI chat plus OpenAI embeddings.

## Pricing estimates

The current repo configuration uses:

- Chat model: `gpt-4.1-mini`
- Embedding model: `text-embedding-3-small`

Estimated OpenAI API cost:

- `gpt-4.1-mini` input tokens: about `$0.004` per `10,000` tokens
- `gpt-4.1-mini` output tokens: about `$0.016` per `10,000` tokens
- `gpt-4.1-mini` cached input tokens: about `$0.001` per `10,000` tokens
- `text-embedding-3-small`: about `$0.0002` per `10,000` tokens

Example estimates:

- `10,000` chat input tokens + `2,000` chat output tokens is about `$0.0072`
- `10,000` embedded tokens is about `$0.0002`

These are pricing estimates based on OpenAI's pricing page and can change over time, so verify before budgeting.

## Run the backend

```bash
python -m app.cli serve --reload
```

Swagger: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## Run the frontend

```bash
cd /Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/frontend
npm install
npm run dev
```

Frontend: [http://127.0.0.1:5173](http://127.0.0.1:5173)

## Sample ingestion flow

Build the bundled sample corpus:

```bash
python -m app.cli build-corpus \
  --corpus-name document-qa \
  --input-dir ./data/sample_docs
```

Or upload PDFs / `.txt` / `.text` / `.md` files from the admin page.

## API endpoints

- `GET /api/health`
- `GET /api/corpora`
- `POST /api/corpora/build`
- `POST /api/corpora/upload-build`
- `GET /api/admin/overview`
- `GET /api/admin/documents`
- `GET /api/admin/chunks`
- `GET /api/admin/sessions`
- `POST /api/admin/retrieve-preview`
- `POST /api/chat`
- `GET /api/chat/{session_id}/history`

## Prompting behavior

The backend uses:

- a system prompt for standalone-question rewriting
- a `MessagesPlaceholder` for prior conversation
- a grounded answer prompt that sees retrieved context only

That means follow-ups like:

- `Explain more`
- `What about the previous point?`
- `Summarize the second recommendation`

can be resolved against previous turns before retrieval happens.

## GitHub checklist

- Push this repo to `main`
- Add screenshots of `#/admin` and `#/chat`
- Add your `.env.example`
- Keep sample docs in `data/sample_docs`
- Add a short demo video or GIF if you want your repo to stand out
