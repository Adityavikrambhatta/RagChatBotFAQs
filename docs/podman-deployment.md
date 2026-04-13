# Podman Deployment Guide

This project ships with a two-container Podman stack:

- `backend`: FastAPI + LangChain + Chroma + OpenAI API access
- `frontend`: React app served by Nginx, with `/api` proxied to the backend

## Supported platforms

- Linux
- Windows with Podman Desktop or Podman Machine
- macOS with Podman Desktop or Podman Machine

Native iOS container execution is not supported. Use Safari or another mobile browser to access the app after it is running on a desktop or server.

## Before you start

Set your OpenAI credentials in [.env](/Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs/.env):

```bash
OPENAI_API_KEY=your_key_here
RAG_APP_LLM_PROVIDER=openai
RAG_APP_OPENAI_MODEL=gpt-4.1-mini
RAG_APP_EMBEDDING_PROVIDER=openai
RAG_APP_EMBEDDING_MODEL=text-embedding-3-small
```

## Start the stack

```bash
cd /Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs
podman compose up --build -d
```

## Open the app

- UI: `http://localhost:8080`
- Backend Swagger: `http://localhost:8000/docs`
- Proxied Swagger: `http://localhost:8080/docs`

## Stop the stack

```bash
podman compose down
```

## Persisted data

One named volume is used:

- `rag-data`: Chroma data, manifests, uploaded files, and chat session history

## Troubleshooting

If corpus build or chat fails in containers, the most common causes are:

- `OPENAI_API_KEY` is missing or invalid
- outbound internet access is blocked
- the `.env` file was not updated before starting the stack
