---
name: openbeavs-admin
description: Operate a running OpenBeavs / GENESIS-AI-Hub instance over its REST API. USE THIS SKILL whenever the user asks to list agents, list users, list models, deploy an agent, register an A2A agent by URL, delete an agent, promote a user, mint a service-account bearer token, query the public registry, or health-check a hub — local or deployed. The skill documents the auth flow (POST /api/v1/auths/signin → bearer token), the trailing-slash quirk on collection endpoints (e.g. /api/v1/agents/ vs /api/v1/agents), the dev placeholder admin (admin@gmail.com / 1234), and the response shapes for the highest-traffic routes. Reads OPENBEAVS_BASE_URL and OPENBEAVS_ADMIN_TOKEN from the environment; if either is missing, ask the user before guessing.
---

# OpenBeavs admin skill

This skill teaches you how to drive a running OpenBeavs hub using `curl`. The
hub is a FastAPI service at `front/backend/open_webui/`; routers live under
`front/backend/open_webui/routers/`. When something here looks wrong, the
routers are the source of truth — open the file referenced in the section.

## Prerequisites — token and base URL

Before any request, both env vars must be set in the bash session:

- `OPENBEAVS_BASE_URL` — e.g. `http://localhost:8080` for local dev, or
  the Cloud Run URL of the active hub for prod.
- `OPENBEAVS_ADMIN_TOKEN` — a bearer token belonging to an `admin` role
  user. Either pull it from browser DevTools (`localStorage.token` after
  signing in via the UI) or call the signin endpoint below.

If either is missing, ask the user this exact question before doing
anything else:

> "I need `OPENBEAVS_BASE_URL` and `OPENBEAVS_ADMIN_TOKEN` to talk to the
> hub. What's the base URL, and do you have an admin token already, or
> would you like me to walk through `signin`?"

Never invent a URL. Never paste a token into the conversation; the user
should `export` it themselves. Treat the token like a password — do not
echo it back, do not write it to disk, and remind the user to unset it
when done (`unset OPENBEAVS_ADMIN_TOKEN`).

### Default placeholder admin (dev/staging only)

The deployed dev/staging hub seeds a placeholder admin account:

- email: `admin@gmail.com`
- password: `1234`

**Use these only after the user confirms the hub is in dev/staging
mode** — never assume them for prod. If the user has not confirmed,
ask: "Is this hub using the placeholder `admin@gmail.com / 1234`
admin, or do you have your own admin credentials?" Do NOT default to
the email in `userEmail`/the harness context — that account almost
certainly has no admin role on the hub.

### Quick start — copy this exactly

> **Note on env-var scope.** `!`-prefix lines in the Codex prompt and
> Codex's own Bash tool calls each spawn a fresh subshell —
> `export`s done in one subshell do NOT survive into later calls. So
> if the user `!export`s the vars from inside Codex, those exports
> are gone by the time Codex tries to run a curl.
>
> **How the skill should handle this:** if a Bash tool call shows
> `OPENBEAVS_BASE_URL` empty or `OPENBEAVS_ADMIN_TOKEN` unset, just
> silently re-auth in a single Bash call (sign in + use the token in
> the same heredoc or `&&` chain). It's faster than asking the user
> to exit and re-launch, and the placeholder dev creds are harmless.
> Mention afterwards (one short line) that for persistence across
> turns the user can `export` both in the terminal **before** running
> `Codex` — that way every subsequent Bash tool call inherits them
> and you don't need to re-auth on every request.
>
> The exception: re-auth ONLY when the email/password are already
> known (placeholder dev admin, or stored from earlier this session).
> If neither var is set AND no creds are known, ask the user.

The fastest way to get a working session, with the trailing slash
already correct. The user can either run these in their terminal
*before* `Codex` (preferred — exports persist for the whole
session), or paste the same block as one Bash call inside Codex
(works for one turn):

