# OSU Genesis AI Hub 🦫

**OSU Genesis AI Hub is an extensible, feature-rich, and user-friendly AI collaboration platform designed for Oregon State University.** It supports various LLM runners like **Ollama** and **OpenAI-compatible APIs**, with **built-in inference engine** for RAG and **A2A Agent Registry** for multi-agent collaboration.

![OSU Genesis AI Hub Demo](./demo.gif)

## Table of Contents
- [About This Fork](#about-this-fork)
- [Prerequisites](#prerequisites)
- [Part 1: Install Miniforge (Conda)](#part-1-install-miniforge-conda)
- [Part 2: Install NVM (Node Version Manager)](#part-2-install-nvm-node-version-manager)
- [Part 3: Clone the Repository](#part-3-clone-the-repository)
- [Part 4: Build and Run OSU Genesis AI Hub](#part-4-build-and-run-osu-genesis-ai-hub)
- [Development Workflow](#development-workflow)
- [A2A Protocol Integration](#a2a-protocol-integration)
- [Troubleshooting](#troubleshooting)
- [Debranding Guide](#debranding-guide)
- [Version Information](#version-information)
- [Legal and Attribution](#legal-and-attribution)
- [License](#license )

---

## About This Project

This repository is the OSU Genesis AI Hub, a customized AI platform based on Open WebUI **version 0.6.5** (commit: `07d8460126a686de9a99e2662d06106e22c3f6b6`), specifically designed for Oregon State University's AI collaboration needs.

### Repository Optimization

This fork has been minimized to reduce repository size and remove unnecessary artifacts:

**Size Reduction**: ~2.7GB → ~619MB (77% reduction)

#### What Was Removed:

- ✅ **Build Artifacts** (`node_modules/`, `build/`, `backend/static/`) - Regenerated during build process
- ✅ **Runtime Data** (`backend/data/cache/`, `backend/data/uploads/`, `backend/data/vector_db/`) - Created during runtime
- ✅ **Generated Assets** (`static/assets/`, `static/pyodide/`) - Rebuilt automatically
- ✅ **Original Project Documentation** (`CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `TROUBLESHOOTING.md`) - Replaced with custom docs

#### What's Preserved:

- ✅ **Source Code** - Complete v0.6.5 codebase
- ✅ **Configuration Files** - All necessary config files
- ✅ **Dependencies Manifests** - `package.json`, `requirements.txt`
- ✅ **Build Scripts** - All build and development scripts

### Why This Approach?

This lean repository approach:
- Reduces clone time and disk space usage
- Ensures users build with current dependencies
- Prevents committing generated or user-specific files
- Makes the repository easier to customize and maintain

All removed files are automatically regenerated when you follow the build instructions below.

### Customization Ready

This fork is prepared for customization and rebranding. See [Debranding Guide](#debranding-guide) section below for details.

---

## Prerequisites

Before you begin, ensure you have:

- **Operating System**: Linux, macOS, or Windows with WSL2
- **Git**: Installed and configured

---

## Part 1: Install Miniforge (Conda)

Miniforge is a minimal installer for Conda that helps you manage Python environments and dependencies.

### On macOS/Linux:

```bash
# Download and install Miniforge
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh

# Follow the installation prompts:
# 1. Press ENTER to review the license
# 2. Type 'yes' to accept the license terms
# 3. Press ENTER to confirm the installation location (or specify custom path)
# 4. Type 'yes' when asked "Do you wish to update your shell profile to automatically initialize conda?"
```

### On Windows:

Follow the official Windows install guide [here](https://github.com/conda-forge/miniforge)

### Verify Installation:

```bash
# Close and reopen your terminal, or run:
source ~/.bashrc  # For bash users
# OR
source ~/.zshrc   # For zsh users

# Verify conda is installed
conda --version
# Expected output: conda 24.x.x or similar
```

---

## Part 2: Install NVM (Node Version Manager)

NVM allows you to install and manage multiple Node.js versions.

### Install NVM:

```bash
# Download and install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Close and reopen your terminal, or run:
source ~/.bashrc  # For bash users
# OR
source ~/.zshrc   # For zsh users

# Verify NVM is installed
nvm --version
# Expected output: 0.39.0 or similar
```

### Install Node.js 22:

```bash
# Install Node.js version 22 (required by Open WebUI)
nvm install 22

# Set Node.js 22 as the active version
nvm use 22

# Set Node.js 22 as the default version
nvm alias default 22

# Verify Node.js installation
node --version
# Expected output: v22.x.x

npm --version
# Expected output: 10.x.x or similar
```

---

## Part 3: Clone the Forked Repository

### Fork and Clone:

1. Go to Open WebUI forked copy on GitHub: `https://github.com/minkim26/open-webui`
2. Copy the clone URL

```bash
# Clone the forked repository
git clone https://github.com/minkim26/open-webui.git

# Navigate into the repository
cd open-webui

# Verify you're on the main branch
git branch --show-current
# Expected output: main

# If not on the main branch, switch to it:
git checkout main
```

---

## Part 4: Build and Run OSU Genesis AI Hub

### Step 1: Set Up Python Environment

```bash
# Navigate to the backend directory
cd backend

# Create a new Conda environment with Python 3.11
conda create --name open-webui python=3.11

# When prompted "Proceed ([y]/n)?", type: y

# Activate the environment
conda activate open-webui

# Your terminal prompt should now show: (open-webui)

# Install Python dependencies
pip install -r requirements.txt -U

# This will take several minutes...
```

### Step 2: Build and Copy Frontend

```bash
# Navigate back to the project root
cd ..

# Ensure you're using Node.js 22
nvm use 22

# Copy the environment file
cp -RPp .env.example .env

# Install frontend dependencies
npm install

# If you encounter errors, try:
npm install --force

# Build the frontend and copy to backend
npm run build:copy
```

This creates an optimized production build and copies it to the `backend/static` directory.
```

### Step 3: Start the Backend Server

```bash
# Navigate to the backend directory
cd backend

# Make sure your conda environment is activated
conda activate open-webui

# Start the backend development server
sh dev.sh
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 4: Access Open WebUI

Open your web browser and navigate to:

**http://localhost:8080**

You should see the Open WebUI interface! 🎉

**API Documentation is available at:**

**http://localhost:8080/docs**

---

## Development Workflow

### Starting Open WebUI:

```bash
# Terminal 1: Navigate to backend and start server
cd ~/open-webui/backend
conda activate open-webui
sh dev.sh

# Access at: http://localhost:8080
```

### Making Frontend Changes:

When you modify frontend code, you need to rebuild:

```bash
# Terminal 2: Navigate to project root
cd ~/open-webui

# Ensure you're using Node 22
nvm use 22

# Rebuild the frontend and copy to backend
npm run build:copy

# The backend will automatically detect changes if dev.sh is running
```

### Stopping the Server:

In the terminal running the backend, press `Ctrl+C`

---

## A2A Protocol Integration

This Open WebUI fork now includes full **Agent-to-Agent (A2A) Protocol** support, allowing it to discover, register, and communicate with external AI agents using JSON-RPC 2.0.

### A2A Documentation

- **[A2A Quick Start Guide](./A2A_QUICKSTART.md)** - Step-by-step user guide with examples
- **[A2A Implementation Summary](./A2A_IMPLEMENTATION_SUMMARY.md)** - Complete technical documentation for developers
- **[A2A Code Changes](./A2A_CODE_CHANGES.md)** - Detailed list of all code modifications

### What is A2A Protocol?

The A2A protocol enables AI agents to:
- **Discover** each other through `.well-known/agent.json` endpoints
- **Communicate** using standardized JSON-RPC 2.0 messaging

### Architecture Overview

```
┌─────────────────────────────────────┐
│   Open WebUI (Port 8080)            │
│   - A2A Hub & Agent                 │
│   - Manages registered agents       │
│   - Routes messages                 │
└──────────────┬──────────────────────┘
               │ A2A Protocol
               │ (JSON-RPC 2.0)
               │
┌──────────────┴──────────────────────┐
│   GENESIS AI Hub (Port 8000)        │
│   - A2A Backend Server              │
│   - Agent Registry                  │
│   - Chat Management                 │
└─────────────────────────────────────┘
```

### A2A Features Implemented
- **Agent Discovery**: `.well-known/agent.json` endpoint 
- **Agent Registry**: Full CRUD operations for agents
- **JSON-RPC 2.0**: Standard messaging protocol
- **REST API**: `/api/v1/agents` endpoints for management
- **Database Persistence**: Agents stored in SQLite
- **Agent Communication**: Send messages to registered agents

### A2A Agent Registry (New!)
The **Agent Registry** allows users to discover, share, and install A2A agents from a decentralized list.
- **Workspace Integration**: Manage agents directly from the "Workspace" -> "Agents" tab.
- **Decentralized**: Submit any publicly hosted A2A agent (via URL).
- **Access Control**: Scope agents to specific users or groups (Public/Private).
- **Foundational Models**: Specify which model powers the agent.
- **One-Click Install**: Add agents to your chat model list with a single click.

---

### Setup: Running Both Services

To test the A2A protocol integration, you need to run both Open WebUI and the GENESIS AI Hub backend.

#### Terminal 1: Start Open WebUI (A2A Hub)

```bash
# Navigate to open-webui backend
cd /GENESIS-AI-Hub-App/open-webui/backend

# Activate conda environment
conda activate open-webui

# Start the server
sh dev.sh

# Expected output:
# INFO: Uvicorn running on http://0.0.0.0:8080
```

**Open WebUI will be available at:**
- Web Interface: http://localhost:8080
- API Docs: http://localhost:8080/docs
- A2A Discovery: http://localhost:8080/.well-known/agent.json

#### Terminal 2: Start GENESIS AI Hub Backend (A2A Server)

```bash
# Navigate to the main backend directory
cd /GENESIS-AI-Hub-App/back

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --reload --port 8000

# Expected output:
# INFO: Uvicorn running on http://0.0.0.0:8000
```

**GENESIS AI Hub will be available at:**
- API Root: http://localhost:8000
- A2A Discovery: http://localhost:8000/.well-known/agent.json
- API Docs: http://localhost:8000/docs

---

### Using A2A Agents in the Chat Interface

Once you've set up your A2A agent connections (see below), you can use them directly in the Open WebUI chat interface just like any other LLM model.

#### Automated Testing

A comprehensive test script is provided to verify your A2A setup:

```bash
# Navigate to the project root
cd /GENESIS-AI-Hub-App/open-webui

# Activate your conda environment
conda activate open-webui

# Run the test script
python test_a2a_integration.py \
  --agent-url http://localhost:8001 \
  --openwebui-url http://localhost:8080 \
  --api-key YOUR_API_KEY_HERE \
  --agent-name "Cyrano de Bergerac"
```

**Expected Output:**
```
============================================================
A2A Integration Test Suite
============================================================

✓ Open WebUI is running (version: 0.6.5)
✓ Agent discovery endpoint accessible
✓ A2A configuration API is accessible
✓ Agent registered successfully (or already registered)
✓ Found N A2A agent model(s) in models list
✓ Successfully received response from agent

============================================================
Test Suite Complete
============================================================

✓ All critical tests passed!
```

The test script will:
1. Verify Open WebUI is running
2. Test agent discovery (`.well-known/agent.json`)
3. Check A2A configuration API access
4. Register the agent with Open WebUI
5. Verify agent appears in models list
6. Test chat completion with the agent

**To get your API key:**
1. Open http://localhost:8080 in your browser
2. Log in or create an account
3. Click your profile → **Settings** → **Account**
4. Scroll to **API Key** section and copy your key

#### Quick Start: Adding an A2A Agent

1. **Start Open WebUI and log in** at http://localhost:8080

2. **Navigate to Admin Settings:**
   - Click your profile icon in the top-right
   - Select **Settings**
   - Go to **Admin Settings** (admin access required)
   - Click on the **Connections** tab

3. **Enable A2A Agents:**
   - Scroll down to the **A2A Agents** section
   - Toggle the switch to enable A2A agents
   - Click the **+** button to add a new agent connection

4. **Add Your Agent:**
   - **Agent URL**: Enter your agent's URL (e.g., `localhost:8001` or `http://localhost:8001`)
   - **Agent Name**: (Optional) Give it a friendly name, or leave blank to auto-fill from agent discovery
   - Click the **Verify Connection** button (↻ icon) to test the connection
   - If successful, you'll see a green checkmark ✓

5. **Save Your Changes:**
   - Click **Save** at the bottom of the Connections page
   - The agent will now appear in your model selector!

#### Using A2A Agents in Chat

1. **Start a New Chat:**
   - Go back to the main chat interface
   - Click the **New Chat** button

2. **Select Your Agent:**
   - Click the model selector dropdown (top of chat)
   - Look for your agent in the list (it will have tags like `agent` and `a2a`)
   - Select the agent model

3. **Chat with Your Agent:**
   - Type your message and press Enter
   - The agent will process your message using its custom logic

#### Troubleshooting Agent Connections

**"Failed to verify agent connection"**
- Ensure the agent server is running at the specified URL
- Check that the agent exposes `/.well-known/agent.json` endpoint
- For localhost, Open WebUI automatically tries both HTTP and HTTPS
- For remote agents, ensure they use HTTPS with valid certificates

**"Agent not appearing in model list"**
- Make sure you clicked **Save** in the Connections settings
- Verify the agent connection has a green checkmark (verified)
- Refresh the page to reload the model list
- Check that A2A Agents are enabled (toggle is ON)
- Check backend logs for `[MODELS]` entries confirming agent was added

**"Agent returns error in chat"**
- Check the agent server logs for error details
- Verify the agent correctly implements JSON-RPC 2.0 protocol
- Ensure the agent returns responses in the expected A2A format

---

### Database Schema

The A2A integration adds an `agent` table to Open WebUI's database:

```sql
CREATE TABLE agent (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    endpoint TEXT,
    url TEXT,
    version TEXT,
    capabilities JSON,
    skills JSON,
    default_input_modes JSON,
    default_output_modes JSON,
    input_schema JSON,
    output_schema JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    user_id TEXT
);
```

The migration runs automatically when you start Open WebUI for the first time after integration.

---

### A2A Implementation Details

**How It Works:**

```
1. User adds agent in Settings → Connections
   ↓
2. POST /api/v1/configs/a2a_agents saves config
   ↓
3. Backend fetches /.well-known/agent.json
   ↓
4. Agent registered in database (agents table)
   ↓
5. Models cache refreshed (includes A2A agents)
   ↓
6. Agent appears in chat model dropdown
   ↓
7. User selects agent and sends message
   ↓
8. Backend routes to generate_a2a_agent_chat_completion()
   ↓
9. JSON-RPC 2.0 message sent to agent endpoint
   ↓
10. Agent response parsed and returned to user
```

**For Developers:**

See [A2A_IMPLEMENTATION_SUMMARY.md](./A2A_IMPLEMENTATION_SUMMARY.md) for complete technical details including:
- Architecture overview
- All code changes with explanations
- Bug fixes and solutions
- Performance considerations
- Security recommendations
- Future enhancements roadmap

---

### Database Inspection

To view registered agents directly in the database:

```bash
# Navigate to the backend data directory
cd /GENESIS-AI-Hub-App/open-webui/backend/open_webui/data

# Open the database
sqlite3 webui.db

# View all agents
SELECT id, name, endpoint, is_active, created_at FROM agent;

# View agent details
SELECT * FROM agent WHERE name LIKE '%Cyrano%';

# Count active agents
SELECT COUNT(*) FROM agent WHERE is_active = 1;

# Exit
.quit
```

**Useful Queries:**

```sql
-- Find agents by endpoint
SELECT * FROM agent WHERE endpoint = 'http://localhost:8001';

-- Show inactive agents
SELECT name, endpoint, updated_at FROM agent WHERE is_active = 0;

-- Delete a specific agent
DELETE FROM agent WHERE id = 'agent-uuid-here';
```

---

## Troubleshooting

### "conda: command not found"

```bash
# Reinitialize your shell
source ~/.bashrc  # For bash
# OR
source ~/.zshrc   # For zsh

# If still not working, manually add to your profile:
echo 'export PATH="$HOME/miniforge3/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "nvm: command not found"

```bash
# Add NVM to your shell profile manually
echo 'export NVM_DIR="$HOME/.nvm"' >> ~/.bashrc
echo '[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"' >> ~/.bashrc
source ~/.bashrc
```

### "Open WebUI Backend Required" Error

This means the frontend isn't being served from the backend. Solution:

```bash
# Rebuild and copy frontend
cd ~/open-webui
npm run build
cp -r build backend/static

# Restart backend
cd backend
conda activate open-webui
sh dev.sh

# Access at http://localhost:8080 (NOT 5173)
```

### Backend Won't Start

```bash
# Check if port 8080 is already in use
lsof -i :8080

# If something is using it, kill that process:
kill -9 <PID>

# Try starting the backend again
```

### Python Dependencies Installation Fails

```bash
# Recreate the conda environment
conda deactivate
conda remove --name open-webui --all
conda create --name open-webui python=3.11
conda activate open-webui
pip install -r requirements.txt -U
```

### Frontend Build Fails

```bash
# Clear npm cache and node_modules
rm -rf node_modules package-lock.json
npm cache clean --force

# Reinstall dependencies
npm install --force

# Try building again
npm run build
```

### Browser Shows Blank Page

```bash
# Check if static files exist
ls -la backend/static/

# If empty, rebuild and copy:
cd ~/open-webui
npm run build
cp -r build backend/static

# Clear browser cache and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
```

---

## Debranding Guide

For future plans to rebrand this fork, modify the following:

1. **README.md** - Update all "Open WebUI" references
2. **package.json** - Change `"name": "open-webui"` to your project name
3. **backend/open_webui/env.py** - Update:
   ```python
   WEBUI_NAME = "Your Project Name"
   WEBUI_FAVICON_URL = "your-favicon-url"
   ```
4. **backend/open_webui/main.py** - Update repository references
5. **Translation files** (`src/lib/i18n/locales/`) - Contains "Open WebUI" text
6. **Configuration files** - Service names and references
7. **Docker files** - Customize for your branding
8. **INSTALLATION.md** - Update installation instructions

### Recommended Approach:

```bash
# Search for all "Open WebUI" references
grep -r "Open WebUI" . --exclude-dir={node_modules,build,backend/static}

# Search for "open-webui" references
grep -r "open-webui" . --exclude-dir={node_modules,build,backend/static}

# Update incrementally and test after each major change
```

---

## Version Information

- **Open WebUI Version**: v0.6.5
- **Commit SHA**: `07d8460126a686de9a99e2662d06106e22c3f6b6`
- **Python Version**: 3.11+
- **Node.js Version**: 22+

---

## Legal and Attribution

This repository is a customized fork of the original [Open WebUI](https://github.com/open-webui/open-webui) project © 2023–2025 Timothy Jaeryang Baek, originally released under the **BSD 3-Clause License**.

This fork includes modifications and rebranding by © 2025 Oregon State University, and all new contributions are licensed under the **MIT License**.

For more deatiled information about the repository, refer to the [GENESIS AI Hub documentation](../README.md).

---

## License

This project is licensed under the [MIT License](./LICENSE).
Portions of this work retain the original Open WebUI BSD 3-Clause License terms.

- Portions of this project are derived from the Open WebUI source code and remain covered by the original BSD 3-Clause License.
- Modifications, additions, and new files authored by Oregon State University are provided under the MIT License.
- The full license terms are available in the [LICENSE](./LICENSE) file.
- Neither the name “Open WebUI” nor the names of its original contributors may be used to endorse or promote derivative products.

By using this codebase, you agree to comply with the licensing conditions specified in both the upstream Open WebUI BSD 3-Clause License and the MIT License governing this fork.
