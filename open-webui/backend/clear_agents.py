#!/usr/bin/env python3
"""
Script to clear all agents from the database.
This will delete all entries in the 'agent' table while preserving other data.
"""

import sqlite3
import os
from pathlib import Path

# Get the database path
backend_dir = Path(__file__).parent
db_path = backend_dir / "data" / "webui.db"

if not db_path.exists():
    print(f"❌ Database file not found at: {db_path}")
    print("The database may not have been created yet.")
    exit(1)

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check how many agents exist
    cursor.execute("SELECT COUNT(*) FROM agent")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("✅ No agents found in the database. Nothing to delete.")
    else:
        print(f"Found {count} agent(s) in the database.")
        
        # Delete all agents
        cursor.execute("DELETE FROM agent")
        conn.commit()
        
        print(f"✅ Successfully deleted {count} agent(s) from the database.")
        print("You can now add new agents for testing.")
        
except sqlite3.Error as e:
    print(f"❌ Database error: {e}")
    conn.rollback()
finally:
    conn.close()