```bash
# In your terminal, BEFORE running `Codex`:
export OPENBEAVS_BASE_URL="https://openbeavs-deploy-test-<hash>.us-west1.run.app"
export OPENBEAVS_ADMIN_TOKEN=$(curl -s -X POST \
  "$OPENBEAVS_BASE_URL/api/v1/auths/signin" \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@gmail.com","password":"1234"}' \
  | jq -r .token)

Codex   # Codex inherits both vars in every Bash tool call
```

Once inside Codex, the very first thing the skill does is verify
both vars are populated:

```bash
echo "URL: $OPENBEAVS_BASE_URL"
echo "TOKEN set: $([ -n "$OPENBEAVS_ADMIN_TOKEN" ] && echo yes || echo no)"

# Confirm the token works AND you got JSON back (not HTML):
curl -fsS "$OPENBEAVS_BASE_URL/api/v1/auths/" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  | jq '{id,email,role}'

# List local agents — note the TRAILING SLASH:
curl -fsS "$OPENBEAVS_BASE_URL/api/v1/agents/" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" | jq
```

If the env-check shows either var empty and the placeholder dev
creds apply, re-auth in-line in the same Bash call and proceed:

```bash
BASE="${OPENBEAVS_BASE_URL:-https://openbeavs-deploy-test-<hash>.us-west1.run.app}"
TOKEN="${OPENBEAVS_ADMIN_TOKEN:-$(curl -s -X POST "$BASE/api/v1/auths/signin" \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@gmail.com","password":"1234"}' | jq -r .token)}"
curl -fsS "$BASE/api/v1/agents/" -H "Authorization: Bearer $TOKEN" | jq
```

Use `curl -fsS` (fail-fast on HTTP errors) and pipe through `jq` so an
HTML body fails loudly. If `jq` errors with "parse error", you almost
certainly forgot the trailing slash on a collection endpoint.

### Finding the prod URL

The active prod service is `openbeavs-deploy-test` in project
`osu-genesis-hub`, region `us-west1`. Other Cloud Run services
(`openbeavs-main`, `genesis-ai-hub-backend`) are placeholders or stale
deployments — `openbeavs-main` returns the SvelteKit shell with no
backend wired, so any API call will look like it "works" (HTTP 200 +
HTML) until you parse the body. **Always ask the user which hub** before
hitting `gcloud run services list`; if you must list, only trust
`openbeavs-deploy-test`.

### CRITICAL — trailing-slash quirk

Collection endpoints (the ones whose path ends at the router prefix)
**require a trailing slash**:

- ✅ `GET /api/v1/agents/` → JSON list from FastAPI
- ❌ `GET /api/v1/agents`  → SvelteKit shell, HTTP 200, `text/html`

This bites because the response is a 200, not a redirect or 404 — a
no-slash request silently returns the frontend HTML. If a curl returns
HTML where you expected JSON, the first thing to check is the trailing
slash. The same pattern applies to `/api/v1/users/`, `/api/v1/models/`,
`/api/v1/registry/`, `/api/v1/auths/`, and any other root-of-router GET.
Sub-paths (`/api/v1/agents/all`, `/api/v1/agents/{id}`) do NOT need the
trailing slash — only the collection root does.

Always pipe JSON-expecting responses through `jq` (or `python3 -m
json.tool`) so an accidental HTML body fails loudly instead of
spreading downstream.

## Auth surface — `/api/v1/auths`

Source: `front/backend/open_webui/routers/auths.py`.

### POST /api/v1/auths/signin (public)

Body: `{ "email": str, "password": str }`.

Response (`SigninResponse`) — fields:

| Field               | Type        | Meaning                                                          |
|---------------------|-------------|------------------------------------------------------------------|
| `token`             | str (JWT)   | Bearer token. Pass as `Authorization: Bearer <token>`.           |
| `token_type`        | str         | Always `"Bearer"`.                                               |
| `expires_at`        | int \| null | Unix epoch seconds. Null when `JWT_EXPIRES_IN=-1` (no expiry).   |
| `id`                | str         | User ID for the signed-in account.                               |
| `email`             | str         | Lowercased email.                                                |
| `name`              | str         | Display name.                                                    |
| `role`              | str         | `"pending"`, `"user"`, or `"admin"` — verify this is `"admin"` before using the token for admin routes. |
| `profile_image_url` | str         | Avatar URL.                                                      |
| `permissions`       | dict        | Resolved permission map for the user's role + group membership.  |

