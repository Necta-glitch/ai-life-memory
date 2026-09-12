# AGENTS.md

## Project: AI Life Memory

AI Life Memory is a mobile application that allows users to capture, organize,
search, and retrieve personal memories using AI.

The application is being developed as a portfolio project focused on
demonstrating professional Mobile Development and AI Engineering practices.

The core idea is:

Capture → Process → Store → Retrieve → Answer

Users should be able to save experiences, thoughts, learnings, events, and
other personal information and later retrieve them using natural language.

---

# 1. Agent Role

You are a development agent working on the AI Life Memory project.

Your responsibilities are:

- Understand the existing architecture before modifying code.
- Follow the existing project structure and conventions.
- Make small, isolated changes.
- Avoid unnecessary refactors.
- Do not introduce new libraries without a clear reason.
- Do not replace existing technologies without explicit approval.
- Explain important architectural decisions.
- Keep the code production-oriented.
- Preserve compatibility between Mobile and Backend.
- Run relevant tests or validation commands after changes.
- Never expose secrets or credentials.

The project owner is actively learning AI Engineering while building this
application.

Therefore, when implementing something important, explain briefly:

1. What is being implemented.
2. Why it is needed.
3. Where it belongs in the architecture.
4. How it connects with the rest of the system.

Do not simply generate code without explaining the architectural role.

---

# 2. Product Vision

AI Life Memory is a personal memory system.

The user can save:

- Experiences
- Thoughts
- Learnings
- Events
- Notes
- Important moments

Initially memories are captured through text.

Future versions will support:

- Voice
- Images
- Documents

The user should later be able to ask questions such as:

"What did I learn about JavaScript async programming?"

"What did I do last Saturday?"

"What were the things I worked on this week?"

The system should retrieve relevant memories and use an LLM to generate an
answer grounded in those memories.

The LLM is NOT the primary search engine.

Retrieval happens before generation.

---

# 3. High-Level Architecture

The system follows this architecture:

React Native
    │
    │ HTTPS
    ▼
FastAPI
    │
    ├── Authentication
    ├── Memories API
    ├── Search API
    ├── Chat API
    ├── AI Processing
    └── RAG
          │
          ├── PostgreSQL + pgvector
          └── OpenAI

The main RAG flow is:

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

---

# 4. Repository Structure

The repository is organized as a monorepo:

```text
ai-life-memory/
├── mobile/
├── backend/
├── docs/
│   ├── product/
│   ├── architecture/
│   └── decisions/
├── .github/
│   └── workflows/
├── AGENTS.md
├── README.md
├── CHANGELOG.md
├── LICENSE
├── .gitignore
└── docker-compose.yml