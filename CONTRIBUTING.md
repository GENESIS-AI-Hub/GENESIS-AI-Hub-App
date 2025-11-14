# Contributing Guide
How to set up, code, test, review, and release so contributions meet our Definition
of Done.

## Code of Conduct
### 1. Our Professional Pledge

We are committed to making the **OSU Genesis Hub** project a positive, harassment-free, and inclusive experience for everyone involved, regardless of technical background, personal identity, or level of experience.

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
Our workflow is GitFlow.
Default branch is `main`
Branch naming should be simple and to the point, creating a new branch for a new feature.
- Examples: `agent-registration-hub-not-found-fix`, `hub-div-center-fix`
Rebase when bringing in lots of changes at once, but try to avoid. Standard procedure is merge.
After merging a branch, close/delete feature branch.

## Issues & Planning
To file an issue, create a ticket in our GitHub projects (link here). You are required to provide a general estimation of the problem size using t-shirt size standard. Triage will be handled by assigning to the project member closest to the issues domain.

## Commit Messages
Adopting a standard convention is a great practice, especially since the **OSU Genesis Hub** code is public and will eventually move to the **DRI-GENESIS Repository**. We will use a simplified version of **Conventional Commits**. This convention makes the project history clean, aids in debugging, and can even be used to automatically generate changelogs.

The simple format to follow is:

### `<type>(<scope>): <subject>`

### Core Components

| Component | Purpose | Examples |
| :--- | :--- | :--- |
| **`<type>`** (Required) | A tag that indicates *what kind* of change this is. | `feat`, `fix`, `chore`, `docs`, `style` |
| **`(<scope>)`** (Optional) | The system part that the change affects (e.g., frontend, auth). | `(frontend)`, `(backend-registry)`, `(auth)` |
| **`<subject>`** (Required) | A short, imperative description of the change (less than 50 characters). | "add MS SSO login route", "center chat bubble text" |

---

### Recommended `<type>` List

| Type | When to Use |
| :--- | :--- |
| **`feat`** | A new feature for the user (e.g., implementing persistent chat history). |
| **`fix`** | A bug fix (e.g., fixing a UI button alignment). |
| **`chore`** | Routine tasks that don't change production code (e.g., updating dependencies, build config). |
| **`docs`** | Changes to documentation (e.g., `README.md`, comments, project wiki). |
| **`style`** | Code formatting changes (e.g., semicolons, white-space, linter rules). |
| **`refactor`** | A change that neither fixes a bug nor adds a feature (e.g., cleaning up legacy code). |

---

### Examples

| Category | Example Commit Message | Purpose |
| :--- | :--- | :--- |
| **New Feature (`feat`)** | `feat(auth): implement MS SSO login route` | Adds the core authentication requirement. |
| **Bug Fix (`fix`)** | `fix(frontend): adjust message display for mobile responsiveness` | Fixes a styling bug on smaller screens. |
| **Routine Task (`chore`)** | `chore(deps): update all package dependencies` | Keeps the project's dependencies up-to-date. |
| **Refactoring (`refactor`)** | `refactor(backend): consolidate agent routing logic into service class` | Improves the internal structure without changing behavior. |

### Referencing and Closing Issues

