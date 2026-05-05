# Security Policy

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

Report security concerns privately:

1. Email the team PM directly: smitjam2@oregonstate.edu
2. CC the sponsor: john.sweet@oregonstate.edu
3. Create a **private** GitHub issue (GitHub → Issues → New → check "Private")

We will acknowledge within 48 hours and aim to patch critical issues within 7 days.

---

## API Key Management

This project integrates API keys from Anthropic, OpenAI, and Google. Follow these rules without exception:

| Rule | Detail |
|------|--------|
| **Never commit `.env` files** | All `.env` files are gitignored. If you accidentally commit one, rotate the key immediately and scrub the git history. |
| **Use `.env.example` as the template** | Each agent directory has a `.env.example` — copy it to `.env` and fill in your values. |
| **Production secrets use GCP Secret Manager** | In Cloud Run, inject secrets via Secret Manager — not environment variables baked into the image. |
| **Rotate on team change** | When a team member leaves, rotate all shared API keys. |
| **Per-developer keys** | Each developer should use their own API keys for local development — do not share a single team key. |

### If a Key Is Accidentally Committed

1. **Revoke the key immediately** at the provider's dashboard (Anthropic/OpenAI/Google AI Studio).
2. Generate a new key.
3. Scrub the key from git history: `git filter-repo --path-glob '*.env' --invert-paths`
4. Force-push the cleaned history and notify all collaborators to re-clone.
5. File a private incident report to the team.

---

## Authentication

- All production endpoints require JWT authentication via `get_verified_user` or `get_admin_user` FastAPI dependencies.
- Admin endpoints additionally require `user.role == "admin"`.
- Microsoft SSO (MSAL) is the primary authentication mechanism. Local username/password is available for dev only.
- `SECRET_KEY` (JWT signing key) must be a long random string — never a short or guessable value.

---

## CORS

- The prototype backend (`back/`) uses `allow_origins=["*"]` — this is acceptable for local dev only.
- The production backend (`front/backend/open_webui/`) must restrict CORS origins to the deployed Cloud Run URL. Never copy `allow_origins=["*"]` into production code.

---

## Dependency Scanning

Run `npm audit` in `front/` at the start of every sprint. Review Dependabot alerts on the GitHub repository. Any `high` or `critical` CVE must be resolved before the next release.

---

## Known Security Considerations

| Area | Risk | Mitigation |
|------|------|-----------|
| A2A agent registration | Anyone with a hub account can register an arbitrary external URL as an agent | Validate agent card schema on registration; consider admin-approval flow for new agents |
| Prompt injection | Users may craft messages designed to hijack agent behavior | Filter inputs at the hub level; per-agent system prompts should reinforce boundaries |
| Open WebUI upstream | This project forks Open WebUI — upstream security fixes must be merged regularly | Pin Open WebUI version; track upstream releases and apply patches |
| Agent servers | Individual agent servers (`claude-agent`, etc.) use `allow_origins=["*"]` | These are intended for localhost use only; if deployed, restrict origins and add auth |