Errors:
- `400 "The email or password provided is incorrect..."` — bad creds.
- `403` — pending or disabled account.

Have the user run this in their own terminal so the password never
enters the chat:

```bash
read -rsp 'password: ' PASS && echo
curl -s -X POST "$OPENBEAVS_BASE_URL/api/v1/auths/signin" \
  -H 'Content-Type: application/json' \
  -d "$(jq -nc --arg e "$EMAIL" --arg p "$PASS" '{email:$e,password:$p}')" \
  | jq -r .token
unset PASS
```

### GET /api/v1/auths/ (verified user)

Verify the current token works and inspect the caller's role:

```bash
curl -s "$OPENBEAVS_BASE_URL/api/v1/auths/" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  | jq '{id,email,role}'
```

### POST /api/v1/auths/add (admin only)

Mints a new user **and returns a bearer token for that user** in the
same response. Body matches `AddUserForm`:

```
{ "name": str, "email": str, "password": str,
  "profile_image_url": str (optional, defaults to "/user.png"),
  "role": "pending" | "user" | "admin" (optional, defaults to "pending") }
```

The returned `token` is the only copy. Print it once, warn the user it
cannot be re-fetched, and do not store it anywhere.

```bash
curl -s -X POST "$OPENBEAVS_BASE_URL/api/v1/auths/add" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"CI Bot","email":"ci@example.com","password":"...","role":"user"}' \
  | jq
```

## Agents — `/api/v1/agents`

Source: `front/backend/open_webui/routers/agents.py`. An "agent" here is
a row in the `agent` table representing an A2A endpoint installed on
this hub. `deployment_mode` is one of: `internal` (served in-process by
the hub itself), `cloud_run` (separate Cloud Run service), or absent
(externally registered via URL).

### GET /api/v1/agents/ (verified user)

Returns active agents visible to the caller. Response: `List[AgentResponse]`.
Note this is a *trimmed* shape — for the full agent record (provider, model,
system_prompt, deployment_mode), use `/all` or `/{agent_id}`.

Per-row fields:

| Field          | Type                  | Meaning                                              |
|----------------|-----------------------|------------------------------------------------------|
| `id`           | str (uuid)            | Stable agent ID; use this in path params.            |
| `name`         | str                   | Display name from the discovery card or deploy form. |
| `description`  | str                   | Short description for the workspace card.            |
| `endpoint`     | str \| null           | A2A JSON-RPC POST URL. `null` for URL-only registrations. |
| `url`          | str \| null           | Base homepage URL. Always present; chat path falls back to `url` when `endpoint` is null. |
| `capabilities` | dict \| null          | A2A capability flags, typically `{"streaming": bool}`. |
| `skills`       | list[dict] \| null    | Discovery-card skills array.                         |
| `is_active`    | bool                  | Soft-delete / disable flag.                          |

```bash
curl -fsS "$OPENBEAVS_BASE_URL/api/v1/agents/" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  | jq '.[] | {id,name,endpoint,url,is_active}'
```

### GET /api/v1/agents/all (admin)

Includes inactive rows AND returns the full `AgentModel` shape — adds
these fields on top of the trimmed list above:

