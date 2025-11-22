Result from test:

Core works: Chats CRUD, message send/receive, file attachment persistence, seeded agent, and external agent registration all function.

Validation solid: Proper 404 for missing chat/agent and 400/422 on malformed payloads.

CORS behavior: Header present correctly when Origin is sent.

Security: register-by-url lacks SSRF protections (no allowlist / localhost & metadata IP block).

Note: Pydantic v2 .dict() deprecations and deprecated startup event; streaming is stubbed.

Top fixes next: 

- JSON-RPC dispatch & chat check
- SSRF guard on register-by-URL
- replace .dict() with .model_dump() and migrate startup to lifespan.