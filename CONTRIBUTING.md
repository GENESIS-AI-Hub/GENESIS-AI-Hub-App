# Contributing Guide
How to set up, code, test, review, and release so contributions meet our Definition
of Done.

## Code of Conduct
Reference the project/community behavior expectations and reporting process.

## Getting Started
List prerequisites, setup steps, environment variables/secrets handling, and how to
run the app locally.

### Prerequisites

*   [Docker](https://www.docker.com/)
*   [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
*   [Node.js and npm](https://nodejs.org/)

### Running the app Locally

#### Backend

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

#### Frontend

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

## Branching & Workflow
Describe the workflow (e.g., trunk-based or GitFlow), default branch, branch
naming, and when to rebase vs. merge.

Our workflow is GitFlow.
Default branch is `main`
Branch naming should be simple and to the point
- Examples: `agent-registration-hub-not-found-fix`, `hub-div-center-fix`
Rebase when bringing in lots of changes at once, but try to avoid. Standard procedure is merge.

## Issues & Planning
Explain how to file issues, required templates/labels, estimation, and
triage/assignment practices.

To file an issue, create a ticket in our GitHub projects (link here). You are required to provide a general estimation of the problem size using t-shirt size standard. Triage will be handled by assigning to the project member closest to the issues domain.

## Commit Messages
State the convention (e.g., Conventional Commits), include examples, and how to
reference issues.


## Code Style, Linting & Formatting
Name the formatter/linter, config file locations, and the exact commands to
check/fix locally.
@ Update

## Testing
@Nam Long Tran

## Pull Requests & Reviews
Outline PR requirements (template, checklist, size limits), reviewer expectations,
approval rules, and required status checks.

## CI/CD
Link to pipeline definitions, list mandatory jobs, how to view logs/re-run jobs,
and what must pass before merge/release.
@Rohan

## Security & Secrets
State how to report vulnerabilities, prohibited patterns (hard-coded secrets),
dependency update policy, and scanning tools.

## Documentation Expectations
Specify what must be updated (README, docs/, API refs, CHANGELOG) and
docstring/comment standards.

## Release Process
Describe versioning scheme, tagging, changelog generation, packaging/publishing
steps, and rollback process.

## Support & Contact
Provide maintainer contact channel, expected response windows, and where to ask
questions.
