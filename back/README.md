# back/ — Prototype A2A Hub

> **This is a prototype.** It uses in-memory Python dicts for storage and resets on every restart.
> All new feature work belongs in the **production backend** at `front/backend/open_webui/`.
> This directory exists for quick local experimentation and as a reference implementation.

## What It Does

A lightweight FastAPI service that:
- Serves its own A2A discovery card at `GET /.well-known/agent.json`
- Manages a registry of agents and chat sessions (in-memory)
- Routes JSON-RPC 2.0 `message/send` requests to registered agents
- Used for local dev and testing without running the full Open WebUI stack

## Running Locally

```bash
cd back/
pip install -r requirements.txt
uvicorn main:app --reload   # http://localhost:8000
```

Interactive API docs: `http://localhost:8000/docs`

## Testing

```bash
cd back/
pytest tests/ -v
```

## Key Differences from the Production Backend

| Concern | Prototype (`back/`) | Production (`front/backend/open_webui/`) |
|---------|--------------------|-----------------------------------------|
| Storage | In-memory dicts (lost on restart) | SQLite via Peewee ORM (persistent) |
| Auth | None | JWT + Microsoft SSO (MSAL) |
| CORS | `allow_origins=["*"]` | Restricted origins |
| Scale | Single process | Uvicorn with async workers |
| Migrations | N/A | Alembic |

## Files

| File | Purpose |
|------|---------|
| `main.py` | All routes, models, and JSON-RPC handler |
| `requirements.txt` | Python dependencies |
| `tests/` | pytest test suite |
