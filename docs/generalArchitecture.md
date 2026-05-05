# General Architecture

> **Note:** This diagram was created during the initial design phase. It captures the intended data flow for authentication, chat, agent routing, and persistence. The actual implementation uses **SvelteKit** (not a generic "chat UI") and **FastAPI + Peewee/SQLite** (not generic "Node.js or Python"), but the data-flow relationships shown here are accurate. For the authoritative component breakdown, see [CLAUDE.md](../CLAUDE.md).

## Data Flow

The diagram below shows how a user request travels through the system:

1. The user authenticates via Microsoft SSO (MSAL/ONID).
2. The chat UI sends the query to the Open WebUI backend.
3. The backend looks up the target agent's endpoint from the agent registry.
4. The backend forwards the message to the agent via A2A (JSON-RPC 2.0).
5. The agent response is streamed back to the browser.
6. Chat history is persisted to the database.

```mermaid
graph LR
    subgraph User Interaction and Authentication
        A[External SSO Provider] --> B(SSO Login Request);
        B --> C{Store ONID};
        C --> D(Log User with ONID);
        D --> E{Use ONID to Load User Filter};
        C --> F[Authentication & User ONID & Details Database];
        F --> G(User Opens Chat);
    end

    subgraph Chat Service and Frontend
        G --> H[Chat Service / AI Agent Frontend];
        E --> H;
        H --> I(On Load: Check Chat History DB);
        H --> J(Agent Response);
    end

    subgraph Data and Processing
        I --> K[Chat History Database];
        K -.-> |Pulls Chat History| H;
        K[Chat History Database] --> L{Pull from Chat DB Processing Logic};
        L --> J;
        J --> M[AI Model Script / Agent ONID];
        M --> J;
    end
    
    subgraph Persistence and Storage
        K -.-> |Stores Chat ID, ONID, Messages| K[Chat History Database: Chat ID PK, ONID, Agent Name, Messages];
        J --> N[File Upload];
        N --> O[File Storage Bucket];
        O -.-> |Stored with Chat ID, Attach to Chat| K;
    end
    
    style H fill:#f9f,stroke:#333,stroke-width:2px
    style M fill:#9f9,stroke:#333,stroke-width:2px
    style K fill:#ccf,stroke:#333,stroke-width:2px
	subGraph2 --- n1
```
