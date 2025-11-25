#!/usr/bin/env python3
"""
Universal A2A Agent Deployment Script for Cloud Run

This script deploys ADK A2A agents to Google Cloud Run.
It automatically pulls configuration from your gcloud config and constructs
the proper gcloud run deploy command.

Usage:
    python deploy_agent.py <agent-name> [options]

Examples:
    python deploy_agent.py oregon-state-expert
    python deploy_agent.py Cyrano-de-Bergerac --project my-project
    python deploy_agent.py oregon-state-expert --region us-central1
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def get_gcloud_config(property_name):
    """Get a property from gcloud config."""
    use_shell = sys.platform.startswith('win')
    try:
        result = subprocess.run(
            ["gcloud", "config", "get-value", property_name],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            shell=use_shell
        )
        value = result.stdout.strip()
        if value and value != "(unset)":
            return value
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    return None


def get_project_number(project_id):
    """Get the project number for a given project ID."""
    use_shell = sys.platform.startswith('win')
    try:
        result = subprocess.run(
            ["gcloud", "projects", "describe", project_id, "--format=value(projectNumber)"],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            shell=use_shell
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Deploy an A2A agent to Google Cloud Run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s oregon-state-expert
  %(prog)s Cyrano-de-Bergerac --project my-project
  %(prog)s oregon-state-expert --region us-central1
        """
    )
    
    parser.add_argument(
        'agent_name',
        help='Name of the agent directory to deploy'
    )
    
    parser.add_argument(
        '--project',
        help='GCP project ID (default: from gcloud config)'
    )
    
    parser.add_argument(
        '--region',
        help='GCP region (default: from gcloud config or us-west1)'
    )
    
    parser.add_argument(
        '--allow-unauthenticated',
        action='store_true',
        help='Make the service public (default: requires authentication)'
    )
    
    parser.add_argument(
        '--memory',
        default='1Gi',
        help='Memory allocation (default: 1Gi)'
    )
    
    args = parser.parse_args()
    
    # Auto-detect project from gcloud config
    project = args.project or get_gcloud_config("project")
    if not project:
        print("\n✗ Error: No GCP project specified and could not detect from gcloud config.")
        print("   Please either:")
        print("   1. Set default project: gcloud config set project YOUR-PROJECT-ID")
        print("   2. Use --project flag: python deploy_agent.py <agent> --project YOUR-PROJECT-ID")
        sys.exit(1)
    
    # Auto-detect region from gcloud config
    region = args.region or get_gcloud_config("compute/region") or "us-west1"
    
    # Get project number for APP_URL
    project_number = get_project_number(project)
    if not project_number:
        print(f"\n⚠ Warning: Could not get project number for {project}")
        print("   APP_URL will need to be updated manually after deployment")
        app_url = f"https://{args.agent_name}.{region}.run.app"
    else:
        app_url = f"https://{args.agent_name}-{project_number}.{region}.run.app"
    
    # Determine agent directory
    script_dir = Path(__file__).parent.resolve()
    agent_dir = script_dir / args.agent_name
    
    if not agent_dir.exists():
        print(f"\n✗ Error: Agent directory not found: {agent_dir}")
        print(f"   Available agents: {', '.join([d.name for d in script_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])}")
        sys.exit(1)
    
    print(f"\n{'='*70}")
    print("A2A Agent Cloud Run Deployment")
    print(f"{'='*70}")
    print(f"Agent:          {args.agent_name}")
    print(f"Project:        {project}")
    print(f"Region:         {region}")
    print(f"Memory:         {args.memory}")
    print(f"Authentication: {'Public' if args.allow_unauthenticated else 'IAM Required'}")
    print(f"App URL:        {app_url}")
    print(f"Source:         {agent_dir}")
    print(f"{'='*70}\n")
    
    # Construct the gcloud run deploy command
    deploy_cmd = [
        "gcloud", "run", "deploy", args.agent_name,
        "--port=8080",
        f"--source={agent_dir}",
        f"--region={region}",
        f"--project={project}",
        f"--memory={args.memory}",
        f"--set-env-vars=GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT={project},GOOGLE_CLOUD_LOCATION={region},APP_URL={app_url},HOST_OVERRIDE={app_url}"
    ]
    
    # Add authentication flag
    if args.allow_unauthenticated:
        deploy_cmd.append("--allow-unauthenticated")
    else:
        deploy_cmd.append("--no-allow-unauthenticated")
    
    print("Running command:")
    print(" ".join(deploy_cmd))
    print("\nThis may take several minutes...\n")
    
    # Run the deployment
    use_shell = sys.platform.startswith('win')
    
    try:
        result = subprocess.run(
            deploy_cmd,
            shell=use_shell,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            print(f"\n{'='*70}")
            print("✓ Agent deployment successful!")
            print(f"{'='*70}")
            print(f"\nYour A2A agent is now deployed to Cloud Run!")
            print(f"\n🌐 Service URL: {app_url}")
            print(f"\n📋 A2A Agent Card: {app_url}/.well-known/agent-card.json")
            print(f"\nTo test your agent:")
            print(f"  curl {app_url}/.well-known/agent-card.json")
            print(f"\nTo view logs:")
            print(f"  gcloud run services logs read {args.agent_name} --project={project} --region={region}")
            print(f"\nTo update environment variables:")
            print(f"  gcloud run services update {args.agent_name} --update-env-vars KEY=VALUE --project={project} --region={region}\n")
        else:
            print(f"\n{'='*70}")
            print("✗ Agent deployment FAILED")
            print(f"{'='*70}")
            print("\nCheck the error messages above for details.")
            print("\nCommon issues:")
            print("  - Missing Dockerfile or requirements.txt in agent directory")
            print("  - Insufficient permissions")
            print("  - Invalid source code structure")
            print(f"\nFor more help, see: https://cloud.google.com/run/docs/deploy-a2a-agents")
            sys.exit(1)
            
    except FileNotFoundError:
        print(f"\n✗ Error: 'gcloud' command not found.")
        print("\nPlease ensure Google Cloud SDK is installed:")
        print("  Visit: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ Deployment cancelled by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
