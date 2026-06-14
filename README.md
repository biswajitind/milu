# agai

A RAG-based chat application that grounds LLM responses in your own documents.

## Overview

Users ask questions in a chat UI. The system retrieves relevant context from a vector store, augments the prompt, and streams an answer from an LLM. Documents are ingested separately through an indexing pipeline.

## High-Level Architecture

```mermaid
graph TB
    subgraph Client
        UI[Chat UI]
    end

    subgraph API["API Layer"]
        GW[API Gateway / FastAPI]
        CHAT[Chat Service]
        INGEST[Ingestion Service]
    end

    subgraph RAG["RAG Pipeline"]
        EMB_Q[Query Embedder]
        RET[Retriever]
        RERANK[Reranker]
        CTX[Context Builder]
    end

    subgraph LLM["LLM Layer"]
        PROMPT[Prompt Composer]
        GEN[LLM / Generator]
    end

    subgraph Data["Data Layer"]
        VDB[(Vector DB)]
        META[(Metadata Store)]
        OBJ[(Object Storage)]
        CACHE[(Session Cache)]
    end

    UI -->|question + session| GW
    GW --> CHAT
    GW --> INGEST

    CHAT --> EMB_Q
    EMB_Q --> RET
    RET --> VDB
    RET --> RERANK
    RERANK --> CTX
    CTX --> PROMPT
    PROMPT --> GEN
    GEN -->|streamed answer| UI
    CHAT --> CACHE

    INGEST --> OBJ
    INGEST --> META
    INGEST -->|chunk + embed| VDB
```

## Chat Request Flow

```mermaid
sequenceDiagram
    actor User
    participant UI as Chat UI
    participant API as Chat API
    participant EMB as Embedder
    participant VDB as Vector DB
    participant LLM as LLM
    participant Cache as Session Cache

    User->>UI: Ask a question
    UI->>API: POST /chat {message, session_id}

    API->>Cache: Load conversation history
    Cache-->>API: Prior turns

    API->>EMB: Embed user query
    EMB-->>API: Query vector

    API->>VDB: Similarity search (top-k)
    VDB-->>API: Relevant chunks + scores

    API->>API: Rerank & trim context window
    API->>LLM: System prompt + context + history + question
    LLM-->>API: Stream tokens
    API-->>UI: SSE / WebSocket stream
    UI-->>User: Render answer with citations

    API->>Cache: Save turn (question + answer + sources)
```

## Document Ingestion Pipeline

```mermaid
flowchart LR
    SRC[Sources] --> LOAD[Loader]
    LOAD --> PARSE[Parser]
    PARSE --> CHUNK[Chunker]
    CHUNK --> EMB[Embedder]
    EMB --> UPSERT[Upsert to Vector DB]
    PARSE --> META[Store metadata]

    subgraph Sources
        PDF[PDF]
        MD[Markdown]
        WEB[Web pages]
        API_SRC[API / DB exports]
    end

    SRC --- PDF
    SRC --- MD
    SRC --- WEB
    SRC --- API_SRC
```

## Component Responsibilities

| Component | Role |
|---|---|
| **Chat UI** | Message input, streamed responses, source citations |
| **Chat API** | Orchestrates retrieval, prompting, and session state |
| **Ingestion Service** | Loads, chunks, embeds, and indexes documents |
| **Embedder** | Converts text to vectors (same model for ingest & query) |
| **Vector DB** | Stores embeddings; runs similarity search |
| **Reranker** | Re-scores retrieved chunks for relevance (optional) |
| **Context Builder** | Assembles top chunks within token budget |
| **LLM** | Generates the final grounded answer |
| **Session Cache** | Persists multi-turn conversation history |

## Prompt Composition

```mermaid
graph LR
    SYS[System instructions] --> PROMPT[Final Prompt]
    CTX[Retrieved context] --> PROMPT
    HIST[Chat history] --> PROMPT
    Q[User question] --> PROMPT
    PROMPT --> LLM[LLM]
```

Typical structure:

1. **System** — answer only from provided context; cite sources; say "I don't know" when context is insufficient
2. **Context** — top-k retrieved chunks with document IDs
3. **History** — recent conversation turns
4. **User** — current question

## Data Model

```mermaid
erDiagram
    DOCUMENT ||--o{ CHUNK : contains
    CHUNK ||--o{ EMBEDDING : has
    SESSION ||--o{ MESSAGE : contains
    MESSAGE }o--o{ CHUNK : cites

    DOCUMENT {
        string id
        string title
        string source_uri
        datetime ingested_at
    }

    CHUNK {
        string id
        string document_id
        int chunk_index
        text content
        json metadata
    }

    EMBEDDING {
        string chunk_id
        vector embedding
    }

    SESSION {
        string id
        string user_id
        datetime created_at
    }

    MESSAGE {
        string id
        string session_id
        string role
        text content
        json source_refs
    }
```

## Deployment View

```mermaid
graph TB
    subgraph Frontend
        WEB[Web App]
    end

    subgraph Backend
        API_SVC[API Service]
        WORKER[Ingestion Worker]
    end

    subgraph External
        LLM_API[LLM Provider]
        EMB_API[Embedding Provider]
    end

    subgraph Storage
        PG[(Postgres)]
        VDB[(Vector DB)]
        S3[(Object Storage)]
        REDIS[(Redis)]
    end

    WEB --> API_SVC
    API_SVC --> LLM_API
    API_SVC --> EMB_API
    API_SVC --> VDB
    API_SVC --> REDIS
    API_SVC --> PG

    WORKER --> S3
    WORKER --> EMB_API
    WORKER --> VDB
    WORKER --> PG
```

## Key Design Decisions

- **Same embedder for ingest and query** — ensures vectors live in the same semantic space
- **Chunk-level retrieval, document-level citations** — balance precision with readable source links
- **Streaming responses** — improves perceived latency for long answers
- **Session-aware history** — enables follow-up questions without re-sending full context each turn
- **Separate ingest path** — indexing is async and decoupled from the chat hot path

## Suggested Stack (reference)

| Layer | Options |
|---|---|
| API | FastAPI, Python |
| Vector DB | pgvector, Qdrant, Pinecone |
| LLM | OpenAI, Anthropic, local via Ollama |
| Embeddings | OpenAI, sentence-transformers |
| Object storage | S3, MinIO |
| Session store | Redis |
| Metadata | PostgreSQL |