| Field               | Type           | Meaning                                                                                  |
|---------------------|----------------|------------------------------------------------------------------------------------------|
| `version`           | str \| null    | Discovery-card version, e.g. `"1.0.0"`.                                                  |
| `default_input_modes`  | list[str]   | A2A input modalities; usually `["text"]`.                                                |
| `default_output_modes` | list[str]   | A2A output modalities; usually `["text"]`.                                               |
| `input_schema`      | dict \| null   | Optional JSON schema for input validation.                                               |
| `output_schema`     | dict \| null   | Optional JSON schema for output validation.                                              |
| `profile_image_url` | str \| null    | Avatar URL; `/static/favicon.png` is the default fallback.                               |
| `system_prompt`     | str \| null    | Set only for agents created via `/deploy`. Null for URL-registered agents.               |
| `provider`          | str \| null    | `"anthropic"`, `"openai"`, or `"gemini"` for deployed agents; null otherwise.            |
| `model`             | str \| null    | Provider-specific model id (e.g. `"Codex-sonnet-4-6"`).                                 |
| `deployment_mode`   | str \| null    | `"internal"` (in-process), `"cloud_run"` (separate service), or null (externally registered). |
| `deployment_status` | str \| null    | `"ready"` is the only state currently emitted by `/deploy`.                              |
| `created_at`        | int            | Unix epoch seconds.                                                                      |
| `updated_at`        | int            | Unix epoch seconds.                                                                      |
| `user_id`           | str \| null    | Owner. Admins can see all rows; non-admins see only their own.                           |

How to read `deployment_mode` quickly:

- `null` → registered by URL via `/register-by-url`. The hub does not
  host this agent; chat traffic goes to `endpoint || url`.
- `"internal"` → the hub itself serves the agent in-process. The
  `endpoint` will be `{base_url}/api/v1/agents/{id}/internal-a2a`. Chat
  traffic short-circuits the HTTP round-trip via `utils/chat.py`.
- `"cloud_run"` → a separate Cloud Run service was provisioned at
  deploy time. `endpoint` is that service's URL.

### GET /api/v1/agents/{agent_id} (verified)

Returns one full `AgentModel` (same shape as `/all` rows). 404 if the
ID does not exist; 401 if a non-admin requests an agent they don't
own.

### POST /api/v1/agents/register-by-url (verified)

Fetches the target's `/.well-known/agent.json`, parses the discovery
card, and inserts an agent row. Body: `RegisterAgentByUrlForm`:

```
{ "agent_url": str, "profile_image_url": str (optional) }
```

```bash
curl -s -X POST "$OPENBEAVS_BASE_URL/api/v1/agents/register-by-url" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"agent_url":"https://weather.example.com"}' | jq
```

### POST /api/v1/agents/deploy (admin) — destructive on prod

Creates a brand-new internally-hosted A2A agent. Body: `DeployAgentForm`:

```
{ "name": str, "description": str, "system_prompt": str,
  "provider": "anthropic" | "openai" | "gemini" (default "anthropic"),
  "model": str (optional; provider default applied if omitted),
  "profile_image_url": str (optional),
  "publish_to_registry": bool (default true),
  "deploy_to_cloud_run": bool (default false) }
```

If `deploy_to_cloud_run` is true on prod, the hub gates this with
`OPENBEAVS_CLOUD_RUN_DISABLED=1` and returns 503. For internal-mode
deploys, the hub stores `endpoint = {base_url}/api/v1/agents/{id}/internal-a2a`
and serves the agent in-process.

```bash
curl -s -X POST "$OPENBEAVS_BASE_URL/api/v1/agents/deploy" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"WeatherBot",
    "description":"Answers Oregon weather questions",
    "system_prompt":"You are a concise weather assistant.",
    "provider":"anthropic"
  }' | jq
```

### DELETE /api/v1/agents/{agent_id} (verified, owner-or-admin)

```bash
curl -s -X DELETE "$OPENBEAVS_BASE_URL/api/v1/agents/$AGENT_ID" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN"
```

## Users — `/api/v1/users`

Source: `front/backend/open_webui/routers/users.py`.

### GET /api/v1/users/ (admin)

Pagination via `?skip=&limit=`. Returns `List[UserModel]`.

Per-row fields:

