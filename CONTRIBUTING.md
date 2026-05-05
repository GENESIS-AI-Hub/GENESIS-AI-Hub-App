# Contributing Guide
How to set up, code, test, review, and release so contributions meet our Definition of Done.

## Code of Conduct
### 1. Our Professional Pledge

We are committed to making the **OpenBeavs** project a positive, harassment-free, and inclusive experience for everyone involved, regardless of technical background, personal identity, or level of experience.

### 2. Our Standards of Behavior

We expect all team members to adhere to the following professional standards:

* **Be Respectful and Inclusive:** Use welcoming, clear, and professional language. Be considerate of differing viewpoints, backgrounds, and experiences, especially when giving and receiving technical feedback.
* **Give Constructive Feedback:** Focus reviews and critiques on the code and the technical requirement, not on the person. Be graceful in accepting constructive criticism.
* **Demonstrate Empathy:** Recognize that your colleagues are also students balancing coursework and life. Support your teammates and help them find solutions.
* **Focus on the Project Goal:** All discussions and decisions should be focused on achieving the **Acceptance Criteria** and delivering a high-quality product for the stakeholder, **John V. Sweet**, and future OSU Faculty users.
* **Maintain Confidentiality:** Respect any information shared within the team or by the sponsor that is deemed sensitive or internal to OSU.

### 3. Unacceptable Behavior

Unacceptable behaviors include, but are not limited to:

* Harassment, discrimination, personal attacks, or exclusionary jokes.
* Trolling or intentionally disruptive behavior in meetings, code reviews, or digital channels.
* Insulting or derogatory comments targeting a person's identity or work.
* Any conduct that would be considered unprofessional or inappropriate in a typical business setting.

### 4. Conflict Resolution & Reporting Process

For issues that arise within the team, we recommend a simple escalation path:

1.  **Direct Communication (Preferred):** If you are comfortable, address the issue privately and respectfully with the person involved. Always **assume positive intent** first.
2.  **Team Escalation:** If the issue persists or you are not comfortable with direct communication, immediately raise the concern to the team's designated **Project Manager (PM)**. The PM is responsible for mediating the conflict.
3.  **Capstone Escalation (Official):** If the conflict involves the PM, or if the mediation process fails, the issue must be formally escalated according to the **CS Capstone Handbook**. This typically means contacting your faculty capstone instructor or advisor.

---

## Getting Started
List prerequisites, setup steps, environment variables/secrets handling, and how to run the app locally.

### Prerequisites

