"""Peewee migrations -- 024_add_agent_visibility_fields.py.

Add in-app access control and Cloud Run auth metadata to A2A agents.
"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Add visibility fields to agent rows."""

    migrator.add_fields(
        "agent",
        access_control=pw.TextField(null=True),
        cloud_run_auth_required=pw.BooleanField(default=False),
    )
    migrator.sql("UPDATE agent SET access_control = '{}' WHERE access_control IS NULL")


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Remove visibility fields from agent rows."""

    migrator.remove_fields(
        "agent",
        "access_control",
        "cloud_run_auth_required",
    )
