# AI Code Reviewer — RAG-Powered Python Application

## Overview

A full-stack AI-powered code reviewer built entirely in Python with a RAG (Retrieval-Augmented Generation) architecture.

## Architecture

```
User Code Input
     ↓
Static Analysis Engine (Python AST)      ← python-backend/ast_analyzer.py
     ↓
RAG Retrieval (TF-IDF cosine similarity) ← python-backend/rag_engine.py
     ↓
Prompt Builder                           ← python-backend/ai_reviewer.py
     ↓
AI (GPT-5.2 via Replit AI Integrations)
     ↓
Structured Markdown Review
     ↓
Flask Frontend Rendering                 ← python-frontend/app.py
```

## Tech Stack

- **Frontend**: Python Flask (port 5000)
- **Backend**: Python FastAPI + Uvicorn (port 8001)
- **AI**: Replit AI Integrations → OpenAI GPT-5.2
- **Database**: SQLite (code_reviews.db, stored in python-backend/)
- **RAG Memory**: TF-IDF + cosine similarity via scikit-learn
- **Static Analysis**: Python `ast` module (AST parsing)

## Project Structure

```
python-backend/
├── main.py          # FastAPI app — REST API for code reviews
├── ast_analyzer.py  # Python AST static analysis engine
├── rag_engine.py    # RAG retrieval using TF-IDF + cosine similarity
├── ai_reviewer.py   # OpenAI client + prompt builder
└── database.py      # SQLite persistence layer

python-frontend/
├── app.py           # Flask app — renders UI, proxies to FastAPI
├── templates/
│   ├── base.html    # Navigation layout
│   ├── index.html   # Code submission form
│   ├── result.html  # Review result page
│   └── history.html # Past reviews list
└── static/
    ├── css/style.css
    └── js/app.js
```

## Workflows

- **FastAPI Backend**: `cd python-backend && python main.py` (port 8001)
- **Start application** (Flask frontend): `cd python-frontend && PORT=5000 BACKEND_URL=http://localhost:8001 python app.py` (port 5000)

## API Endpoints (FastAPI)

- `POST /api/review` — Submit code for review
- `GET /api/reviews` — List past reviews
- `GET /api/reviews/{id}` — Get a specific review
- `GET /api/health` — Health check

## RAG Architecture

1. New code is submitted
2. Past reviews are fetched from SQLite
3. TF-IDF vectors are computed for all stored code + new code
4. Top-K most similar reviews are retrieved via cosine similarity
5. Retrieved reviews are formatted as context in the LLM prompt
6. GPT-5.2 generates a structured Markdown review using the RAG context
7. The review is saved to SQLite for future RAG retrieval

## Static Analysis Features (Python AST)

- Mutable default arguments (bug)
- Bare except clauses (warning)
- Global variable usage (warning)
- Long functions > 50 lines (warning)
- Missing docstrings (info)
- Cyclomatic complexity estimate
- Function/class/import counts

## Environment Variables

- `AI_INTEGRATIONS_OPENAI_BASE_URL` — Replit AI proxy URL (auto-set)
- `AI_INTEGRATIONS_OPENAI_API_KEY` — Replit AI key (auto-set)
- `PORT` — Flask port (default 5000)
- `BACKEND_URL` — FastAPI URL (default http://localhost:8001)
- `FASTAPI_PORT` — FastAPI port (default 8001)
- `SQLITE_DB_PATH` — SQLite DB file path (default code_reviews.db)

## Monorepo (existing Node.js workspace)

The Node.js pnpm monorepo structure (api-server, mockup-sandbox) is preserved but not used by this Python application.
