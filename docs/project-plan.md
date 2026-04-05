# Project Plan

## Goal

Build a safe, grounded, conversational Document Q&A Assistant using LangChain and a React UI.

## Milestones

1. Repository setup
- Backend and frontend skeleton
- Environment variables
- Sample documents

2. Document ingestion
- Load PDFs with `PyPDFLoader`
- Load text files with `TextLoader`
- Show document count and sample content

3. Chunking and indexing
- Use `RecursiveCharacterTextSplitter`
- Configure `chunk_size` and `chunk_overlap`
- Persist embeddings in Chroma

4. Conversational RAG
- Add `ChatPromptTemplate`
- Add `MessagesPlaceholder`
- Add history-aware retriever for follow-up questions
- Enforce grounded responses with `I don't know.`

5. UI
- Admin page for ingestion and monitoring
- User page for chat

6. Hardening
- Validate uploads
- Persist session history
- Add tests and screenshots
