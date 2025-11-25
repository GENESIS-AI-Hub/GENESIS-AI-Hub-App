"""Peewee migrations -- 021_add_foundational_model.py.

Add foundational_model column to registry_agent table.
"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    
    # Check if column exists first to avoid errors if running multiple times
    # Peewee migrate usually handles this but being safe
    migrator.add_fields(
        'registry_agent',
        foundational_model=pw.TextField(null=True)
    )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_fields('registry_agent', 'foundational_model')
