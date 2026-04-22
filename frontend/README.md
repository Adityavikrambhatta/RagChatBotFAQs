# Frontend README

This frontend can feel complex at first because it supports two different modes in one app:

- `#/chat`: the user-facing chat experience
- `#/admin`: the admin/monitoring and corpus-ingestion experience

The goal of this document is to explain the code in plain language so you know where to look first.

## Big Picture

The frontend is a React app built with Vite.

At a high level, the app is split into:

1. `App.jsx`
   This is the composition layer. It does not contain the business logic anymore. It just wires together providers and page sections.

2. `stores/`
   These hold the state and actions.

3. `components/`
   These render UI sections and call store actions.

4. `api/` and `utils/`
   These contain helper functions used by stores and components.

## Recommended Reading Order

If the frontend feels overwhelming, read the files in this order:

1. [App.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/App.jsx)
2. [AppStore.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/stores/AppStore.jsx)
3. [CorpusStore.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/stores/CorpusStore.jsx)
4. [ChatStore.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/stores/ChatStore.jsx)
5. the components used by the view you care about

That order gives you:

- layout first
- app state second
- corpus/admin logic third
- chat logic fourth
- visual details last

## What `App.jsx` Does

[App.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/App.jsx) is now mostly a router/composer.

It does three things:

- wraps the app in the three store providers
- decides whether to show the admin view or chat view
- places the main page sections on the screen

So instead of one giant file doing everything, `App.jsx` now acts like an assembly file.

## Store Overview

We are using a custom React Context store pattern, not Redux or Zustand.

### 1. AppStore

File:
[AppStore.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/stores/AppStore.jsx)

Purpose:

- global app-level state
- current route from the URL hash
- app health metadata
- status banner text

Main responsibilities:

- detect `#/chat` vs `#/admin`
- expose `navigate()`
- hold the shared status message shown near the top of the app

Think of this store as:
"small global UI state"

### 2. CorpusStore

File:
[CorpusStore.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/stores/CorpusStore.jsx)

Purpose:

- everything related to corpora and admin ingestion
- available corpora
- selected corpus
- document/chunk preview data
- file upload state
- build progress
- retriever preview

Main responsibilities:

- call `/api/health`
- call `/api/admin/overview`
- load corpus detail/documents/chunks
- upload files and build corpus
- run retriever preview queries

Think of this store as:
"admin data + corpus data"

### 3. ChatStore

File:
[ChatStore.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/stores/ChatStore.jsx)

Purpose:

- everything related to chat sessions
- current question draft
- message history
- active cited sources
- session id
- sending chat messages
- loading old session history

Main responsibilities:

- send a question to `/api/chat`
- load prior history from `/api/chat/:sessionId/history`
- create a new session id

Think of this store as:
"conversation state"

## Why The Stores Are Split This Way

The split was done to separate concerns:

- `AppStore`: route/status
- `CorpusStore`: ingestion/admin/corpus browsing
- `ChatStore`: live conversation logic

Without this split, one file had to manage:

- route changes
- corpus upload
- corpus selection
- chunk preview
- session history
- question composer
- answer rendering
- source rendering

That made changes risky because one edit could affect unrelated behavior.

## Component Overview

All UI sections are in:
[components](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components)

Each component is meant to be a visual slice of the screen.

### Shared / top-level

- [HeroSection.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/HeroSection.jsx)
  Top banner and tab navigation.

### Admin side

- [BuildPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/BuildPanel.jsx)
  Upload files and trigger corpus build.

- [AnswerPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/AnswerPanel.jsx)
  Despite the filename, this component currently exports `BuildSummaryPanel`.
  It shows the latest indexing/build result.

- [CorpusListPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/CorpusListPanel.jsx)
  Lists all corpora and lets the user pick one.

- [DocumentsPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/DocumentsPanel.jsx)
  Shows loaded document previews.

- [ChunksPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/ChunksPanel.jsx)
  Shows chunk previews currently stored in the vector index.

- [PreviewPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/PreviewPanel.jsx)
  Lets you run a retriever preview query.

- [HistoryPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/HistoryPanel.jsx)
  On the admin side this exports `SessionsPanel`, which shows recent conversations.

### Chat side

