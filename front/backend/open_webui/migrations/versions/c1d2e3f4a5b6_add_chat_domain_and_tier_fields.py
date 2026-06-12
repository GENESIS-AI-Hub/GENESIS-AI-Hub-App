"""add source_domain and agent_tier to chat table

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-06-01

Implements the domain-isolation and audit-tier requirements from the OpenBeavs
Chat Privacy Architecture §5 (Database Design Implications) and §6
(Cross-Domain Chat History).

New columns on `chat`:
  - source_domain  VARCHAR  The originating OSU domain FAB that created this
                            chat (e.g. "library.oregonstate.edu"). NULL for
                            chats created before this migration. Used to
                            enforce the default per-domain isolation policy
                            and to support opt-in cross-domain context sharing.
  - agent_tier     VARCHAR  The highest-access trust tier agent touched in
                            this conversation ('public' | 'authenticated' |
                            'privileged'). Recorded for audit logs and PII
                            scrubber job targeting. NULL = unknown (pre-migration
                            rows and chats that only use internal agents).
"""

from alembic import op
import sqlalchemy as sa

revision = "c1d2e3f4a5b6"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("chat", schema=None) as batch_op:
        batch_op.add_column(sa.Column("source_domain", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("agent_tier", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("chat", schema=None) as batch_op:
        batch_op.drop_column("agent_tier")
        batch_op.drop_column("source_domain")
