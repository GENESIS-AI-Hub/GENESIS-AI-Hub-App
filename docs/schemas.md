# Database Schemas

> **Note:** This ER diagram reflects the initial target schema. The production implementation builds on top of the existing Open WebUI schema (Peewee/SQLite in `front/backend/open_webui/models/`). Custom tables added by this project are in `agents.py`, `registry.py`, and `tickets.py` within that directory. The entities below map to those tables conceptually, though column names and relationships may differ in the actual Peewee models.

## Entity Relationships

- **ChatDB** — one chat session per user, linked to a sequence of messages
- **MessagesDB** — individual messages within a chat, attributed to a user or agent
- **AgentDB** — registered agents (mirrors `AgentModel` in `models/agents.py`)
- **Bucket** — file uploads attached to chat sessions (GCS-backed in production)

```mermaid
erDiagram
    %% ENTITIES
    ChatDB {
        INT Chat_ID PK
        VARCHAR ChatTitle
        VARCHAR User_ONID FK
        INT Last_Message_ID FK
        TIMESTAMP Created_At
    }

    MessagesDB {
        INT Message_ID PK
        INT Chat_Session FK
        ENUM Sender_Type "user | agent"
        VARCHAR Content_Text
        VARCHAR File_Location_URL
        TIMESTAMP Sent_At
        BOOLEAN Is_Flagged
    }

    AgentDB {
        INT Agent_ID PK
        VARCHAR AgentName
        VARCHAR AgentCardURL "URL to hosted agent description"
        ENUM Scope "Global | Departmental | Private"
        BOOLEAN Is_Public "True = No Auth Required"
        VARCHAR Endpoint_URL "The backend service routing URL"
        VARCHAR Description
    }

    Bucket {
        VARCHAR File_Location_URL PK
        VARCHAR Original_Filename
        VARCHAR Mime_Type
        TIMESTAMP Uploaded_At
        VARCHAR Uploader_ONID FK
    }

    %% RELATIONSHIPS
    ChatDB ||--o{ MessagesDB : has
    MessagesDB ||--|| Bucket : references_file
    AgentDB ||--o{ MessagesDB : uses_agent
    ChatDB ||--|| User : created_by

```