| Field               | Type        | Meaning                                                            |
|---------------------|-------------|--------------------------------------------------------------------|
| `id`                | str (uuid)  | Stable user ID; use in `/update/role` and `/{id}/update`.          |
| `email`             | str         | Lowercased on insert. Login key.                                   |
| `name`              | str         | Display name.                                                      |
| `role`              | str         | `"pending"` (signup queued, no access), `"user"`, or `"admin"`.    |
| `profile_image_url` | str         | Avatar URL; `/user.png` is the default fallback.                   |
| `last_active_at`    | int \| null | Unix epoch seconds of last token verification.                     |
| `created_at`        | int         | Unix epoch seconds.                                                |
| `updated_at`        | int         | Unix epoch seconds.                                                |
| `api_key`           | str \| null | Set if the user generated a personal API key via `/api/v1/auths/api_key`. |
| `settings`          | dict \| null | Per-user UI preferences blob.                                     |
| `info`              | dict \| null | Free-form admin notes.                                            |

```bash
curl -fsS "$OPENBEAVS_BASE_URL/api/v1/users/?limit=200" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  | jq '.[] | {id,email,role,last_active_at}'
```

`role == "pending"` is the most common gotcha — new signups are queued
in this state until an admin promotes them via `/update/role`. They
can sign in but can't read any resource.

### POST /api/v1/users/update/role (admin)

Body: `{ "id": str, "role": "pending" | "user" | "admin" }`. Note the
hub refuses to demote the first-ever user (the bootstrap admin).

```bash
curl -s -X POST "$OPENBEAVS_BASE_URL/api/v1/users/update/role" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"id":"<user-id>","role":"admin"}' | jq
```

### POST /api/v1/users/{user_id}/update (admin) — destructive

Body: `UserUpdateForm = { name, email, profile_image_url, password? }`.
Overwrites all four fields; pass current values for ones you don't want
to change.

### DELETE /api/v1/users/{user_id} (admin) — destructive

## Models — `/api/v1/models`

Source: `front/backend/open_webui/routers/models.py`. Note the per-model
endpoints take `id` as a **query parameter**, not a path component, so
slashes in IDs (`anthropic/Codex-3-sonnet`) work.

### GET /api/v1/models/ (verified, role-aware)

Returns models the caller can see (`List[ModelUserResponse]`).

### GET /api/v1/models/base (admin)

Foundation models registered with the hub.

### POST /api/v1/models/create (verified, needs `workspace.models` perm)

Body: `ModelForm`. Creates a model row.

### POST /api/v1/models/model/toggle?id=... (verified)

Flips `is_active` on the named model. Idempotent-ish.

```bash
curl -s -X POST "$OPENBEAVS_BASE_URL/api/v1/models/model/toggle?id=$MODEL_ID" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" | jq
```

### DELETE /api/v1/models/model/delete?id=... (verified)

Removes one model.

### DELETE /api/v1/models/delete/all (admin) — destructive, irreversible

Purges every model row on the hub. Always confirm before issuing this.

## Registry — `/api/v1/registry`

Source: `front/backend/open_webui/routers/registry.py`. The registry is
the **public marketplace** — separate from the local agents table. An
agent can exist in `agent` (installed here) without being in
`registry_agent`, and vice versa.

- `GET /api/v1/registry/` — list cards visible to the caller.
- `POST /api/v1/registry/` — submit by URL (form `SubmitRegistryAgentForm`).
- `PATCH /api/v1/registry/{id}` — update a card.
- `DELETE /api/v1/registry/{id}` — destructive; remove from marketplace.

## Health

These endpoints are mounted at the root, NOT under `/api/v1`:

- `GET /health` → `{ "status": true }`. Public, no auth.
- `GET /health/db` → DB connectivity check. Public.
- `GET /api/version` → `{ "version": str }`. Public.

```bash
curl -fs "$OPENBEAVS_BASE_URL/health" >/dev/null \
  && curl -fs "$OPENBEAVS_BASE_URL/health/db" >/dev/null \
  && curl -fs "$OPENBEAVS_BASE_URL/api/version" \
  || echo 'hub unhealthy'
```

