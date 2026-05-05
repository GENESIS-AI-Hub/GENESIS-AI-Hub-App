# Claude Agent

A minimal A2A-compatible agent server that proxies requests to the Anthropic Claude API.

## What It Does

Exposes a JSON-RPC 2.0 endpoint (`POST /`) and an A2A discovery card (`GET /.well-known/agent.json`). When OpenBeavs sends a `message/send` request, this server forwards the text to Claude and returns the response.

**Port:** `8002`

## Setup

### 1. Install dependencies

```bash
cd agents/claude-agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

Get a key at [console.anthropic.com](https://console.anthropic.com).

### 3. Start the server

```bash
python agent.py
```

The agent card will be available at `http://localhost:8002/.well-known/agent.json`.

## Install in OpenBeavs

1. Ensure the server is running (step 3 above).
2. Go to **Workspace → Agents** → click **+**.
3. Enter `http://localhost:8002` and click **Add**.

The agent will appear in the model selector and Arena mode.

## Available Models

Default: `claude-sonnet-4-6`

Also supported (pass via `params.model` in the JSON-RPC request):
- `claude-opus-4-6`
- `claude-haiku-4-5-20251001`
- `claude-3-5-sonnet-20241022`
- `claude-3-5-haiku-20241022`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic API key (`sk-ant-...`) |
| `AGENT_URL` | No | `http://localhost:8002` | Public URL reported in the agent card |
| `PORT` | No | `8002` | Port to bind the server to |
