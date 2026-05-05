"""add chat encryption fields

Revision ID: a1b2c3d4e5f6
Revises: ca81bd47c050
Create Date: 2026-04-09

Adds per-user envelope encryption columns to the chat table and a key_ref
column to the user table, as specified in §1 and §5 of the OpenBeavs Chat
Privacy Architecture document.

New columns on `chat`:
  - key_ref      TEXT        — KMS resource path for the user's wrapping key
  - encrypted_dek BYTEA      — DEK wrapped by the user's KMS key
  - content_enc  BYTEA       — AES-256-GCM ciphertext of the chat JSON
  - session_type VARCHAR     — 'authenticated' | 'guest' | 'a2a'
  - expires_at   BIGINT      — epoch TTL for guest chats; NULL for authenticated
  - key_version  VARCHAR     — KMS key version used, for re-encryption tracking

New column on `user`:
  - key_ref      TEXT        — KMS resource path for this user's wrapping key
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "3781e22d8b01"
branch_labels = None
depends_on = None


def upgrade():
    # ---- chat table -------------------------------------------------------
    with op.batch_alter_table("chat", schema=None) as batch_op:
        batch_op.add_column(sa.Column("key_ref", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("encrypted_dek", sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column("content_enc", sa.LargeBinary(), nullable=True))
        batch_op.add_column(sa.Column("session_type", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("expires_at", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("key_version", sa.String(), nullable=True))

    # ---- user table -------------------------------------------------------
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("key_ref", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("key_ref")

    with op.batch_alter_table("chat", schema=None) as batch_op:
        batch_op.drop_column("key_version")
        batch_op.drop_column("expires_at")
        batch_op.drop_column("session_type")
        batch_op.drop_column("content_enc")
        batch_op.drop_column("encrypted_dek")
        batch_op.drop_column("key_ref")
