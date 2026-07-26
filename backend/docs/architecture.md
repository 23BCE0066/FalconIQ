# FalconIQ Architecture & API

## Overview
FalconIQ is an enterprise-grade AI Compliance Officer designed for Anti-Money Laundering (AML) investigations. It leverages a strict Modular Monolith architecture pattern combining Pydantic/SQLModel for validation/persistence and Gemini for dynamic intelligence.

## System Flow
1. **API Layer**: Receives natural language queries on `/api/v1/chat`.
2. **Supervisor Agent**: Initiates an execution session, generates a Request ID.
3. **Planner Agent**: Queries Gemini to formulate a structured ExecutionPlan (tools to run).
4. **Workflow Builder**: Turns the plan into a resolved directed acyclic graph (DAG) of tools.
5. **Tool Execution Loop**: Supervisor runs each tool dynamically passing an `ExecutionContext`.
6. **Persistence**: `SessionRepository` logs immutable records in `agent_execution_logs`.

## Core Technologies
* **Framework**: FastAPI + Pydantic V2
* **Database**: SQLite + SQLModel
* **Data Processing**: Pandas
* **AI Orchestration**: Custom framework + Gemini 2.5 Flash
* **Network Analysis**: NetworkX

## API Endpoints

### `GET /api/v1/health`
Validates readiness of database, tools registry, and API keys.

### `POST /api/v1/chat`
Submit a natural language investigation.
**Body:**
```json
{
  "query": "Find structuring patterns in the last 30 days"
}
```

## Running the app
```bash
poetry run uvicorn app.main:app --reload
```
