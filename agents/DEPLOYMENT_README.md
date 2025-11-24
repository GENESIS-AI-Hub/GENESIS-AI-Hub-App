# ADK Agent Deployment Guide

This guide explains how to use the universal deployment script to deploy any ADK agent to Google Cloud Platform's Agent Engine.

## Overview

The `deploy_agent.py` script is a universal deployment tool that can deploy **any** ADK agent in the `agents/` directory to GCP. It automatically:

- Detects the correct agent directory structure
- Creates GCS staging buckets if needed
- Configures deployment parameters
- Handles errors and provides detailed feedback

## Prerequisites

### 1. Google Cloud Platform Setup

**Create a GCP Project:**
```bash
gcloud projects create YOUR-PROJECT-ID
gcloud config set project YOUR-PROJECT-ID
```

**Enable Required APIs:**
```bash
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
```

**Set Up Authentication:**
```bash
# Authenticate with your Google account
gcloud auth login

# Set application default credentials
gcloud auth application-default login
```

### 2. Install Google ADK

```bash
pip install google-adk
```

Verify installation:
```bash
adk --version
```

### 3. Install gsutil

The script uses `gsutil` for GCS bucket management. It's included with the Google Cloud SDK:

```bash
# Install Google Cloud SDK if not already installed
# Visit: https://cloud.google.com/sdk/docs/install

# Verify gsutil is available
gsutil version
```

## Configuration

### Default Settings

The script uses these default values:
- **Project ID**: `genesis-hub-osu-test`
- **Region**: `us-west1`
- **Staging Bucket**: `gs://{project-id}-staging` (auto-generated)
- **Display Name**: `{agent-name}-agent` (auto-generated)

### Customizing Configuration

You can override defaults using command-line arguments (see Usage section below).

## Usage

### Basic Deployment

Deploy an agent with default settings:

```bash
cd agents
python deploy_agent.py <agent-name>
```

**Examples:**
```bash
# Deploy Oregon State expert agent
python deploy_agent.py oregon-state-expert

# Deploy Cyrano de Bergerac agent
python deploy_agent.py Cyrano-de-Bergerac
```

### Custom Project and Region

Deploy to a specific GCP project and region:

```bash
python deploy_agent.py <agent-name> --project YOUR-PROJECT-ID --region us-central1
```

**Example:**
```bash
python deploy_agent.py oregon-state-expert --project my-osu-project --region us-west2
```

### Custom Display Name

Set a custom display name for the deployed agent:

```bash
python deploy_agent.py <agent-name> --display-name "My Custom Agent Name"
```

**Example:**
```bash
python deploy_agent.py oregon-state-expert --display-name "OSU Expert Bot"
```

### Custom Staging Bucket

Specify a custom GCS staging bucket:

```bash
python deploy_agent.py <agent-name> --staging-bucket gs://my-custom-bucket
```

### All Options Combined

```bash
python deploy_agent.py oregon-state-expert \
  --project my-project \
  --region us-east1 \
  --staging-bucket gs://my-staging-bucket \
  --display-name "Oregon State Expert"
```

### Get Help

View all available options:

```bash
python deploy_agent.py --help
```

## Agent Directory Structure

The script automatically detects the deployable directory for each agent. It looks for `agent.py` in:

1. `{agent-name}/agent/` (preferred for new agents)
2. `{agent-name}/orchestrator/` (for multi-agent systems)
3. `{agent-name}/src/` (alternative structure)
4. `{agent-name}/` (root-level agent.py)

**Example structures:**

```
agents/
├── oregon-state-expert/
│   └── agent/
│       └── agent.py  ✓ Found here
│
├── Cyrano-de-Bergerac/
│   └── orchestrator/
│       └── agent.py  ✓ Found here
│
└── simple-agent/
    └── agent.py      ✓ Found here
```

## Deployment Process

When you run the deployment script, it:

1. **Validates** the agent directory exists
2. **Detects** the correct subdirectory containing `agent.py`
3. **Checks** for the staging bucket (creates if needed)
4. **Runs** `adk deploy agent_engine` with your configuration
5. **Streams** deployment output in real-time
6. **Reports** success or failure

## Troubleshooting

### Error: Agent directory not found

**Problem:** The specified agent name doesn't match any directory in `agents/`.

**Solution:** Check available agents:
```bash
ls agents/
```

