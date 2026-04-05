# Requirements Mapping

## Functional requirements

- Answer questions from PDF or text documents: supported
- Remember previous questions: supported through stored session history
- Handle follow-up queries: supported through history-aware retrieval
- Avoid hallucination: prompt requires retrieved-context-only answers and uses `I don't know.`

## Technical requirements

- LangChain: used for loaders, splitter, retriever, prompts, and chain composition
- No fine-tuning: satisfied
- Grounding focus: satisfied
- Conversational flow: satisfied

## UI requirements

- Admin page: ingestion, corpus stats, documents, chunks, retrieval preview, sessions
- User page: chat-only experience with source-backed answers
