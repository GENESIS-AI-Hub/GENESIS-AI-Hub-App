#!/usr/bin/env python3
"""Universal A2A Agent Deployment Script for Cloud Run.

Two entry points:

* ``deploy_agent_to_cloud_run(...)`` — importable helper used by the
  hub backend's ``utils/cloud_run.py`` to provision a per-agent Cloud
  Run service when an admin clicks "Deploy" in the UI.
* ``main()`` — the original CLI for deploying ADK agents from the
  ``agents/`` directory by name.

Both share the same gcloud command construction so the behaviour stays
in one place.

After a successful deploy the script fetches the real Cloud Run URL via
``gcloud run services describe`` and (optionally) patches the hub agent
record so the ``url`` and ``endpoint`` fields are never blank.

Usage (CLI):
    python deploy_agent.py <agent-name> [options]

Examples:
    python deploy_agent.py oregon-state-expert
    python deploy_agent.py Cyrano-de-Bergerac --project my-project
    python deploy_agent.py oregon-state-expert --region us-central1

    # Deploy and immediately update the hub record:
    python deploy_agent.py unit-converter-agent \\
        --hub-url https://openbeavs.example.com \\
        --api-key $MY_TOKEN \\
        --agent-id <uuid-from-hub>
"""

import argparse
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Iterable, Mapping, Optional


class CloudRunDeployError(RuntimeError):
    """Raised when a Cloud Run deployment fails for any reason."""


def _use_shell() -> bool:
    return sys.platform.startswith("win")