To automatically close an issue tracked on your project board or GitHub repository (e.g., Issue **#22** for RBAC), you must use one of the following keywords followed by the issue number in the commit message **body** or **footer**.


## Code Style, Linting & Formatting
Name the formatter/linter, config file locations, and the exact commands to
check/fix locally.

### Front end:
- Formatter: [ESLint](https://eslint.org/)
- Config path: `front/eslint.config.mjs`
- Commands:
    - `npm run lint` to lint
  
### Back end:
- Formatter: [Ruff](https://docs.astral.sh/ruff/)
- Config path: 
- Commands:
    - `ruff format` to lint

## Testing
@Nam Long Tran

## Pull Requests & Reviews

| Requirement | Details |
| :--- | :--- |
| **PR Template** | Mandatory. Must include: **Description** (what the change does), **Related Issues** (which issue(s) this closes/references), **Testing Notes** (how a reviewer can test), and **Screenshots/Video** (if a UI change). |
| **Checklist** | Required items before marking 'Ready for Review': `[ ] Code meets acceptance criteria`, `[ ] All automated tests pass`, `[ ] Documentation/API docs updated (if applicable)`, `[ ] Self-reviewed for style/logic errors`. |
| **Size Limits** | Target a maximum of **400-500 lines of code change**. If a change is larger, work with your team to break it down into smaller, logical PRs to expedite review. |
| **Reviewer Expectations** | Reviewers must check for **functional correctness**, adherence to the **Tech Stack** (e.g., React.js, GCP preferences), security concerns, and code style. Reviews should be **constructive and objective**. |
| **Approval Rules** | A PR requires **one (1) approval** from another team member before it can be merged to the main branch. The submitter cannot approve their own PR. |
| **Status Checks** | Required status checks (to be configured in GitHub): **All Unit Tests Pass** and **Code Linter/Style Check Passes**. |

---

## CI/CD
Link to pipeline definitions, list mandatory jobs, how to view logs/re-run jobs,
and what must pass before merge/release.
@Rohan

## Security & Secrets

| Policy | Standard |
| :--- | :--- |
| **Vulnerability Reporting** | Immediately report any security concern to the entire team via a private channel (e.g., email chain) and create a **private, high-priority GitHub Issue** labeled `Security`. |
| **Prohibited Patterns** | **NEVER hard-code secrets** (API keys, database credentials, Microsoft SSO client secrets) directly into the code base, even in environment files committed to Git. This is critical as your code is **public**. |
| **Secrets Management** | All secrets must be loaded via environment variables from a secure source (e.g., a **`.env`** file that is listed in **`.gitignore`** and manually managed/shared, or a proper service like **GCP Secret Manager**). |
| **Dependency Updates** | Dependencies should be reviewed and updated **at the start of every sprint** (weekly/bi-weekly). Use tools like `npm audit` or **Dependabot** (GitHub native) to scan for known vulnerabilities. |
| **Scanning Tools** | Implement a linter and static analysis tool (e.g., **ESLint** for JavaScript) to check for common security errors and bad practices. |

---

## Documentation Expectations

| Artifact | Requirement |
| :--- | :--- |
| **`README.md`** | Must be updated before the **End of Term 1** milestone. Should cover: Project overview, setup instructions (local development), dependencies, and how to run tests. |
| **`/docs`** | Create a `docs/` folder for long-form project documentation. Must include the **Agentic Services Registry** schema, major architectural decisions, and the **Code of Conduct**. |
| **API References** | Use an automated tool (e.g., Swagger/OpenAPI) for the **Back-End Routing** API endpoints to document parameters, responses, and authentication methods. |
| **`CHANGELOG.md`** | Required. This file should be generated using the information from the **Conventional Commits** during the release process. |
| **Docstring/Comments** | All functions, classes, and complex logic blocks must have clear, concise docstrings (e.g., JSDoc for Node.js/React or docstrings for Python) explaining *what* they do, *why*, and listing parameters/returns. |

---

## Release Process

| Step | Detail |
| :--- | :--- |
| **Versioning Scheme** | Use **Semantic Versioning (SemVer)**: `MAJOR.MINOR.PATCH`. `PATCH` for bug fixes, `MINOR` for new features (`feat`), and `MAJOR` for breaking changes (e.g., changing the Agent Registry Spec). |
| **Tagging** | Every successful deployment to the staging/production environment must be tagged in Git with the new version number (e.g., `git tag v1.0.0`). |
| **Changelog Generation** | Automatically generate the `CHANGELOG.md` from the commit history using a script (or manual aggregation of `feat` and `fix` commits) for each release. |
| **Packaging/Publishing** | Since **GCP is preferred**, deployment will likely involve containerization (e.g., Docker) and using **Cloud Run** or **App Engine**. The final package is the build artifact pushed to the cloud environment. |
| **Rollback Process** | Rollback is achieved by immediately deploying the **previous stable Git tag** (version) to the hosting platform. |

---

## Support & Contact

| Channel | Detail |
| :--- | :--- |
| **Maintainer Contact** | The primary channel for urgent team questions and conflict resolution is the team's designated **Project Manager (PM)**. |
| **Sponsor Contact** | For project requirements, feedback, or technical specs (e.g., API for FAIE), the point of contact is **John V. Sweet** via his **Email**. |
| **Response Windows (Team)** | Aim for a **4-hour response window** during standard school hours (M-F, 9 am - 5 pm) for urgent team messages. |
| **Response Windows (Sponsor)** | Team should prepare agenda items for the **Friday sprint meetings** with **John Sweet**. Reserve emails for critical questions or follow-up. |
| **Where to Ask Questions** | **Technical:** Private team chat/Slack. **Requirements/Scope:** Friday Sponsor Meeting. **Conduct/Process:** The **CS Capstone Handbook** or your Faculty Advisor. |