* [Docker](https://www.docker.com/)
* [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
* [Node.js and npm](https://nodejs.org/)

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

#### Frontend (OpenBeavs)

For detailed setup and development instructions for the OpenBeavs frontend, please refer to `front/README.md`.

---

## Branching & Workflow
Our workflow is GitFlow.
Default branch is `main`.
Branch naming should be simple and to the point, creating a new branch for a new feature.
* Examples: `feature/agent-registration`, `bugfix/hub-div-center`
Rebase when bringing in lots of changes at once, but try to avoid. Standard procedure is merge.
After merging a branch, close/delete the feature branch.

---

## Issues & Planning
To file an issue, create a ticket in our GitHub projects. You are required to provide a general estimation of the problem size using the t-shirt size standard. Triage will be handled by assigning the ticket to the project member closest to the issue's domain.

---

## Commit Messages
Adopting a standard convention is a great practice, especially since the **OpenBeavs** code is public. We will use a simplified version of **Conventional Commits**. This convention makes the project history clean, aids in debugging, and can even be used to automatically generate changelogs.

The simple format to follow is:

### `<type>(<scope>): <subject>`

### Core Components

| Component | Purpose | Examples |
| :--- | :--- | :--- |
| **`<type>`** (Required) | A tag that indicates *what kind* of change this is. | `feat`, `fix`, `chore`, `docs`, `style` |
| **`(<scope>)`** (Optional) | The system part that the change affects. | `(frontend)`, `(backend-registry)`, `(auth)` |
| **`<subject>`** (Required) | A short, imperative description of the change (less than 50 characters). | "add MS SSO login route", "center chat bubble text" |

### Recommended `<type>` List

| Type | When to Use |
| :--- | :--- |
| **`feat`** | A new feature for the user (e.g., implementing persistent chat history). |
| **`fix`** | A bug fix (e.g., fixing a UI button alignment). |
| **`chore`** | Routine tasks that don't change production code (e.g., updating dependencies). |
| **`docs`** | Changes to documentation (e.g., `README.md`, comments). |
| **`style`** | Code formatting changes (e.g., semicolons, white-space). |
| **`refactor`** | A change that neither fixes a bug nor adds a feature. |

### Referencing and Closing Issues

To automatically close an issue tracked on your project board or GitHub repository (e.g., Issue **#22** for RBAC), you must use one of the following keywords followed by the issue number in the commit message **body** or **footer**.

---

## Code Style, Linting & Formatting

### Front end:
For linting and formatting:
* Commands:
    * `npm run lint` - Lints frontend, types, and backend
    * `npm run lint:frontend` - Lints frontend with ESLint
    * `npm run format` - Formats code with Prettier
  
### Back end:
* Formatter: [Ruff](https://docs.astral.sh/ruff/)
* Config path: [Insert path if applicable]
* Commands:
    * `ruff check .` to lint
    * `ruff format` to format

---

## Testing

All new API routes require unit tests. All PRs must pass every test before merge.

### Backend

```bash
# Prototype backend (back/)
cd back/
pytest tests/ -v

# Production backend (front/backend/)
cd front/
pytest backend/open_webui/test/ -v
```

### Frontend

```bash
cd front/
npm run test:frontend   # Vitest unit tests
npm run cy:open         # Cypress E2E tests (interactive browser)
```

### What to Test

| Layer | Test Type | Tool | Location |
| :--- | :--- | :--- | :--- |
| Prototype backend | Unit | pytest | `back/tests/` |
| Production backend | Unit | pytest | `front/backend/open_webui/test/` |
| Frontend components | Unit | Vitest | `front/test/` |
| Full user flows | E2E | Cypress | `front/cypress/` |

Run `npm run lint` and all relevant tests locally before opening a PR. The CI pipeline will block merges on any failure.

---

## Pull Requests & Reviews

| Requirement | Details |
| :--- | :--- |
| **PR Template** | Mandatory. Must include: **Description**, **Related Issues**, **Testing Notes**, and **Screenshots/Video** (if UI). |
| **Checklist** | Items before 'Ready for Review': `[ ] Meets acceptance criteria`, `[ ] Tests pass`, `[ ] Docs updated`, `[ ] Self-reviewed`. |
| **Size Limits** | Target a maximum of **400-500 lines of code change**. Break larger changes into smaller, logical PRs. |
| **Reviewer Expectations** | Check for **functional correctness**, adherence to the **Tech Stack**, security concerns, and code style. |
| **Approval Rules** | Requires **one (1) approval** from another team member before merging to `main`. Cannot approve your own PR. |
| **Status Checks** | Required status checks: **All Unit Tests Pass** and **Code Linter/Style Check Passes**. |

---

## CI/CD
Our Continuous Integration and Continuous Deployment (CI/CD) pipeline is fully automated via Google Cloud Build, pulling from definitions in our `cloudbuild.yaml` file. 

Merging code into the `main` branch automatically triggers the deployment process. **No manual execution of local deployment scripts is required for standard releases.**

### Pipeline Execution Flow
The pipeline executes on a Google Cloud build machine within the `osu-genesis-hub` project and automatically handles deploying both the frontend and backend to Cloud Run:

1. **Pull Cache:** Pulls the previous Docker image (`openbeavs-frontend:latest`) from Google Artifact Registry to use as a layer cache, optimizing build speeds.
2. **Unified Build:** Executes a build from the repository root. This step compiles the SvelteKit frontend and bundles it alongside the Python/FastAPI backend into a **single, unified Docker container**.
3. **Push to Artifact Registry:** Tags the newly built image with the GitHub commit SHA and `latest`, then pushes it to Artifact Registry (`us-west1`).
4. **Deploy to Cloud Run:** Deploys the unified image to the Cloud Run service (`openbeavs-deploy-test`), injecting the required production environment variables.

### Mandatory Requirements for Merge
Before a PR can be merged to `main` (which triggers the automated deployment pipeline), the following conditions must be met:
* All GitHub Action status checks (Linters, Unit Tests) must pass.
* At least one approving review from a team member.

### Viewing Logs & Troubleshooting
If an automatic deployment fails, the DevOps Lead or a team member with GCP access should navigate to **Cloud Build Logs** in the Google Cloud Console. This will identify the exact point of failure (e.g., a linting error, build failure, or deployment timeout). If a rollback is necessary, it can be executed directly from the Cloud Run revisions dashboard.

---

## Security & Secrets

| Policy | Standard |
| :--- | :--- |
| **Vulnerability Reporting** | Immediately report security concerns to the team and create a **private, high-priority GitHub Issue**. |
| **Prohibited Patterns** | **NEVER hard-code secrets** (API keys, credentials) directly into the code base. |
| **Secrets Management** | All secrets must be loaded via environment variables (e.g., a `.env` file in `.gitignore` or GCP Secret Manager). |
| **Dependency Updates** | Review and update dependencies at the start of every sprint using tools like `npm audit` or Dependabot. |
| **Scanning Tools** | Implement a linter and static analysis tool to check for common security errors. |

---

## Documentation Expectations

| Artifact | Requirement |
| :--- | :--- |
| **`README.md`** | Must be updated before End of Term 1. Covers project overview, setup, dependencies, and testing. |
| **`/docs`** | Folder for long-form project documentation (Registry schema, architectural decisions, Code of Conduct). |
| **API References** | Use an automated tool (e.g., Swagger/OpenAPI) for the Back-End Routing API endpoints. |
| **`CHANGELOG.md`** | Generated using information from Conventional Commits during the release process. |
| **Docstrings** | All complex logic blocks must have clear docstrings (JSDoc/Python docstrings) explaining *what* and *why*. |

---

## Release Process

| Step | Detail |
| :--- | :--- |
| **Versioning Scheme** | Use **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`. |
| **Tagging** | Every successful deployment to production must be tagged in Git with the new version number. |
| **Changelog Generation** | Automatically generate the `CHANGELOG.md` from the commit history for each release. |
| **Packaging/Publishing** | The unified frontend/backend Docker container is built and pushed to GCP Artifact Registry via Cloud Build. |
| **Rollback Process** | Achieved by reverting the Cloud Run service to the previous stable revision via the GCP Console. |

---

## Support & Contact

| Channel | Detail |
| :--- | :--- |
| **Maintainer Contact** | Primary channel for urgent team questions and conflict resolution is the Project Manager (PM). |
| **Sponsor Contact** | For project requirements or technical specs, contact **John V. Sweet** via his Email. |
| **Response Windows** | Aim for a 4-hour response window during standard school hours for urgent team messages. |
| **Sponsor Meetings** | Prepare agenda items for Friday sprint meetings. Reserve emails for critical follow-up. |
| **Where to Ask** | **Technical:** Private team chat. **Scope:** Friday Sponsor Meeting. **Process:** CS Capstone Handbook. |
