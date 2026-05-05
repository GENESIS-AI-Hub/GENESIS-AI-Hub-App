"""Peewee migrations -- 023_add_featured_agents.py.

Add is_featured column to registry_agent table for admin-curated agent showcase.
"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""

    migrator.add_fields(
        'registry_agent',
        is_featured=pw.BooleanField(default=False)
    )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_fields('registry_agent', 'is_featured')
