# ChatGPT Agent

A minimal A2A-compatible agent server that proxies requests to the OpenAI API.

## What It Does

Exposes a JSON-RPC 2.0 endpoint (`POST /`) and an A2A discovery card (`GET /.well-known/agent.json`). When OpenBeavs sends a `message/send` request, this server forwards the text to OpenAI and returns the response.

**Port:** `8003`

## Setup

### 1. Install dependencies

```bash
cd agents/chatgpt-agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
CHATGPT_API_KEY=sk-...
```

Get a key at [platform.openai.com](https://platform.openai.com).

### 3. Start the server

```bash
python agent.py
```

The agent card will be available at `http://localhost:8003/.well-known/agent.json`.

## Install in OpenBeavs

1. Ensure the server is running (step 3 above).
2. Go to **Workspace → Agents** → click **+**.
3. Enter `http://localhost:8003` and click **Add**.

The agent will appear in the model selector and Arena mode.

## Available Models

Default: `gpt-4o`

Also supported (pass via `params.model` in the JSON-RPC request):
- `gpt-4o-mini`
- `gpt-4-turbo`
- `o1`
- `o3-mini`

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CHATGPT_API_KEY` | Yes | — | OpenAI API key (`sk-...`) |
| `AGENT_URL` | No | `http://localhost:8003` | Public URL reported in the agent card |
| `PORT` | No | `8003` | Port to bind the server to |
