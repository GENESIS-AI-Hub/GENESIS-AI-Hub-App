# Oregon State Expert Agent

This project implements an AI agent that serves as an expert on all things Oregon State University. Built using the Google Agent Development Kit (ADK), the agent uses Gemini as its base model and Google Search as a tool to provide accurate, comprehensive answers about OSU.

## Features

- **Oregon State Expertise**: Specialized knowledge about Oregon State University
- **Google Search Integration**: Real-time information retrieval for up-to-date answers
- **A2A Protocol Support**: Agent-to-Agent communication via standardized protocol
- **Gemini-Powered**: Uses Gemini 1.5 Pro for intelligent responses

## Installation

1. **Clone the repository and navigate to the agent directory:**

   ```bash
   cd agents/oregon-state-expert
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv
   
   # On Windows
   .venv\Scripts\activate
   # On macOS/Linux 
   source .venv/bin/activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. **Create a `.env` file** in the root of the project.

2. **Add your Gemini API key** to the `.env` file. You can obtain a key from [Google AI Studio](https://aistudio.google.com/app/apikey).

   ```
   GEMINI_API_KEY="YOUR_API_KEY_HERE"
   ```

3. **(Optional) Specify the model** to be used by the agent:
   ```
   OREGON_STATE_MODEL="gemini-1.5-pro-latest"
   ```

## Running the Agent Locally

To run the Oregon State expert agent with the ADK web interface:

```bash
adk web agent
```

This will start a local web server where you can interact with the agent.

## Running the A2A Server

To set up the A2A server for agent-to-agent communication:

```bash
uvicorn agent.agent:a2a_app --host localhost --port 8002
```

This will start an A2A server that allows other agents to discover and interact with the Oregon State expert. You can verify that the server is running by visiting `http://localhost:8002/.well-known/agent-card.json`, which displays the agent card.

## Example Queries

Try asking the agent questions like:

- "What is Oregon State University known for?"
- "Tell me about OSU's engineering programs"
- "What's the mascot of Oregon State?"
- "What are the school colors?"
- "Tell me about Oregon State's research programs"
- "What sports does OSU compete in?"

## Deployment to GCP

To deploy this agent to Google Cloud Platform, use the universal deployment script:

```bash
cd agents
python deploy_agent.py oregon-state-expert
```

For detailed deployment instructions, see [DEPLOYMENT_README.md](../DEPLOYMENT_README.md).

## Architecture

The agent is built using:
- **Google ADK**: Agent Development Kit for building AI agents
- **Gemini 1.5 Pro**: Large language model for natural language understanding
- **Google Search Tool**: Real-time information retrieval
- **A2A Protocol**: Standardized agent-to-agent communication

## For More Information

- [ADK Documentation](https://google.github.io/adk-docs/)
- [A2A Protocol](https://a2aprotocol.org/)
