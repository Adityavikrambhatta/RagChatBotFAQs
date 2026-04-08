# Podman Deployment Guide

This project ships with a three-container Podman stack:

- `ollama`: hosts the local chat and embedding models
- `backend`: FastAPI + LangChain + Chroma
- `frontend`: React app served by Nginx, with `/api` proxied to the backend

## Supported platforms

- Linux
- Windows with Podman Desktop or Podman Machine
- macOS with Podman Desktop or Podman Machine

Native iOS container execution is not supported. Use Safari or another mobile browser to access the app after it is running on a desktop or server.

## Start the stack

```bash
cd /Users/aditya_vikram_bhattacharya/Documents/TuteDude/RagChatBotFAQs
podman compose up --build -d
```

## Pull the Ollama models

```bash
podman exec ragchatbot-ollama ollama pull llama3.1
podman exec ragchatbot-ollama ollama pull nomic-embed-text
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

Two named volumes are used:

- `ollama-data`: downloaded Ollama models
- `rag-data`: Chroma data, manifests, uploaded files, and chat session history

## Troubleshooting

If chat or ingestion fails on a fresh start, the most common cause is that the Ollama models have not been pulled yet. Pull the models first, then retry the upload or chat request.
