# Chat Encryption Implementation

**Branch:** `chat-privacy`  
**Reference:** `database/openbeavs-chat-privacy-architecture.md` §1, §5, §7

---

## Overview

OpenBeavs implements **user-level AES-256 envelope encryption** for chat content stored in the PostgreSQL database. Each authenticated user is assigned a unique encryption key reference (stored in a KMS). All chat records for that user are encrypted at rest — plaintext content is never persisted to the database.

This is a **feature-flagged** implementation: encryption is off by default and enabled via the `ENABLE_CHAT_ENCRYPTION` environment variable, allowing gradual rollout without breaking existing deployments.

---

## Architecture: Envelope Encryption

Envelope encryption uses two layers of keys:

```
Chat content (JSON)
       │
       ▼
  AES-256-GCM (DEK — random per-chat 32-byte key)
       │
       ▼
  Encrypted ciphertext  ──────────────────────► stored in DB (content_enc)
  
  DEK
       │
       ▼
  AES-256-GCM (user's KMS-managed wrapping key)
       │
       ▼
  Encrypted DEK ───────────────────────────────► stored in DB (encrypted_dek)
  
  KMS key reference (path, not the key itself) ► stored in DB (key_ref)
```

The raw keys never touch the database. Only the wrapped DEK and ciphertext are persisted.

---

## Files Changed

### New Files

| File | Purpose |
|------|---------|
| `front/backend/open_webui/utils/encryption.py` | Core encryption utility — AES-256-GCM envelope encryption, KMS abstraction (GCP Cloud KMS + local dev fallback), guest ephemeral key helpers |
| `front/backend/open_webui/migrations/versions/a1b2c3d4e5f6_add_chat_encryption_fields.py` | Alembic migration — adds 6 new columns to `chat` and 1 to `user` |

### Modified Files

| File | Change |
|------|--------|
| `front/backend/open_webui/env.py` | Added `ENABLE_CHAT_ENCRYPTION`, `USE_GCP_KMS`, `GCP_KMS_LOCATION`, `GCP_KMS_KEY_RING`, `ENCRYPTION_MASTER_KEY` environment variables |
| `front/backend/open_webui/models/users.py` | Added `key_ref` column to `User` table and `UserModel`; `insert_new_user` now provisions a KMS key on account creation when encryption is enabled |
| `front/backend/open_webui/models/chats.py` | Added 6 encryption columns to `Chat` table; `insert_new_chat` and `update_chat_by_id` transparently encrypt on write; all read methods transparently decrypt via `_decrypt_row` helper |
| `front/backend/open_webui/routers/chats.py` | `create_new_chat`, `clone_chat_by_id`, and `clone_shared_chat_by_id` now pass `user.key_ref` to `insert_new_chat` |
| `front/backend/open_webui/routers/auths.py` | `signin` lazily provisions a `key_ref` for existing users who predate the encryption feature |

---

## Database Schema Changes

### `chat` table — 6 new columns

| Column | Type | Description |
|--------|------|-------------|
| `key_ref` | TEXT | KMS resource path for the user's wrapping key. `NULL` = unencrypted row |
| `encrypted_dek` | BYTEA | The per-chat DEK, wrapped by the user's KMS key |
| `content_enc` | BYTEA | AES-256-GCM encrypted blob of the `chat` JSON field |
| `session_type` | VARCHAR | `'authenticated'` \| `'guest'` \| `'a2a'` |
| `expires_at` | BIGINT | Epoch TTL for guest chats; `NULL` for authenticated users |
| `key_version` | VARCHAR | KMS key version used; supports targeted re-encryption after rotation |

When a row is encrypted:
- `chat` column stores `{}` (empty) — no plaintext alongside ciphertext
- `content_enc` stores the AES-256-GCM ciphertext
- `encrypted_dek` stores the wrapped DEK
- `key_ref` stores the KMS path

### `user` table — 1 new column

| Column | Type | Description |
|--------|------|-------------|
| `key_ref` | TEXT | KMS resource path for this user's wrapping key; `NULL` for pre-existing users until their next login |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_CHAT_ENCRYPTION` | `false` | Master switch — enable AES-256 envelope encryption |
| `USE_GCP_KMS` | `false` | Use GCP Cloud KMS for key wrapping (production). `false` = local master key (dev/CI) |
| `GCP_KMS_LOCATION` | `us-west1` | GCP region for the KMS key ring |
| `GCP_KMS_KEY_RING` | `openbeavs-users` | KMS key ring name |
| `ENCRYPTION_MASTER_KEY` | _(none)_ | 64-char hex string (32 bytes). Required when `ENABLE_CHAT_ENCRYPTION=true` and `USE_GCP_KMS=false`. Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |

