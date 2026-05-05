"""
Minimal test A2A agent: Weather Expert stub.

Implements the A2A protocol (JSON-RPC 2.0 + /.well-known/agent.json) using
only fastapi + uvicorn — no ML dependencies required.
Returns a canned weather response so you can test Chris routing end-to-end.

Usage:
    cd agents/test-weather-agent
    python agent.py          # runs on port 8001
    python agent.py --port 8002
"""

import sys
import uuid

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8001
BASE_URL = f"http://localhost:{PORT}"

app = FastAPI(title="Weather Expert Agent (test stub)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/.well-known/agent.json")
def agent_card(request: Request):
    """A2A discovery card."""
    return {
        "name": "Weather Expert",
        "description": "Provides current weather conditions and forecasts for any location.",
        "url": BASE_URL,
        "version": "1.0.0",
        "capabilities": {"streaming": False},
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": "weather_lookup",
                "name": "Weather Lookup",
                "description": "Get current weather or forecast for a city or region.",
                "tags": ["weather", "forecast", "temperature", "climate"],
                "examples": [
                    "What is the weather in Portland?",
                    "Will it rain in Corvallis tomorrow?",
                    "Temperature in Seattle right now",
                ],
            }
        ],
    }


@app.post("/")
async def handle_jsonrpc(request: Request):
    """A2A JSON-RPC 2.0 message handler."""
    body = await request.json()
    rpc_id = body.get("id", 1)
    method = body.get("method", "")

    if method != "message/send":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {"code": -32601, "message": f"Method '{method}' not found"},
        })

    # Extract user text from the A2A message
    params = body.get("params", {})
    message = params.get("message", {})
    parts = message.get("parts", [])
    user_text = next((p.get("text", "") for p in parts if p.get("type") == "text"), "")

    # Canned response — swap in a real weather API call here
    reply = (
        f"[Weather Expert] Here's the weather update for your query: '{user_text}'\n\n"
        "Currently: 58°F / 14°C, partly cloudy with a chance of rain. "
        "Tomorrow: high of 62°F, low of 48°F. "
        "Extended forecast: expect rain mid-week typical of Pacific Northwest spring."
    )

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": rpc_id,
        "result": {
            "artifacts": [
                {
                    "artifactId": str(uuid.uuid4()),
                    "parts": [{"type": "text", "text": reply}],
                }
            ]
        },
    })


if __name__ == "__main__":
    print(f"\n Weather Expert Agent (test stub)")
    print(f" Port       : {PORT}")
    print(f" Agent card : {BASE_URL}/.well-known/agent.json")
    print(f" A2A RPC    : POST {BASE_URL}/\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
