# Open WebUI 👋

**Open WebUI is an [extensible](https://docs.openwebui.com/features/plugin/), feature-rich, and user-friendly self-hosted AI platform designed to operate entirely offline.** It supports various LLM runners like **Ollama** and **OpenAI-compatible APIs**, with **built-in inference engine** for RAG, making it a **powerful AI deployment solution**.

![Open WebUI Demo](./demo.gif)

## Table of Contents
- [About This Fork](#about-this-fork)
- [Prerequisites](#prerequisites)
- [Part 1: Install Miniforge (Conda)](#part-1-install-miniforge-conda)
- [Part 2: Install NVM (Node Version Manager)](#part-2-install-nvm-node-version-manager)
- [Part 3: Clone the Repository](#part-3-clone-the-repository)
- [Part 4: Build and Run Open WebUI](#part-4-build-and-run-open-webui)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Debranding Guide](#debranding-guide)
- [Version Information](#version-information)
- [Legal and Attribution](#legal-and-attribution)
- [License](#license )

---

## About This Fork

This repository is a customized fork of [Open WebUI](https://github.com/open-webui/open-webui) based on **version 0.6.5** (commit: `07d8460126a686de9a99e2662d06106e22c3f6b6`).

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

### On Windows (WSL2):

```bash
curl -L -O "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
bash Miniforge3-Linux-x86_64.sh
```

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

## Part 4: Build and Run Open WebUI

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

### Step 2: Build the Frontend

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

# Build the frontend (this compiles it into static files)
npm run build
```

This creates an optimized production build in the `build/` directory.

### Step 3: Copy Built Frontend to Backend

```bash
# Copy the built frontend to the backend's static directory
cp -r build backend/static

# Verify the files were copied
ls -la backend/static/
```

### Step 4: Start the Backend Server

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

### Step 5: Access Open WebUI

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

# Rebuild the frontend
npm run build

# Copy the new build to backend
cp -r build backend/static

# The backend will automatically detect changes if dev.sh is running
```

### Stopping the Server:

In the terminal running the backend, press `Ctrl+C`

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

---

## License

This project is licensed under the [MIT License](./LICENSE).
Portions of this work retain the original Open WebUI BSD 3-Clause License terms.

- Portions of this project are derived from the Open WebUI source code and remain covered by the original BSD 3-Clause License.
- Modifications, additions, and new files authored by Oregon State University are provided under the MIT License.
- The full license terms are available in the [LICENSE](./LICENSE) file.
- Neither the name “Open WebUI” nor the names of its original contributors may be used to endorse or promote derivative products.

By using this codebase, you agree to comply with the licensing conditions specified in both the upstream Open WebUI BSD 3-Clause License and the MIT License governing this fork.
