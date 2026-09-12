# AI Life Memory — Backend Status & Remaining Work

## Project

AI Life Memory is a mobile application where users save personal memories through text, voice, images, and documents.

Core pipeline:

Capture → Process → Store → Retrieve → Answer

The backend is built with:

- Python
- FastAPI
- PostgreSQL
- pgvector
- SQLAlchemy
- psycopg
- Pydantic
- OpenAI API
- Docker

Backend architecture:

API → Service → Repository → Database

AI/RAG architecture will eventually be:

User Question
    ↓
Query Processing
    ↓
Semantic Search + Keyword Search
    ↓
RRF
    ↓
Reranking
    ↓
Relevant Memories
    ↓
LLM
    ↓
Answer + Sources


# CURRENT BACKEND STRUCTURE

backend/
└── app/
    ├── api/
    │   ├── __init__.py
    │   └── memories.py
    ├── core/
    │   └── config.py
    ├── db/
    │   ├── base.py
    │   └── database.py
    ├── models/
    │   ├── __init__.py
    │   └── memory.py
    ├── repositories/
    │   ├── __init__.py
    │   └── memory_repository.py
    ├── schemas/
    │   ├── __init__.py
    │   └── memory.py
    ├── services/
    │   ├── __init__.py
    │   └── memory_service.py
    ├── __init__.py
    └── main.py

backend/
├── .env
├── .env.example
├── requirements.txt
└── create_tables.py


# DATABASE

Docker Compose uses:

- PostgreSQL 16
- pgvector

Database:

name: ai_life_memory
user: ai_life_memory
port: 5432

pgvector extension is already enabled.

Current table:

memories

Columns:

- id
- user_id
- content
- source
- created_at
- occurred_at

Current SQLAlchemy model:

class Memory(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="text",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )


# ENVIRONMENT

backend/.env contains:

DATABASE_URL=postgresql+psycopg://ai_life_memory:dev_password@localhost:5432/ai_life_memory

Do not commit .env.

.env.example is safe to commit.


# ALREADY IMPLEMENTED

## FastAPI

GET /health

returns:

{
    "status": "ok"
}


## Memory endpoints

POST /memories/

Creates a memory.

Currently user_id is temporarily:

"dev-user"

This MUST eventually be replaced with the authenticated user's ID.

GET /memories/

Returns all memories.

GET /memories/{memory_id}

Returns one memory.

Returns HTTP 404 if the memory does not exist.


# CURRENT ARCHITECTURE

The API currently calls:

MemoryService

The service calls:

MemoryRepository

The repository accesses:

SQLAlchemy → PostgreSQL

Do NOT move database queries back into the API layer.


# CURRENT REPOSITORY

MemoryRepository currently has:

create()
get_all()
get_by_id()

Database access should remain inside the repository.


# CURRENT SERVICE

MemoryService currently has:

create_memory()
get_memories()
get_memory()

The service is intentionally thin right now.

Later it will contain business logic such as:

- AI processing
- summaries
- topics
- entities
- embeddings
- search logic
- RAG orchestration


# IMMEDIATE TASK

Finish the Memory CRUD.

Already implemented:

CREATE
POST /memories/

READ ALL
GET /memories/

READ ONE
GET /memories/{id}

Still needed:

UPDATE
PUT or PATCH /memories/{id}

DELETE
DELETE /memories/{id}


# UPDATE REQUIREMENTS

Create a MemoryUpdate Pydantic schema.

Fields should be optional so partial updates are possible.

Example:

class MemoryUpdate(BaseModel):
    content: str | None = None
    occurred_at: datetime | None = None

Do not allow changing:

- id
- user_id
- created_at

Source should not be changed through the basic update endpoint unless there is a clear architectural reason.

Implement update through:

API → Service → Repository


# DELETE REQUIREMENTS

Implement:

DELETE /memories/{memory_id}

Expected behavior:

- delete existing memory
- return appropriate response
- return 404 if memory does not exist

Implement through:

API → Service → Repository


