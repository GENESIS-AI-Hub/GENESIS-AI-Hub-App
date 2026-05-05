# Gemini Agent

A minimal A2A-compatible agent server that proxies requests to the Google Gemini API via the OpenAI-compatible endpoint.

## What It Does

Exposes a JSON-RPC 2.0 endpoint (`POST /`) and an A2A discovery card (`GET /.well-known/agent.json`). When OpenBeavs sends a `message/send` request, this server forwards the text to Gemini (via `https://generativelanguage.googleapis.com/v1beta/openai/`) and returns the response.

**Port:** `8004`

## Setup

### 1. Install dependencies

```bash
cd agents/gemini-agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your Google API key:

```
GEMINI_API_KEY=AIza...
```

Get a key at [aistudio.google.com](https://aistudio.google.com).

### 3. Start the server

```bash
python agent.py
```

The agent card will be available at `http://localhost:8004/.well-known/agent.json`.

## Install in OpenBeavs

1. Ensure the server is running (step 3 above).
2. Go to **Workspace → Agents** → click **+**.
3. Enter `http://localhost:8004` and click **Add**.

The agent will appear in the model selector and Arena mode.

## Available Models

Default: `gemini-2.0-flash`

Also supported (pass via `params.model` in the JSON-RPC request):
- `gemini-2.5-pro`
- `gemini-2.5-flash`
- `gemini-2.0-flash-lite`
- `gemini-1.5-pro`
- `gemini-1.5-flash`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | Yes | — | Google AI Studio API key (`AIza...`) |
| `AGENT_URL` | No | `http://localhost:8004` | Public URL reported in the agent card |
| `PORT` | No | `8004` | Port to bind the server to |
