"""Peewee migrations -- 020_add_registry_agents.py.

Add registry_agent table for A2A Agent Registry.
"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    @migrator.create_model
    class RegistryAgent(pw.Model):
        id = pw.TextField(unique=True, primary_key=True)
        user_id = pw.TextField(null=True)
        url = pw.TextField(unique=True, null=False)
        name = pw.TextField(null=False)
        description = pw.TextField(null=True)
        image_url = pw.TextField(null=True)
        tools = pw.TextField(null=True)  # JSON field
        access_control = pw.TextField(null=True)  # JSON field
        created_at = pw.BigIntegerField(null=False)
        updated_at = pw.BigIntegerField(null=False)

        class Meta:
            table_name = "registry_agent"


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_model("registry_agent")