## Common workflows

### 1. List every agent, including inactive

```bash
curl -s "$OPENBEAVS_BASE_URL/api/v1/agents/all" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  | jq '.[] | {id,name,is_active,deployment_mode,deployment_status,model}'
```

### 2. Deploy an internal-mode agent and verify it's reachable

```bash
NEW=$(curl -s -X POST "$OPENBEAVS_BASE_URL/api/v1/agents/deploy" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"name":"CloudBot","description":"demo","system_prompt":"answer briefly","provider":"anthropic"}')
ID=$(echo "$NEW" | jq -r .id)
echo "deployed $ID"
curl -s "$OPENBEAVS_BASE_URL/api/v1/agents/$ID" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  | jq '{id,name,deployment_mode,deployment_status}'
```

For internal-mode agents, the hub also exposes the discovery card at
`GET /api/v1/agents/{id}/internal-a2a/.well-known/agent.json` (public)
which is useful for proving the in-process route is wired up.

### 3. Promote a user to admin by email

```bash
ID=$(curl -s "$OPENBEAVS_BASE_URL/api/v1/users/?limit=200" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  | jq -r '.[] | select(.email == "kimminsu@oregonstate.edu") | .id')
[ -n "$ID" ] || { echo "user not found"; exit 1; }
curl -s -X POST "$OPENBEAVS_BASE_URL/api/v1/users/update/role" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "$(jq -nc --arg id "$ID" '{id:$id,role:"admin"}')" | jq
```

### 4. Mint a service-account bearer for CI

```bash
read -rsp 'password for new account: ' P && echo
curl -s -X POST "$OPENBEAVS_BASE_URL/api/v1/auths/add" \
  -H "Authorization: Bearer $OPENBEAVS_ADMIN_TOKEN" \
  -H 'Content-Type: application/json' \
  -d "$(jq -nc --arg p "$P" '{name:"CI Bot",email:"ci-bot@example.com",password:$p,role:"user"}')" \
  | jq -r .token
unset P
```

The output is the bearer for the new account. It is the only copy.

### 5. Health check the hub

See the curl block in the Health section above. Wrap in CI as the smoke
check after every deploy.

## Safety rules

Confirm with the user before running ANY of these:

- `DELETE /api/v1/agents/{id}` — removes a deployed agent.
- `DELETE /api/v1/users/{id}` — removes a user account.
- `POST /api/v1/users/{user_id}/update` — overwrites name/email/password
  in one call; easy to clobber data.
- `DELETE /api/v1/models/delete/all` — purges every model row.
- `DELETE /api/v1/registry/{id}` — removes a marketplace card.
- `POST /api/v1/auths/add` — mints a token; the new token is the only
  copy and must be handled like a secret.
- `POST /api/v1/agents/deploy` against prod with `deploy_to_cloud_run:true`
  — has shared-infra side effects and costs money.

Reads (`GET`) and idempotent toggles do NOT need confirmation.

## Routes intentionally NOT documented here

These exist but are out of scope for admin operations — point the user
at the routers if they ask:

- `front/backend/open_webui/routers/chats.py` (chat history) — UI-driven.
- `front/backend/open_webui/routers/files.py`, `knowledge.py` — multipart
  uploads / RAG; awkward via curl.
- `front/backend/open_webui/routers/ollama.py`, `openai.py` — LLM
  proxies; the chat path uses these internally.
- `tools.py`, `prompts.py`, `tasks.py`, `memories.py`, `folders.py`,
  `groups.py`, `channels.py`, `functions.py`, `pipelines.py`,
  `images.py`, `audio.py`, `retrieval.py`, `embed.py`, `tickets.py`,
  `configs.py`, `utils.py` — all under `/api/v1/<name>`; survey those
  files directly if you need them.

## When this skill is wrong

Routes drift. If a curl here returns 404 or 422, open the router file
referenced in that section and trust the source. Then edit this skill
to match — leaving stale docs is worse than no docs.
