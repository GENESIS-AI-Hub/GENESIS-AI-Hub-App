"""add trust tier columns to agent and registry_agent

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-23

Implements the coarse access-gate model described in the OpenBeavs Chat Privacy
Architecture §4 (Three-Tier Agent Access Model).

New columns on `agent` and `registry_agent`:
  - trust_tier    VARCHAR  'public' | 'authenticated' | 'privileged'
                           Default 'public' so existing rows remain accessible.
  - required_role VARCHAR  Optional OSU role hint (student/staff/faculty).
                           Stored now, enforced once OSU OIDC lands (#141).
"""

from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("agent", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "trust_tier",
                sa.String(),
                nullable=False,
                server_default="public",
            )
        )
        batch_op.add_column(sa.Column("required_role", sa.String(), nullable=True))

    with op.batch_alter_table("registry_agent", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "trust_tier",
                sa.String(),
                nullable=False,
                server_default="public",
            )
        )
        batch_op.add_column(sa.Column("required_role", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("registry_agent", schema=None) as batch_op:
        batch_op.drop_column("required_role")
        batch_op.drop_column("trust_tier")

    with op.batch_alter_table("agent", schema=None) as batch_op:
        batch_op.drop_column("required_role")
        batch_op.drop_column("trust_tier")
