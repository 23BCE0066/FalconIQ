# FalconIQ: Enterprise AI-Powered AML Investigation Platform

FalconIQ is an enterprise-grade AI-powered Anti-Money Laundering (AML) investigation platform built for financial institutions. It utilizes an Agentic AI architecture (Planner & Supervisor) to dynamically construct workflows based on natural language queries, bypassing static rule-based rigid systems.

## Architecture
- **Backend:** Modular Monolith using FastAPI & Python 3.11+.
- **Database:** SQLite with SQLModel for unified Pydantic+SQLAlchemy schemas.
- **AI Core:** Gemini Flash for Planning and Explainability.
- **State Management:** InMemory/SQLite Execution Context to trace runs.
- **Frontend (TBD):** Next.js & TailwindCSS.

## Folder Structure
```
backend/
└── app/
    ├── api/          # RESTful endpoints (v1)
    ├── agents/       # AI Logic (Planner, Supervisor)
    ├── config/       # Environment & yaml configurations
    ├── constants/    # Fixed variables, enums
    ├── core/         # Base classes, exceptions, DI
    ├── database/     # DB engine and SQLModel definitions
    ├── interfaces/   # Interfaces for loose coupling
    ├── logging/      # Structured logging via structlog
    ├── middleware/   # Request tracing, global error handling
    ├── repository/   # Data access layer
    ├── schemas/      # Pydantic payloads (request/responses)
    ├── services/     # Business logic layer
    ├── tools/        # Tool registry and implementations
    └── utils/        # Helpers, parsers, generators
```

## Run Instructions
1. Setup Python environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```
2. Setup environment variables:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY
   ```
3. Run the development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Roadmap
- **Phase 1:** Infrastructure (Logging, Config, Database, Middleware, Base Classes)
- **Phase 2:** Core Framework (ExecutionContext, Tool Registry)
- **Phase 3:** AI Layer (Planner, Supervisor)
- **Phase 4:** Business Layer (Rules, ML, Features)
- **Phase 5:** API (FastAPI Routes)
- **Phase 6:** Frontend (Next.js)
- **Phase 7:** Testing & Demo Data
