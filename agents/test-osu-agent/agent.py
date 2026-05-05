"""
Minimal test A2A agent: OSU Expert stub.

Implements the A2A protocol (JSON-RPC 2.0 + /.well-known/agent.json) using
only fastapi + uvicorn — no ML dependencies required.
Returns canned OSU information so you can test Chris routing end-to-end.

Usage:
    cd agents/test-osu-agent
    python agent.py          # runs on port 8002
    python agent.py --port 8003
"""

import sys
import uuid

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

PORT = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8002
BASE_URL = f"http://localhost:{PORT}"

app = FastAPI(title="OSU Expert Agent (test stub)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/.well-known/agent.json")
def agent_card(request: Request):
    """A2A discovery card."""
    return {
        "name": "OSU Expert",
        "description": (
            "Expert on Oregon State University: academics, athletics, admissions, "
            "campus life, research programs, and history."
        ),
        "url": BASE_URL,
        "version": "1.0.0",
        "capabilities": {"streaming": False},
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": "osu_info",
                "name": "OSU Information",
                "description": "Answer questions about Oregon State University.",
                "tags": ["osu", "oregon state", "university", "college", "beavers", "corvallis"],
                "examples": [
                    "What majors does OSU offer?",
                    "Tell me about OSU's computer science program",
                    "When was Oregon State University founded?",
                    "How do I apply to OSU?",
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

    params = body.get("params", {})
    message = params.get("message", {})
    parts = message.get("parts", [])
    user_text = next((p.get("text", "") for p in parts if p.get("type") == "text"), "")

    # Canned response — swap in the real OSU expert ADK agent here
    reply = (
        f"[OSU Expert] Answering your question about OSU: '{user_text}'\n\n"
        "Oregon State University (OSU) was founded in 1868 and is located in Corvallis, Oregon. "
        "It's a Land Grant research university with over 200 undergraduate programs across colleges "
        "including Engineering, Liberal Arts, Science, Business, and Forestry. "
        "The Beavers compete in the Pac-12 Conference. "
        "OSU's computer science program is housed in the College of Engineering and is nationally ranked."
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
    print(f"\n OSU Expert Agent (test stub)")
    print(f" Port       : {PORT}")
    print(f" Agent card : {BASE_URL}/.well-known/agent.json")
    print(f" A2A RPC    : POST {BASE_URL}/\n")
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")
