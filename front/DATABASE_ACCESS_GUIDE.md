# Accessing the Tickets Database

This guide explains how to access and manage the tickets database where user-submitted support tickets are stored.

## Database Location

The tickets are stored in the main Open WebUI SQLite database:

```
<path-to-OpenBeavs>\front\backend\data\webui.db
```

## Method 1: Using SQLite Command Line (Recommended)

### Step 1: Install SQLite (if not already installed)

**Windows:**
1. Download SQLite tools from: https://www.sqlite.org/download.html
2. Extract the files to a folder (e.g., `C:\sqlite`)
3. Add the folder to your PATH environment variable

**Or use PowerShell:**
```powershell
winget install SQLite.SQLite
```

### Step 2: Open the Database

```powershell
# Navigate to the database directory
cd <path-to-OpenBeavs>\front\backend\data

# Open the database
sqlite3 webui.db
```

### Step 3: View All Tickets

```sql
-- View all tickets with basic info
SELECT id, name, email, issue_type, status, created_at 
FROM ticket 
ORDER BY created_at DESC;

-- View a specific ticket with full details
SELECT * FROM ticket WHERE id = 'ticket-id-here';

-- Count tickets by status
SELECT status, COUNT(*) as count 
FROM ticket 
GROUP BY status;

-- View recent tickets (last 10)
SELECT 
    substr(id, 1, 8) as short_id,
    name,
    email,
    issue_type,
    status,
    datetime(created_at, 'unixepoch') as submitted_at
FROM ticket 
ORDER BY created_at DESC 
LIMIT 10;
```

### Step 4: Update Ticket Status

```sql
-- Mark a ticket as in progress
UPDATE ticket 
SET status = 'in_progress', 
    updated_at = strftime('%s', 'now')
WHERE id = 'ticket-id-here';

-- Mark a ticket as resolved
UPDATE ticket 
SET status = 'resolved',
    resolved_at = strftime('%s', 'now'),
    updated_at = strftime('%s', 'now')
WHERE id = 'ticket-id-here';

-- Close a ticket
UPDATE ticket 
SET status = 'closed',
    updated_at = strftime('%s', 'now')
WHERE id = 'ticket-id-here';
```

### Step 5: Search Tickets

```sql
-- Search by email
SELECT * FROM ticket WHERE email LIKE '%example.com%';

-- Search by name
SELECT * FROM ticket WHERE name LIKE '%John%';

-- Search by issue type
SELECT * FROM ticket WHERE issue_type = 'bug';

-- Search by description content
SELECT * FROM ticket WHERE description LIKE '%error%';

-- View tickets from a specific user (if logged in)
SELECT * FROM ticket WHERE user_id = 'user-id-here';
```

### Step 6: Export Tickets

```sql
-- Export to CSV
.mode csv
.headers on
.output tickets_export.csv
SELECT 
    id,
    name,
    email,
    issue_type,
    description,
    status,
    datetime(created_at, 'unixepoch') as submitted_at,
    datetime(updated_at, 'unixepoch') as last_updated
FROM ticket;
.output stdout
```

### Step 7: Exit SQLite

```sql
.quit
```

## Method 2: Using DB Browser for SQLite (GUI Tool)

### Step 1: Install DB Browser

Download from: https://sqlitebrowser.org/dl/

Or use PowerShell:
```powershell
winget install DB.Browser.for.SQLite
```

### Step 2: Open the Database

1. Launch DB Browser for SQLite
2. Click "Open Database"
3. Navigate to: `<path-to-OpenBeavs>\front\backend\data\webui.db`
4. Click the "Browse Data" tab
5. Select "ticket" from the Table dropdown

### Step 3: View and Edit

- **Browse**: Use the "Browse Data" tab to view tickets
- **Filter**: Use the filter box to search
- **Edit**: Double-click any cell to edit (be careful!)
- **Execute SQL**: Use the "Execute SQL" tab for custom queries

## Method 3: Using Python Script

Create a file `view_tickets.py`:

```python
import sqlite3
import json
from datetime import datetime

# Connect to database
conn = sqlite3.connect('<path-to-OpenBeavs>/front/backend/data/webui.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all tickets
cursor.execute("""
    SELECT * FROM ticket 
    ORDER BY created_at DESC
""")

tickets = cursor.fetchall()

print(f"\\nTotal Tickets: {len(tickets)}\\n")
print("=" * 100)

for ticket in tickets:
    print(f"\\nID: {ticket['id']}")
    print(f"Name: {ticket['name']}")
    print(f"Email: {ticket['email']}")
    print(f"Type: {ticket['issue_type']}")
    print(f"Status: {ticket['status']}")
    print(f"Submitted: {datetime.fromtimestamp(ticket['created_at'])}")
    print(f"Description: {ticket['description'][:100]}...")
    
    # Parse metadata
    if ticket['metadata']:
        metadata = json.loads(ticket['metadata'])
        print(f"Browser: {metadata.get('userAgent', 'N/A')[:50]}...")
        print(f"URL: {metadata.get('currentUrl', 'N/A')}")
    
    print("-" * 100)

conn.close()
```

Run with:
```powershell
python view_tickets.py
```

## Method 4: Using the API (Admin Only)

### Get All Tickets

```bash
curl -X GET "http://localhost:8080/api/v1/tickets" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Get Ticket Statistics

```bash
curl -X GET "http://localhost:8080/api/v1/tickets/stats/summary" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Get Specific Ticket

```bash
curl -X GET "http://localhost:8080/api/v1/tickets/TICKET_ID" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Update Ticket Status

```bash
curl -X PATCH "http://localhost:8080/api/v1/tickets/TICKET_ID" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "resolved"}'
```

### Delete Ticket

```bash
curl -X DELETE "http://localhost:8080/api/v1/tickets/TICKET_ID" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Database Schema

The `ticket` table has the following structure:

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Unique ticket ID (UUID) |
| user_id | TEXT | User ID if logged in (nullable) |
| name | TEXT | Submitter's name |
| email | TEXT | Submitter's email |
| issue_type | TEXT | Type: bug, feature_request, general_feedback |
| description | TEXT | Detailed description |
| metadata | JSON | Auto-captured data (browser, URL, etc.) |
| status | TEXT | Status: new, in_progress, resolved, closed |
| created_at | INTEGER | Unix timestamp when created |
| updated_at | INTEGER | Unix timestamp when last updated |
| resolved_at | INTEGER | Unix timestamp when resolved (nullable) |

## Common Queries

### Get New Tickets

```sql
SELECT * FROM ticket WHERE status = 'new' ORDER BY created_at DESC;
```

### Get Tickets by Type

```sql
SELECT issue_type, COUNT(*) as count 
FROM ticket 
GROUP BY issue_type;
```

### Get Tickets from Last 7 Days

```sql
SELECT * FROM ticket 
WHERE created_at > strftime('%s', 'now', '-7 days')
ORDER BY created_at DESC;
```

### Get Unresolved Tickets

```sql
SELECT * FROM ticket 
WHERE status IN ('new', 'in_progress')
ORDER BY created_at ASC;
```

## Tips

1. **Backup First**: Always backup the database before making changes:
   ```powershell
   copy webui.db webui.db.backup
   ```

2. **Read-Only Mode**: Open in read-only mode to prevent accidental changes:
   ```bash
   sqlite3 -readonly webui.db
   ```

3. **Pretty Output**: Use these SQLite commands for better formatting:
   ```sql
   .mode column
   .headers on
   .width 10 20 30 15 10
   ```

4. **Timestamps**: Convert Unix timestamps to readable dates:
   ```sql
   SELECT datetime(created_at, 'unixepoch') as created FROM ticket;
   ```

## Troubleshooting

**Database is locked:**
- Make sure the backend server is stopped
- Close any other programs accessing the database

**Permission denied:**
- Run your terminal as administrator
- Check file permissions on the database file

**Table not found:**
- Make sure the backend has been started at least once (creates tables automatically)
- Check you're in the correct database file
