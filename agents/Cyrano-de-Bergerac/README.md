This project implements a simple, two-agent system named "Cyrano de Bergerac," inspired by the play of the same name. The system uses the Google Agent Development Kit (ADK) to create a conversational agent that replies to user input in a specific tone.

## The Cyrano de Bergerac System

In the play, Cyrano de Bergerac provides eloquent words to a rival, Christian de Neuvillette (Chris), so that together they might win the love of Roxane. In our system, one agent, "Cyrano," crafts responses, while another agent, "Chris," acts as the intermediary with the user.

Here's the workflow:

1.  **Chris (The Front-End Agent):** Accepts a statement or question from the user.
2.  **Tone Analysis:** Chris analyzes the input to classify its emotional tone (e.g., formal, angry, happy).
3.  **Handoff to Cyrano:** Chris passes the original message and the classified tone to the Cyrano agent.
4.  **Cyrano (The Wordsmith):** Cyrano receives the message and tone, and uses a generative model to craft a suitable reply.
5.  **Response Delivery:** The crafted reply is passed back through the system and delivered to the user.

## System Architecture

The system is built using the Google ADK and consists of three main components:

- `chris/agent.py`: This agent is responsible for the initial user interaction and tone analysis. It takes the user's text and outputs a JSON object containing the original text and the determined tone.
- `cyrano/agent.py`: This agent takes the JSON object from Chris and uses its generative model to craft a reply in the specified tone.
- `orchestrator/agent.py`: This is a `SequentialAgent` that manages the workflow, running `chris_agent` first and then passing its output to `cyrano_agent`.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <repository-url>
    cd Cyrano-de-Bergerac
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv .venv
    
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux 
    source .venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  **Create a `.env` file** in the root of the project.

2.  **Add your Gemini API key** to the `.env` file. You can obtain a key from [Google AI Studio](https://aistudio.google.com/app/apikey).

    ```
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    ```

3.  **Specify the models** to be used by the agents in the `.env` file. For example:
    ```
    CHRIS_MODEL="gemini-pro"
    CYRANO_MODEL="gemini-pro"
    ```

## Running the System

To run the Cyrano de Bergerac system, use the `adk web` command

## Running the A2A Server

To set up the A2A server, run the following command:

```bash
uvicorn orchestrator.agent:a2a_app --host localhost --port 8001
```

This will start an A2A server that allows the Cyrano de Bergerac agent system to be used by other agents. You can verify that the server is running by visiting `http://localhost:8001/.well-known/agent-card.json`, which displays the agent card and provides instructions for other agents on how to interact with it.

For more information, please refer to the [ADK A2A documentation](https://google.github.io/adk-docs/a2a/quickstart-exposing/#overview).
