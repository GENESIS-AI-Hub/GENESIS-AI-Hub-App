# GENESIS-AI-Hub

OSU GENESIS AI Hub for CS Capstone. Team # 043

A model for collaboration between Oregon State AI agents, utilizing context to provide users with better responses to queries.

Team Roster/Contacts:

James Smith
#: 5037138776
email: smitjam2@oregonstate.edu , galavantinggeckoguy@gmail.com
GH: gitJamoo

Minsu Kim
#: 971-297-4257
Email: kimminsu@oregonstate.edu , minsteww26@gmail.com
GH: minkim26

Rohan Thapliyal
#: 5035236168
email: thapliyr@oregonstate.edu , rohanthapliyal2020@gmail.com
GH: Rohanthap

John Sweet
#: 2135456760
email: john.sweet@oregonstate.edu
GH: jsweet8258

#eof#

## Project Structure

- `front/`: Contains the React frontend application.
- `back/`: Contains the FastAPI backend application.
- `deploy.sh`: A script to deploy both applications to Google Cloud Run.

## Prerequisites

- [Docker](https://www.docker.com/)
- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- [Node.js and npm](https://nodejs.org/)

## Local Development

### Backend

1.  Navigate to the `back` directory:
    ```bash
    cd back
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the development server:
    ```bash
    uvicorn main:app --reload
    ```
    The backend will be available at `http://localhost:8000`.

- Note: To lint, use `ruff check`

### Frontend

1.  Navigate to the `front` directory:
    ```bash
    cd front
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Run the development server:
    ```bash
    npm start
    ```
    The frontend will be available at `http://localhost:3000`.

- Note: To lint, use `npm run lint`

## Deployment

1.  **Authenticate with GCP:**

    ```bash
    gcloud auth login
    gcloud auth configure-docker
    ```

2.  **Configure the `deploy.sh` script:**

    Open `deploy.sh` and replace the following placeholder values with your GCP project ID and desired region:

    - `your-gcp-project-id`
    - `your-gcp-region`

3.  **Run the deployment script:**

    ```bash
    ./deploy.sh
    ```

    The script will build and deploy both the backend and frontend applications to Google Cloud Run. The frontend will be automatically configured to communicate with the deployed backend.
