#!/usr/bin/env python3
"""Fetch the real Cloud Run URL for a deployed agent and patch it in the hub.

After deploying an agent the hub record can have a blank or predicted URL.
This script:
  1. Calls ``gcloud run services describe`` to get the actual service URL,
     OR accepts the URL directly via ``--url`` if you already know it.
  2. PATCHes the hub's ``/api/agents/{agent_id}`` endpoint so both ``url``
     and ``endpoint`` are set correctly.

The ``--endpoint`` flag lets you set the A2A JSON-RPC path separately from
the base URL (needed when the agent mounts its handler at a sub-path such as
``/a2a/unit_converter_agent/`` rather than ``/``).

Usage:
    # Look up URL from GCP automatically:
    python update_agent_url.py <service-name> --agent-id <uuid> [options]

    # Supply URL directly (skips gcloud lookup):
    python update_agent_url.py --agent-id <uuid> --url <base-url> [--endpoint <rpc-url>]

Examples:
    python update_agent_url.py oregon-state-expert \\
        --agent-id abc123 \\
        --hub-url https://openbeavs.example.com \\
        --api-key $MY_TOKEN

    # unit-converter-agent: base URL + sub-path endpoint
    python update_agent_url.py \\
        --agent-id abc123 \\
        --url https://unit-converter-agent-716080272371.us-west1.run.app \\
        --endpoint https://unit-converter-agent-716080272371.us-west1.run.app/a2a/unit_converter_agent/ \\
        --hub-url https://openbeavs.example.com \\
        --api-key $MY_TOKEN
"""

import argparse
import os
import subprocess
import sys
from typing import Optional


# ---------------------------------------------------------------------------
# gcloud helpers
# ---------------------------------------------------------------------------


def _use_shell() -> bool:
    return sys.platform.startswith("win")


def _run_gcloud(*args: str) -> Optional[str]:
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


def get_gcloud_config(prop: str) -> Optional[str]:
    return _run_gcloud("config", "get-value", prop)


def get_cloud_run_url(service_name: str, project: str, region: str) -> Optional[str]:
    """Return the live HTTPS URL assigned to a Cloud Run service."""
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


def get_agent(hub_url: str, agent_id: str, api_key: str) -> dict:
    import urllib.request
    import json

    url = f"{hub_url.rstrip('/')}/api/agents/{agent_id}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise SystemExit(f"Hub GET failed ({exc.code}): {body}") from exc


def patch_agent_url(
    hub_url: str,
    agent_id: str,
    api_key: str,
    new_url: str,
    new_endpoint: str,
    *,
    dry_run: bool = False,
) -> dict:
    """PATCH the hub record to set url and endpoint."""
    import urllib.request
    import json

    payload = json.dumps({"url": new_url, "endpoint": new_endpoint}).encode()
    url = f"{hub_url.rstrip('/')}/api/agents/{agent_id}"

    if dry_run:
        print(f"[dry-run] Would PATCH {url}")
        print(f"[dry-run] Payload: {payload.decode()}")
        return {}

    req = urllib.request.Request(
        url,
        data=payload,
        method="PATCH",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise SystemExit(f"Hub PATCH failed ({exc.code}): {body}") from exc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Update a hub agent's URL from the real Cloud Run service URL.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "service_name",
        nargs="?",
        help="Cloud Run service name — required unless --url is supplied",
    )
    parser.add_argument(
        "--agent-id",
        required=True,
        help="UUID of the agent record in the hub (from GET /api/agents/all)",
    )
    parser.add_argument(
        "--url",
        dest="direct_url",
        help="Skip gcloud lookup and use this as the agent base URL directly",
    )
    parser.add_argument(
        "--endpoint",
        dest="direct_endpoint",
        help=(
            "A2A JSON-RPC endpoint URL (default: same as --url). "
            "Use when the agent mounts its handler at a sub-path, "
            "e.g. https://...run.app/a2a/unit_converter_agent/"
        ),
    )
    parser.add_argument(
        "--hub-url",
        default=os.environ.get("OPENBEAVS_HUB_URL", "http://localhost:8080"),
        help="Base URL of the hub (default: $OPENBEAVS_HUB_URL or http://localhost:8080)",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("OPENBEAVS_API_KEY"),
        help="Hub API bearer token (default: $OPENBEAVS_API_KEY)",
    )
    parser.add_argument("--project", help="GCP project ID (default: from gcloud config)")
    parser.add_argument(
        "--region", help="GCP region (default: from gcloud config, then us-west1)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without making any changes",
    )

    args = parser.parse_args()

    if not args.api_key:
        parser.error("No API key provided. Pass --api-key or set OPENBEAVS_API_KEY.")

    if not args.direct_url and not args.service_name:
        parser.error("Provide either a service_name positional argument or --url.")

    # ---------------------------------------------------------------------------
    # Resolve the base URL
    # ---------------------------------------------------------------------------
    if args.direct_url:
        base_url = args.direct_url.rstrip("/")
        source = "provided directly"
    else:
        project = args.project or get_gcloud_config("project")
        if not project:
            parser.error(
                "No GCP project. Pass --project or run: gcloud config set project YOUR-PROJECT-ID"
            )
        region = args.region or get_gcloud_config("compute/region") or "us-west1"

        print(f"\nQuerying Cloud Run for service '{args.service_name}'...")
        base_url = get_cloud_run_url(args.service_name, project, region)
        if not base_url:
            raise SystemExit(
                f"Could not retrieve URL for Cloud Run service '{args.service_name}'. "
                "Verify the service name, project, and region, and that it is deployed."
            )
        base_url = base_url.rstrip("/")
        source = f"gcloud ({args.service_name})"

    # The A2A JSON-RPC endpoint defaults to the base URL but can differ when
    # the agent mounts at a sub-path (e.g. /a2a/unit_converter_agent/).
    endpoint_url = (args.direct_endpoint or base_url).rstrip("/") + "/"

    print(f"\n{'='*60}")
    print("Update Agent URL")
    print(f"{'='*60}")
    print(f"Agent ID: {args.agent_id}")
    print(f"URL:      {base_url}  [{source}]")
    print(f"Endpoint: {endpoint_url}")
    print(f"Hub URL:  {args.hub_url}")
    if args.dry_run:
        print("Mode:     DRY RUN — no changes will be made")
    print(f"{'='*60}\n")

    # 1. Fetch current hub record so we can show what will change.
    print("Fetching current agent record from hub...")
    current = get_agent(args.hub_url, args.agent_id, args.api_key)
    print(f"  name:     {current.get('name')}")
    print(f"  url:      {current.get('url') or '(blank)'}")
    print(f"  endpoint: {current.get('endpoint') or '(blank)'}")

    if current.get("url") == base_url and current.get("endpoint") == endpoint_url:
        print("\nAgent record already up to date. Nothing to do.")
        return

    # 2. Patch the hub record.
    print(f"\nPatching hub agent {args.agent_id}...")
    updated = patch_agent_url(
        args.hub_url,
        args.agent_id,
        args.api_key,
        base_url,
        endpoint_url,
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("\n[dry-run] No changes were made.")
        return

    print(f"\n{'='*60}")
    print("Agent URL updated successfully!")
    print(f"{'='*60}")
    print(f"  url:      {updated.get('url')}")
    print(f"  endpoint: {updated.get('endpoint')}")
    print(f"\nTest:  curl {endpoint_url}.well-known/agent-card.json")


if __name__ == "__main__":
    main()