For production (GCP Cloud Run), `ENCRYPTION_MASTER_KEY` should be stored in GCP Secret Manager and injected via `--set-secrets`.

---

## Key Lifecycle

### New user (signup)
1. `Users.insert_new_user()` calls `create_user_key_ref(user_id)`
2. In GCP KMS mode: creates a new `ENCRYPT_DECRYPT` crypto key in the configured key ring
3. In local mode: returns a synthetic reference `local://users/<user_id>`
4. Reference is stored in `user.key_ref`

### Existing user (first login after encryption enabled)
1. `signin` in `auths.py` checks `user.key_ref`
2. If `NULL`, calls `create_user_key_ref` and updates `user.key_ref` via `Users.update_user_by_id`
3. Subsequent chats for this user will be encrypted

### Chat write
1. Router calls `Chats.insert_new_chat(user_id, form_data, key_ref=user.key_ref)`
2. If `ENABLE_CHAT_ENCRYPTION=true` and `key_ref` is set:
   - Generate a random 32-byte DEK
   - Encrypt chat JSON with DEK (AES-256-GCM)
   - Wrap DEK with the user's KMS key
   - Store `chat={}`, `content_enc=<ciphertext>`, `encrypted_dek=<wrapped_dek>`, `key_ref=<ref>`
3. If encryption is disabled or `key_ref` is `NULL`: store plaintext as before (backward compatible)

### Chat read
All read methods (`get_chat_by_id`, `get_chats_by_user_id`, list methods, etc.) pass the SQLAlchemy row through `_decrypt_row()`:
1. If `content_enc` and `encrypted_dek` are present: unwrap DEK → decrypt content → return plaintext dict
2. If not present: return `chat` column as-is (unencrypted rows)

This makes decryption **transparent** — callers never know whether a row was encrypted.

---

## Verification

To confirm encryption is active against the live database:

```bash
python -c "import os
from sqlalchemy import create_engine, text
engine = create_engine(os.environ['DATABASE_URL'])
with engine.connect() as conn:
    row = conn.execute(text(
        'SELECT title, chat, key_ref, content_enc IS NOT NULL as encrypted'
        ' FROM chat ORDER BY created_at DESC LIMIT 1'
    )).fetchone()
    print('title:    ', row[0])
    print('plaintext:', row[1])   # Should be {}
    print('key_ref:  ', row[2])   # Should be local://users/<id> or GCP path
    print('encrypted:', row[3])   # Should be True"
```

Expected output when working correctly:
```
title:     My Chat
plaintext: {}
key_ref:   local://users/85a20591-4b96-4fef-b7b0-6af01e831617
encrypted: True
```

---

## Production Deployment Checklist

- [ ] Generate `ENCRYPTION_MASTER_KEY` and store in GCP Secret Manager (`encryption-master-key`)
- [ ] Grant Cloud Run service account `roles/secretmanager.secretAccessor` on the secret
- [ ] Add `--set-secrets=...,ENCRYPTION_MASTER_KEY=encryption-master-key:latest` to `cloudbuild.yaml`
- [ ] Add `ENABLE_CHAT_ENCRYPTION=true` to `--set-env-vars` in `cloudbuild.yaml`
- [ ] For GCP KMS mode (when ready): set `USE_GCP_KMS=true`, provision key ring `openbeavs-users` in us-west1, grant service account `roles/cloudkms.cryptoKeyEncrypterDecrypter`
- [ ] Deploy — migration runs automatically on startup
- [ ] Run verify script to confirm `encrypted: True` on new chats

---

## Open Items

- **Guest ephemeral keys** (`generate_ephemeral_key` in `encryption.py`) are implemented but not yet wired into the guest session flow — the full guest key lifecycle (cookie delivery, promotion on login, 24h TTL purge) is a follow-on task
- **Key rotation** — `key_version` column is reserved for a future background re-encryption job
- **GCP KMS mode** — `USE_GCP_KMS=true` path requires `google-cloud-kms` package (`pip install google-cloud-kms`) and a provisioned key ring; currently using local master key mode