def _run_gcloud(*args: str) -> Optional[str]:
    """Run a gcloud command and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            ["gcloud", *args],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            shell=_use_shell(),
        )
        value = result.stdout.strip()
        return value if value and value != "(unset)" else None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def get_gcloud_config(property_name: str) -> Optional[str]:
    """Read a property from ``gcloud config``."""
    return _run_gcloud("config", "get-value", property_name)


def get_project_number(project_id: str) -> Optional[str]:
    """Resolve the numeric project number for ``project_id``."""
    return _run_gcloud("projects", "describe", project_id, "--format=value(projectNumber)")


def get_cloud_run_url(service_name: str, project: str, region: str) -> Optional[str]:
    """Return the live HTTPS URL assigned to a Cloud Run service after deploy."""
    return _run_gcloud(
        "run",
        "services",
        "describe",
        service_name,
        f"--project={project}",
        f"--region={region}",
        "--format=value(status.url)",
    )


# ---------------------------------------------------------------------------
# Hub API helpers
# ---------------------------------------------------------------------------


def _patch_hub_agent(
    hub_url: str,
    agent_id: str,
    api_key: str,
    url: str,
    endpoint: str,
) -> dict:
    """PATCH the hub's agent record to set url and endpoint."""
    payload = json.dumps({"url": url, "endpoint": endpoint}).encode()
    api_url = f"{hub_url.rstrip('/')}/api/agents/{agent_id}"
    req = urllib.request.Request(
        api_url,
        data=payload,
        method="PATCH",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise CloudRunDeployError(
            f"Hub PATCH failed ({exc.code}) for agent {agent_id}: {body}"
        ) from exc
    except OSError as exc:
        raise CloudRunDeployError(
            f"Could not reach hub at {hub_url}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Core deploy function (used by hub backend and CLI)
# ---------------------------------------------------------------------------


def deploy_agent_to_cloud_run(
    service_name: str,
    source_dir: Path,
    env_vars: Mapping[str, str],
    *,
    project: Optional[str] = None,
    region: Optional[str] = None,
    memory: str = "1Gi",
    allow_unauthenticated: bool = True,
    secret_refs: Optional[Mapping[str, str]] = None,
    extra_set_env_vars: Optional[Iterable[str]] = None,
) -> str:
    """Deploy a Cloud Run service from ``source_dir`` and return its URL.

    ``service_name`` is used both as the Cloud Run service name and as
    the basis for the predicted URL. ``env_vars`` are passed to
    ``--set-env-vars`` and must not contain secrets — bind those via
    ``secret_refs`` (mapping of env-var name -> ``secret-id:version``)
    so they're routed through Secret Manager and don't appear in the
    revision metadata.

    After a successful deploy the function queries GCP for the real
    assigned URL and returns that instead of a predicted value.

    Raises ``CloudRunDeployError`` on any failure, including when
    gcloud is not on PATH.
    """
    project = project or get_gcloud_config("project")
    if not project:
        raise CloudRunDeployError(
            "No GCP project specified and could not detect one from gcloud config. "
            "Run `gcloud config set project YOUR-PROJECT-ID` or pass project= explicitly."
        )

    region = region or get_gcloud_config("compute/region") or "us-west1"

    # Compute a predicted URL so APP_URL / HOST_OVERRIDE are available to the
    # service at startup even before we can query the real URL.
    project_number = get_project_number(project)
    if project_number:
        predicted_url = f"https://{service_name}-{project_number}.{region}.run.app"
    else:
        predicted_url = f"https://{service_name}.{region}.run.app"

    if not source_dir.exists():
        raise CloudRunDeployError(f"Agent source directory not found: {source_dir}")

    set_env_pairs = [f"{k}={v}" for k, v in env_vars.items()]
    set_env_pairs.append(f"APP_URL={predicted_url}")
    set_env_pairs.append(f"HOST_OVERRIDE={predicted_url}")
    if extra_set_env_vars:
        set_env_pairs.extend(extra_set_env_vars)

    deploy_cmd = [
        "gcloud",
        "run",
        "deploy",
        service_name,
        "--port=8080",
        f"--source={source_dir}",
        f"--region={region}",
        f"--project={project}",
        f"--memory={memory}",
        f"--set-env-vars={','.join(set_env_pairs)}",
    ]

    if secret_refs:
        secret_pairs = ",".join(f"{k}={v}" for k, v in secret_refs.items())
        deploy_cmd.append(f"--update-secrets={secret_pairs}")

    if allow_unauthenticated:
        deploy_cmd.append("--allow-unauthenticated")
    else:
        deploy_cmd.append("--no-allow-unauthenticated")

    try:
        result = subprocess.run(
            deploy_cmd,
            shell=_use_shell(),
            text=True,
            encoding="utf-8",
        )
    except FileNotFoundError as exc:
        raise CloudRunDeployError(
            "gcloud is not installed or not on PATH on the hub host."
        ) from exc

    if result.returncode != 0:
        raise CloudRunDeployError(
            f"gcloud run deploy failed for service '{service_name}' (exit {result.returncode})."
        )

    # gcloud run deploy is synchronous — the service is live at this point.
    # Query the real assigned URL rather than returning our prediction.
    real_url = get_cloud_run_url(service_name, project, region)
    return real_url or predicted_url


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Deploy an A2A agent to Google Cloud Run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s oregon-state-expert
  %(prog)s Cyrano-de-Bergerac --project my-project
  %(prog)s oregon-state-expert --region us-central1

  # Deploy and update the hub record in one step:
  %(prog)s unit-converter-agent \\
      --hub-url https://openbeavs.example.com \\
      --api-key $MY_TOKEN \\
      --agent-id <uuid-from-hub>
        """,
    )

    parser.add_argument("agent_name", help="Name of the agent directory to deploy")
    parser.add_argument("--project", help="GCP project ID (default: from gcloud config)")
    parser.add_argument(
        "--region", help="GCP region (default: from gcloud config or us-west1)"
    )
    parser.add_argument(
        "--allow-unauthenticated",
        action="store_true",
        help="Make the service public (default: requires authentication)",
    )
    parser.add_argument("--memory", default="1Gi", help="Memory allocation (default: 1Gi)")

    hub_group = parser.add_argument_group(
        "hub update (optional)",
        "If all three flags are provided the script patches the hub agent record "
        "with the real Cloud Run URL immediately after deploy.",
    )
    hub_group.add_argument(
        "--hub-url",
        help="Base URL of the OpenBeavs hub (e.g. https://openbeavs.example.com)",
    )
    hub_group.add_argument(
        "--api-key",
        help="Hub API bearer token (from Settings → Account → API Key)",
    )
    hub_group.add_argument(
        "--agent-id",
        help="UUID of the agent record in the hub (from GET /api/agents/all)",
    )
    hub_group.add_argument(
        "--endpoint",
        dest="rpc_endpoint",
        help=(
            "A2A JSON-RPC endpoint if different from the service root URL "
            "(e.g. https://...run.app/a2a/unit_converter_agent/). "
            "Defaults to the Cloud Run service URL."
        ),
    )

    args = parser.parse_args()

    script_dir = Path(__file__).parent.resolve()
    agent_dir = script_dir / args.agent_name

    if not agent_dir.exists():
        available = [
            d.name
            for d in script_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]
        print(f"\n✗ Error: Agent directory not found: {agent_dir}")
        print(f"   Available agents: {', '.join(available)}")
        sys.exit(1)

    project = args.project or get_gcloud_config("project")
    if not project:
        print("\n✗ Error: No GCP project specified and could not detect from gcloud config.")
        print("   Please either:")
        print("   1. Set default project: gcloud config set project YOUR-PROJECT-ID")
        print("   2. Use --project flag: python deploy_agent.py <agent> --project YOUR-PROJECT-ID")
        sys.exit(1)

    region = args.region or get_gcloud_config("compute/region") or "us-west1"

    hub_args = (args.hub_url, args.api_key, args.agent_id)
    update_hub = all(hub_args)
    if any(hub_args) and not update_hub:
        missing = [
            name
            for name, val in zip(("--hub-url", "--api-key", "--agent-id"), hub_args)
            if not val
        ]
        print(f"\n✗ Error: Hub update requires all three flags. Missing: {', '.join(missing)}")
        sys.exit(1)

    print(f"\n{'='*70}")
    print("A2A Agent Cloud Run Deployment")
    print(f"{'='*70}")
    print(f"Agent:          {args.agent_name}")
    print(f"Project:        {project}")
    print(f"Region:         {region}")
    print(f"Memory:         {args.memory}")
    print(f"Authentication: {'Public' if args.allow_unauthenticated else 'IAM Required'}")
    print(f"Source:         {agent_dir}")
    if update_hub:
        print(f"Hub update:     {args.hub_url}  (agent {args.agent_id})")
    print(f"{'='*70}\n")

    env_vars = {
        "GOOGLE_GENAI_USE_VERTEXAI": "true",
        "GOOGLE_CLOUD_PROJECT": project,
        "GOOGLE_CLOUD_LOCATION": region,
    }

    try:
        url = deploy_agent_to_cloud_run(
            args.agent_name,
            agent_dir,
            env_vars,
            project=project,
            region=region,
            memory=args.memory,
            allow_unauthenticated=args.allow_unauthenticated,
        )
    except CloudRunDeployError as exc:
        print(f"\n{'='*70}")
        print("✗ Agent deployment FAILED")
        print(f"{'='*70}")
        print(f"\n{exc}")
        print("\nCommon issues:")
        print("  - Missing Dockerfile or requirements.txt in agent directory")
        print("  - Insufficient permissions")
        print("  - Invalid source code structure")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ Deployment cancelled by user.")
        sys.exit(1)

    print(f"\n{'='*70}")
    print("✓ Agent deployment successful!")
    print(f"{'='*70}")
    print(f"\nYour A2A agent is now deployed to Cloud Run!")
    print(f"\n🌐 Service URL: {url}")
    print(f"\n📋 A2A Agent Card: {url}/.well-known/agent-card.json")
    print("\nTo test your agent:")
    print(f"  curl {url}/.well-known/agent-card.json")
    print("\nTo view logs:")
    print(
        f"  gcloud run services logs read {args.agent_name} --project={project} --region={region}"
    )

    if not update_hub:
        return

    # Patch the hub record with the real URL.
    endpoint_url = (args.rpc_endpoint or url).rstrip("/") + "/"
    print(f"\n{'='*70}")
    print("Updating hub agent record...")
    print(f"{'='*70}")
    print(f"  url:      {url}")
    print(f"  endpoint: {endpoint_url}")
    try:
        updated = _patch_hub_agent(
            args.hub_url,
            args.agent_id,
            args.api_key,
            url,
            endpoint_url,
        )
        print(f"\n✓ Hub record updated for agent '{updated.get('name', args.agent_id)}'")
    except CloudRunDeployError as exc:
        print(f"\n✗ Hub update failed (deploy succeeded): {exc}")
        print(
            f"\nRun manually:\n"
            f"  python update_agent_url.py \\\n"
            f"    --agent-id {args.agent_id} \\\n"
            f"    --url {url} \\\n"
            f"    --endpoint {endpoint_url} \\\n"
            f"    --hub-url {args.hub_url} \\\n"
            f"    --api-key <your-token>"
        )


if __name__ == "__main__":
    main()