Use the exact directory name (case-sensitive).

### Error: Could not find deployable directory

**Problem:** The agent directory doesn't contain `agent.py` in expected locations.

**Solution:** Ensure your agent has `agent.py` in one of these locations:
- `{agent-name}/agent/agent.py`
- `{agent-name}/orchestrator/agent.py`
- `{agent-name}/src/agent.py`
- `{agent-name}/agent.py`

### Error: 'adk' command not found

**Problem:** ADK is not installed or not in PATH.

**Solution:**
```bash
# Install ADK
pip install google-adk

# Or install with A2A support
pip install google-adk[a2a]

# Verify installation
adk --version
```

### Error: 'gsutil' command not found

**Problem:** Google Cloud SDK is not installed.

**Solution:** Install the Google Cloud SDK:
- Visit: https://cloud.google.com/sdk/docs/install
- Follow installation instructions for your OS
- Run `gcloud init` after installation

### Error: Permission denied or authentication failed

**Problem:** Not authenticated with GCP or insufficient permissions.

**Solution:**
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Verify current account
gcloud auth list

# Set the correct project
gcloud config set project YOUR-PROJECT-ID
```

### Error: Bucket creation failed

**Problem:** Insufficient permissions or bucket name conflict.

**Solution:**
```bash
# Check if you have storage.buckets.create permission
gcloud projects get-iam-policy YOUR-PROJECT-ID

# Try a different bucket name
python deploy_agent.py <agent-name> --staging-bucket gs://unique-bucket-name
```

### Deployment hangs or times out

**Problem:** Network issues or GCP service problems.

**Solution:**
- Check your internet connection
- Verify GCP services are operational: https://status.cloud.google.com/
- Try again after a few minutes
- Check GCP quotas: `gcloud compute project-info describe --project=YOUR-PROJECT-ID`

## Advanced Usage

### Deploying from a Different Directory

If you're not in the `agents/` directory:

```bash
# From project root
python agents/deploy_agent.py oregon-state-expert

# From anywhere (use absolute path)
python /path/to/agents/deploy_agent.py oregon-state-expert
```

### Environment Variables

You can set default values using environment variables:

```bash
export GCP_PROJECT_ID="my-project"
export GCP_REGION="us-central1"

# Then deploy without flags
python deploy_agent.py oregon-state-expert
```

### Scripting Deployments

Create a deployment script for multiple agents:

```bash
#!/bin/bash
# deploy_all.sh

AGENTS=("oregon-state-expert" "Cyrano-de-Bergerac")
PROJECT="my-project"
REGION="us-west1"

for agent in "${AGENTS[@]}"; do
  echo "Deploying $agent..."
  python deploy_agent.py "$agent" --project "$PROJECT" --region "$REGION"
done
```

## Post-Deployment

After successful deployment, you can:

### Test the Deployed Agent

```bash
# Use gcloud to interact with the deployed agent
gcloud ai agents describe AGENT-ID --project=YOUR-PROJECT-ID --region=YOUR-REGION
```

### View Deployment Logs

```bash
# Check Cloud Logging for agent execution logs
gcloud logging read "resource.type=aiplatform.googleapis.com/Agent" --project=YOUR-PROJECT-ID
```

### Update an Existing Agent

Simply run the deployment script again with the same agent name and project. ADK will update the existing deployment.

## Best Practices

1. **Test Locally First**: Always test your agent locally before deploying:
   ```bash
   cd agents/<agent-name>
   adk web agent
   ```

2. **Use Consistent Naming**: Keep agent directory names lowercase with hyphens for consistency.

3. **Version Control**: Commit your agent code before deploying to track changes.

4. **Monitor Costs**: GCP Agent Engine usage incurs costs. Monitor your usage in the GCP Console.

5. **Use Staging Environments**: Deploy to a test project first before production.

## Additional Resources

- [Google ADK Documentation](https://google.github.io/adk-docs/)
- [Vertex AI Agent Engine](https://cloud.google.com/vertex-ai/docs/agents)
- [GCP Authentication Guide](https://cloud.google.com/docs/authentication)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs)

## Support

For issues with:
- **This script**: Check the troubleshooting section above
- **ADK**: Visit [ADK GitHub Issues](https://github.com/google/adk-python/issues)
- **GCP**: Contact [Google Cloud Support](https://cloud.google.com/support)
