# ADK Agent Deployment Guide

This guide explains how to use the universal deployment script to deploy any ADK agent to Google Cloud Platform's Agent Engine.

## Overview

The `deploy_agent.py` script is a simple wrapper around the `adk deploy agent_engine` command that:

- **Auto-detects your GCP project and region** from `gcloud config`
- **Automatically creates staging buckets** if needed
- **Works exactly like the ADK CLI** - just pass the agent name
- **Supports all platforms** (Windows, macOS, Linux)

**Simple usage:**
```bash
python deploy_agent.py <agent-name>
```

That's it! The script handles everything else automatically.

## Prerequisites

### 1. Google Cloud Platform Setup

**Authenticate and set your project:**
```bash
# Authenticate with your Google account
gcloud auth login
gcloud auth application-default login

# Set your default project
gcloud config set project YOUR-PROJECT-ID

# (Optional) Set your default region
gcloud config set compute/region us-west1
```

### 2. Install Google ADK

```bash
pip install google-adk
```

Verify installation:
```bash
adk --version
```

## Usage

### Basic Deployment

Deploy an agent with auto-detected settings:

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

The script will automatically:
- Use your project from `gcloud config get-value project`
- Use your region from `gcloud config get-value compute/region` (or default to `us-west1`)
- Create staging bucket as `gs://<project-id>-staging`
- Set display name as `<agent-name>-agent`

### Custom Configuration

Override any auto-detected values:

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

## How It Works

The deployment script:

1. **Auto-detects GCP configuration** from your `gcloud config`
2. **Constructs the ADK command** with proper parameters
3. **Runs the deployment** from the agents directory
4. **Reports success** with A2A agent card instructions

The script essentially runs:
```bash
adk deploy agent_engine <agent-name> \
  --project=<project> \
  --region=<region> \
  --staging_bucket=<bucket> \
  --display_name=<name>
```

But handles all the configuration automatically!

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
