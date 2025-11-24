"""Peewee migrations -- 022_add_agent_image.py.

Add profile_image_url column to agent table.
"""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your migrations here."""
    
    migrator.add_fields(
        'agent',
        profile_image_url=pw.TextField(null=True)
    )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Write your rollback migrations here."""

    migrator.remove_fields('agent', 'profile_image_url')
