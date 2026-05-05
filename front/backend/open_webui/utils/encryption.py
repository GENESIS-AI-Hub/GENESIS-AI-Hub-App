"""
Chat content encryption utility — User-Level Envelope Encryption.

Architecture (from openbeavs-chat-privacy-architecture.md §1, §7):
  - One AES-256 DEK (Data Encryption Key) per chat record.
  - DEK is wrapped (encrypted) by the user's KMS-managed key.
  - Only the wrapped DEK + ciphertext are persisted; plaintext and raw
    DEKs never touch the database.
  - Supports GCP Cloud KMS (production) and a local symmetric master
    key (development / CI when USE_GCP_KMS=false).

Environment variables:
  ENABLE_CHAT_ENCRYPTION  - "true" / "false"  (default: false)
  USE_GCP_KMS             - "true" / "false"  (default: false)
  GCP_KMS_KEY_RING        - e.g. "openbeavs-users"
  GCP_PROJECT_ID          - GCP project id
  GCP_KMS_LOCATION        - e.g. "us-west1"
  ENCRYPTION_MASTER_KEY   - 32-byte hex string used in local mode only
"""

import logging
import os
import secrets
import struct
from base64 import b64decode, b64encode
from typing import Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

log = logging.getLogger(__name__)

####################################
# Environment-level configuration
####################################

ENABLE_CHAT_ENCRYPTION: bool = (
    os.environ.get("ENABLE_CHAT_ENCRYPTION", "false").lower() == "true"
)
USE_GCP_KMS: bool = os.environ.get("USE_GCP_KMS", "false").lower() == "true"
GCP_PROJECT_ID: str = os.environ.get("GCP_PROJECT_ID", "")
GCP_KMS_LOCATION: str = os.environ.get("GCP_KMS_LOCATION", "us-west1")
GCP_KMS_KEY_RING: str = os.environ.get("GCP_KMS_KEY_RING", "openbeavs-users")

# Local dev master key — must be exactly 32 bytes (hex-encoded = 64 hex chars).
_MASTER_KEY_HEX: str = os.environ.get("ENCRYPTION_MASTER_KEY", "")

####################################
# GCP Cloud KMS helpers
####################################


def _gcp_key_path(crypto_key_id: str) -> str:
    """Build the full GCP Cloud KMS resource name for a crypto key."""
    return (
        f"projects/{GCP_PROJECT_ID}/locations/{GCP_KMS_LOCATION}"
        f"/keyRings/{GCP_KMS_KEY_RING}/cryptoKeys/{crypto_key_id}"
    )


def _gcp_wrap_dek(plaintext_dek: bytes, key_ref: str) -> bytes:
    """Wrap a DEK using GCP Cloud KMS encrypt."""
    from google.cloud import kms  # type: ignore[import-untyped]

    client = kms.KeyManagementServiceClient()
    response = client.encrypt(
        request={"name": key_ref, "plaintext": plaintext_dek}
    )
    return response.ciphertext


def _gcp_unwrap_dek(wrapped_dek: bytes, key_ref: str) -> bytes:
    """Unwrap a DEK using GCP Cloud KMS decrypt."""
    from google.cloud import kms  # type: ignore[import-untyped]

    client = kms.KeyManagementServiceClient()
    response = client.decrypt(
        request={"name": key_ref, "ciphertext": wrapped_dek}
    )
    return response.plaintext


def create_user_key_ref(user_id: str) -> str:
    """
    Provision a new per-user crypto key in GCP Cloud KMS and return its
    resource path. In local mode, returns a synthetic key reference that
    encodes the user id (the actual wrapping is done with the master key).

    Called once at account creation / first login.
    """
    if USE_GCP_KMS:
        from google.cloud import kms  # type: ignore[import-untyped]

        client = kms.KeyManagementServiceClient()
        key_ring_name = client.key_ring_path(
            GCP_PROJECT_ID, GCP_KMS_LOCATION, GCP_KMS_KEY_RING
        )
        crypto_key_id = f"user-{user_id}"
        client.create_crypto_key(
            request={
                "parent": key_ring_name,
                "crypto_key_id": crypto_key_id,
                "crypto_key": {
                    "purpose": kms.CryptoKey.CryptoKeyPurpose.ENCRYPT_DECRYPT,
                    "version_template": {
                        "algorithm": kms.CryptoKeyVersion.CryptoKeyVersionAlgorithm.GOOGLE_SYMMETRIC_ENCRYPTION,
                    },
                },
            }
        )
        return _gcp_key_path(crypto_key_id)
    else:
        # Local mode: synthetic reference; wrapping uses ENCRYPTION_MASTER_KEY.
        return f"local://users/{user_id}"


####################################
# Local-mode master-key helpers
####################################