# AFTER CRUD

Once CRUD is complete, improve the backend foundation before implementing AI.

Recommended order:

1. Complete CRUD
2. Add proper error handling
3. Add user isolation
4. Add authentication
5. Add database migrations with Alembic
6. Add tests
7. Improve project configuration
8. Add AI memory processing
9. Add embeddings
10. Add semantic search
11. Add keyword search
12. Add hybrid search
13. Add RRF
14. Add RAG chat


# IMPORTANT: USER IS LEARNING AI ENGINEERING

This project is also a learning project.

Do not blindly generate large amounts of code.

When implementing a feature:

1. Inspect the existing code.
2. Explain briefly what will change.
3. Implement the smallest coherent change.
4. Verify it.
5. Do not rewrite working code unnecessarily.

Prefer simple, understandable implementations over premature abstractions.


# AI MEMORY MODEL — FUTURE

The Memory model will eventually include:

Memory
├── id
├── user_id
├── content
├── source
├── created_at
├── occurred_at
├── summary
├── topics
├── entities
├── embedding
└── metadata


Important:

created_at = when the memory was saved.

occurred_at = when the event actually happened.


# FUTURE AI PIPELINE

When creating a memory:

content
   ↓
AI processing
   ├── summary
   ├── topics
   └── entities
   ↓
embedding
   ↓
PostgreSQL + pgvector


Embedding experimentation will eventually compare:

1. content only
2. content + summary
3. content + summary + topics + entities


# FUTURE SEARCH

Semantic search:

query
 ↓
embedding
 ↓
pgvector
 ↓
similar memories


Keyword search:

query
 ↓
keyword matching
 ↓
candidate memories


Hybrid:

Semantic Search
      +
Keyword Search
      ↓
     RRF
      ↓
Combined ranking


# FUTURE RAG

User question
    ↓
query processing
    ↓
hybrid search
    ↓
RRF
    ↓
reranking
    ↓
relevant memories
    ↓
context
    ↓
LLM
    ↓
answer + memory sources


The LLM should NOT be used as the search engine.

Retrieval must find relevant memories first.


# AUTHENTICATION

Authentication is not implemented yet.

Current:

user_id = "dev-user"

Do not pretend this is production authentication.

Eventually:

Firebase Authentication
        ↓
FastAPI
        ↓
authenticated user ID
        ↓
user-specific memories


VERY IMPORTANT:

Every memory query must eventually be scoped by user_id.

A user must never be able to access another user's memories.


# DATABASE MIGRATIONS

Current tables were created using:

Base.metadata.create_all()

This is acceptable for the current development stage.

Before the project becomes production-ready, introduce:

Alembic

Do not unnecessarily introduce Alembic before the current CRUD/foundation is stable.


# TESTING

Tests are not implemented yet.

Eventually add pytest tests for:

- health endpoint
- create memory
- list memories
- get memory
- update memory
- delete memory
- 404 behavior
- user isolation
- AI processing
- semantic search
- hybrid search
- RRF
- RAG


# DEVELOPMENT RULES

Do not:

- replace FastAPI
- replace PostgreSQL
- replace pgvector
- replace SQLAlchemy
- introduce another backend framework
- introduce unnecessary dependencies
- put database queries inside API endpoints
- put OpenAI calls directly inside API endpoints
- implement the entire AI system at once
- remove existing working functionality


Keep this architecture:

API
 ↓
Service
 ↓
Repository
 ↓
Database


AI-specific logic should eventually live under:

app/ai/


# NEXT MILESTONES

M0 Foundation
- FastAPI
- Docker
- PostgreSQL
- pgvector
- configuration
- DB connection

M1 Create & Store Memories
- CRUD
- user isolation foundation

M2 AI Memory Processing
- summary
- topics
- entities

M3 Embeddings + pgvector

M4 Semantic Search

M5 Hybrid Search + RRF

M6 RAG Chat

M7 Voice Memories

M8 Multimodal Memories

v1.0 AI Life Memory