- [AskPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/AskPanel.jsx)
  On the chat side this exports `UserControlsPanel`, which manages corpus/session controls.

- [TranscriptPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/TranscriptPanel.jsx)
  Displays the conversation and send form.

- [CitationsPanel.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/CitationsPanel.jsx)
  On the chat side this exports `SourcesPanel`, which shows grounding evidence.

- [SourceBadge.jsx](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/components/SourceBadge.jsx)
  Small presentational component for one source card.

## Why Some File Names Feel Odd

A few filenames no longer match the exported component names perfectly:

- `AnswerPanel.jsx` exports `BuildSummaryPanel`
- `AskPanel.jsx` exports `UserControlsPanel`
- `CitationsPanel.jsx` exports `SourcesPanel`
- `HistoryPanel.jsx` exports `SessionsPanel`

This happened because the app evolved from an earlier simpler UI, and some filenames were kept while behavior changed.

If you want to simplify further, the next cleanup would be renaming these files so names match the component purpose exactly.

## Data Flow

Here is the normal flow:

1. A component renders.
2. The component reads state from a store using `useAppStore()`, `useCorpusStore()`, or `useChatStore()`.
3. If the user clicks a button or submits a form, the component calls a store action.
4. The store action calls the backend using `fetchJson()`.
5. The store updates React state.
6. Any components consuming that state re-render.

Example:

- user clicks "Upload and build"
- `BuildPanel` calls `submitBuild()`
- `submitBuild()` in `CorpusStore` sends files to the backend
- `CorpusStore` updates:
  - selected corpus
  - latest build result
  - progress/status
- admin panels re-render automatically

## API Layer

File:
[client.js](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/api/client.js)

This file does two things:

- resolves the backend base URL
- provides `fetchJson()` so every store uses the same request/error handling

This keeps API logic out of components.

## Utility Layer

Files:

- [appRuntime.js](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/utils/appRuntime.js)
- [formatters.js](/Users/aditya_vikram_bhattacharya/Documents/CODE/RagChatBotFAQs/frontend/src/utils/formatters.js)

Purpose:

- route parsing from the URL hash
- session id creation
- API base resolution
- formatting timestamps for display

These helpers keep repeated logic out of stores/components.

## Why It Feels Complicated

The main reasons are:

1. The app is really two workflows in one.
   Admin + chat live in the same frontend.

2. Some components are still named from older versions.
   That adds mental friction.

3. `CorpusStore` is doing a lot.
   It handles overview loading, corpus detail loading, file upload, build status, and retriever preview.

4. There is route state, corpus state, and chat state all at once.
   That is more to keep in your head than a normal single-page chat app.

## What I Would Simplify Next

If you want to make it easier to maintain, these are the best next steps:

1. Rename confusing files so names match the actual exported component.
2. Split `CorpusStore` into:
   - `AdminStore`
   - `CorpusStore`
3. Add a dedicated `routes/` folder with:
   - `AdminPage`
   - `ChatPage`
4. Move backend response-shaping into adapter/helper functions so the stores are less crowded.

## Practical Mental Model

Use this mental model when reading the code:

- `App.jsx` = page assembly
- `AppStore` = top bar and route state
- `CorpusStore` = admin side and corpus loading
- `ChatStore` = user chat side
- `components/` = visual pieces only

If you keep that separation in mind, the code becomes much easier to navigate.

## Current File Map

```text
frontend/src/
  App.jsx
  api/
    client.js
  components/
    AnswerPanel.jsx
    AskPanel.jsx
    BuildPanel.jsx
    ChunksPanel.jsx
    CitationsPanel.jsx
    CorpusListPanel.jsx
    DocumentsPanel.jsx
    HeroSection.jsx
    HistoryPanel.jsx
    PreviewPanel.jsx
    SourceBadge.jsx
    TranscriptPanel.jsx
  stores/
    AppStore.jsx
    ChatStore.jsx
    CorpusStore.jsx
  utils/
    appRuntime.js
    formatters.js
```

## Final Note

The frontend is more modular than before, but not yet "fully simplified."

It is now better organized, but still carries some historical naming and mixed responsibilities from earlier versions. That is why it feels cleaner than before, but not yet truly minimal.