def _local_master_key() -> bytes:
    """Return the 32-byte master key from ENCRYPTION_MASTER_KEY env var."""
    if not _MASTER_KEY_HEX:
        raise EnvironmentError(
            "ENCRYPTION_MASTER_KEY is not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    key_bytes = bytes.fromhex(_MASTER_KEY_HEX)
    if len(key_bytes) != 32:
        raise ValueError("ENCRYPTION_MASTER_KEY must be a 64-character hex string (32 bytes).")
    return key_bytes


def _local_wrap_dek(plaintext_dek: bytes) -> bytes:
    """Wrap DEK with the local master key using AES-256-GCM."""
    master_key = _local_master_key()
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(master_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext_dek, b"")
    # Prefix with nonce so we can unwrap later: [nonce(12)] + [ciphertext]
    return nonce + ciphertext


def _local_unwrap_dek(wrapped_dek: bytes) -> bytes:
    """Unwrap a DEK that was wrapped with the local master key."""
    master_key = _local_master_key()
    nonce, ct = wrapped_dek[:12], wrapped_dek[12:]
    aesgcm = AESGCM(master_key)
    return aesgcm.decrypt(nonce, ct, b"")


####################################
# Public encryption API
####################################


def wrap_dek(plaintext_dek: bytes, key_ref: str) -> bytes:
    """Wrap a DEK using either GCP KMS or local master key."""
    if USE_GCP_KMS:
        return _gcp_wrap_dek(plaintext_dek, key_ref)
    return _local_wrap_dek(plaintext_dek)


def unwrap_dek(wrapped_dek: bytes, key_ref: str) -> bytes:
    """Unwrap a DEK using either GCP KMS or local master key."""
    if USE_GCP_KMS:
        return _gcp_unwrap_dek(wrapped_dek, key_ref)
    return _local_unwrap_dek(wrapped_dek)


def encrypt_chat_content(content: dict, key_ref: str) -> Tuple[bytes, bytes]:
    """
    Encrypt chat content dict with a fresh DEK (envelope encryption).

    Returns:
        (encrypted_dek, ciphertext) both as raw bytes.
        Store encrypted_dek and ciphertext in the DB; never the plaintext DEK.
    """
    import json

    plaintext = json.dumps(content).encode("utf-8")
    dek = secrets.token_bytes(32)  # 256-bit random DEK

    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(dek)
    ciphertext = aesgcm.encrypt(nonce, plaintext, b"")
    # Prefix ciphertext with nonce: [nonce(12)] + [ciphertext]
    ciphertext_blob = nonce + ciphertext

    encrypted_dek = wrap_dek(dek, key_ref)
    return encrypted_dek, ciphertext_blob


def decrypt_chat_content(encrypted_dek: bytes, ciphertext_blob: bytes, key_ref: str) -> dict:
    """
    Decrypt chat content using envelope decryption.

    Args:
        encrypted_dek: The wrapped DEK stored in the DB.
        ciphertext_blob: The [nonce + ciphertext] blob stored in the DB.
        key_ref: The user's KMS key reference.

    Returns:
        The original chat content dict.
    """
    import json

    dek = unwrap_dek(encrypted_dek, key_ref)
    nonce, ct = ciphertext_blob[:12], ciphertext_blob[12:]
    aesgcm = AESGCM(dek)
    plaintext = aesgcm.decrypt(nonce, ct, b"")
    return json.loads(plaintext.decode("utf-8"))


####################################
# Guest ephemeral key helpers
####################################


def generate_ephemeral_key() -> Tuple[str, bytes]:
    """
    Generate a temporary key for a guest session.

    Returns:
        (key_ref, raw_key_bytes)
        key_ref is stored in the chat record.
        raw_key_bytes is sent to the client as a secure session cookie
        (HttpOnly; Secure; SameSite=Strict) — never persisted server-side.
    """
    raw_key = secrets.token_bytes(32)
    key_id = secrets.token_hex(16)
    key_ref = f"ephemeral://{key_id}"
    return key_ref, raw_key


def encrypt_with_raw_key(content: dict, raw_key: bytes) -> bytes:
    """Encrypt content with a raw 32-byte key (for guest ephemeral sessions)."""
    import json

    plaintext = json.dumps(content).encode("utf-8")
    nonce = secrets.token_bytes(12)
    aesgcm = AESGCM(raw_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, b"")
    return nonce + ciphertext


def decrypt_with_raw_key(ciphertext_blob: bytes, raw_key: bytes) -> dict:
    """Decrypt content encrypted with a raw 32-byte key."""
    import json

    nonce, ct = ciphertext_blob[:12], ciphertext_blob[12:]
    aesgcm = AESGCM(raw_key)
    plaintext = aesgcm.decrypt(nonce, ct, b"")
    return json.loads(plaintext.decode("utf-8"))
