#!/usr/bin/env python3
"""
Universal ADK Agent Deployment Script for GCP

This script deploys any ADK agent to Google Cloud Platform's Agent Engine.
It automatically detects the agent directory structure and handles deployment
configuration.

Usage:
    python deploy_agent.py <agent-name> [options]

Examples:
    python deploy_agent.py oregon-state-expert
    python deploy_agent.py Cyrano-de-Bergerac --project my-project --region us-central1
    python deploy_agent.py oregon-state-expert --display-name "OSU Expert"
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

# --- Default Configuration ---
DEFAULT_GCP_PROJECT_ID = "osu-genesis-ai-hub"
DEFAULT_GCP_REGION = "us-west1"
# Staging bucket will be auto-generated as: gs://{project_id}-staging
# ---------------------


def find_agent_directory(agent_name, base_dir):
    """
    Finds the deployable directory for the given agent.
    
    Looks for either:
    1. A subdirectory named 'agent', 'orchestrator', or 'src' within the agent directory
    2. The agent directory itself if it contains agent.py
    
    Args:
        agent_name: Name of the agent directory
        base_dir: Base directory containing all agents
    
    Returns:
        Path to the deployable directory
    
    Raises:
        FileNotFoundError: If agent directory or deployable subdirectory not found
    """
    agent_path = base_dir / agent_name
    
    if not agent_path.exists():
        raise FileNotFoundError(
            f"Agent directory not found: {agent_path}\n"
            f"Available agents: {', '.join([d.name for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith('.')])}"
        )
    
    # Check for common subdirectory patterns
    for subdir_name in ['agent', 'orchestrator', 'src']:
        subdir = agent_path / subdir_name
        if subdir.exists() and subdir.is_dir():
            # Verify it contains agent.py
            if (subdir / 'agent.py').exists():
                return subdir
    
    # Check if the agent directory itself contains agent.py
    if (agent_path / 'agent.py').exists():
        return agent_path
    
    raise FileNotFoundError(
        f"Could not find deployable directory for agent '{agent_name}'.\n"
        f"Expected to find 'agent.py' in one of: {agent_path}/agent, {agent_path}/orchestrator, "
        f"{agent_path}/src, or {agent_path}"
    )


def create_staging_bucket(project_id, region, staging_bucket):
    """Creates the GCS staging bucket if it doesn't exist."""
    print(f"\n{'='*60}")
    print(f"Checking for staging bucket: {staging_bucket}")
    print(f"{'='*60}")
    
    # Extract bucket name from gs:// URL
    bucket_name = staging_bucket.replace("gs://", "")
    
    # Determine if we need shell=True (Windows)
    use_shell = sys.platform.startswith('win')
    
    # Try gcloud storage first (modern, cross-platform)
    check_bucket_cmd = ["gcloud", "storage", "buckets", "describe", bucket_name, "--format=value(name)"]
    
    try:
        result = subprocess.run(
            check_bucket_cmd, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            shell=use_shell
        )
        print("✓ Staging bucket already exists.")
        return
    except subprocess.CalledProcessError:
        print("✗ Staging bucket not found. Creating...")
    except FileNotFoundError:
        print("✗ 'gcloud' command not found. Please install Google Cloud SDK.")
        print("   Visit: https://cloud.google.com/sdk/docs/install")
        sys.exit(1)
    
    # Create the bucket using gcloud storage
    create_bucket_cmd = [
        "gcloud", "storage", "buckets", "create",
        staging_bucket,
        f"--project={project_id}",
        f"--location={region}",
        "--uniform-bucket-level-access"
    ]
    
    try:
        subprocess.run(
            create_bucket_cmd, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8',
            shell=use_shell
        )
        print(f"✓ Successfully created bucket: {staging_bucket}")
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr if e.stderr else str(e)
        print(f"✗ Error creating bucket: {error_msg}")
        sys.exit(1)


def deploy_agent(agent_dir, project_id, region, staging_bucket, display_name):
    """Runs the ADK deploy command."""
    print(f"\n{'='*60}")
    print(f"Deploying agent from: {agent_dir}")
    print(f"Display name: {display_name}")
    print(f"{'='*60}\n")
    
    # Get the current environment's PATH and add the local bin dir
    env = os.environ.copy()
    user_bin_path = "(Not found)"
    try:
        user_base_cmd = [sys.executable, "-m", "site", "--user-base"]
        user_base = subprocess.run(
            user_base_cmd, 
            check=True, 
            capture_output=True, 
            text=True, 
            encoding='utf-8'
        ).stdout.strip()
        user_bin_path = os.path.join(user_base, "bin")
        if user_bin_path not in env.get("PATH", ""):
            print(f"Adding '{user_bin_path}' to PATH.")
            env["PATH"] = f"{user_bin_path}{os.pathsep}{env.get('PATH', '')}"
    except Exception:
        print(f"Warning: Could not determine pip user base path. Using system PATH.")
    
    deploy_cmd = [
        "adk", "deploy", "agent_engine",
        f"--project={project_id}",
        f"--region={region}",
        f"--staging_bucket={staging_bucket}",
        f"--display_name={display_name}",
        str(agent_dir)
    ]
    
    print("Running command:")
    print(" ".join(deploy_cmd))
    print("\nThis may take several minutes...\n")
    
    try:
        # Run the command and stream output in real-time
        # Use shell=True on Windows to properly find commands in PATH
        use_shell = sys.platform.startswith('win')
        
        process = subprocess.Popen(
            deploy_cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            shell=use_shell
        )
        
        full_stdout = ""
        full_stderr = ""

        # Read stdout line by line
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                full_stdout += output

        # Read any remaining stderr
        full_stderr = process.stderr.read()
        if full_stderr:
            print("\n--- Errors ---", file=sys.stderr)
            print(full_stderr.strip(), file=sys.stderr)
            
        # Final check
        if process.returncode != 0 or "Deploy failed:" in full_stdout or "Deploy failed:" in full_stderr:
            print(f"\n{'='*60}")
            print("✗ Agent deployment FAILED")
            print(f"{'='*60}")
            if "Deploy failed:" not in full_stderr:
                 print(full_stderr, file=sys.stderr)
            sys.exit(1)
        else:
            print(f"\n{'='*60}")
            print("✓ Agent deployment successful!")
            print(f"{'='*60}")
            
    except FileNotFoundError:
        print(f"\n✗ Error: 'adk' command not found.")
        print(f"We checked this path: {user_bin_path}")
        print("\nPlease ensure ADK is installed:")
        print("  pip install google-adk")
        print("\nOr check your PATH configuration.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Deploy an ADK agent to Google Cloud Platform's Agent Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s oregon-state-expert
  %(prog)s Cyrano-de-Bergerac --project my-project
  %(prog)s oregon-state-expert --region us-central1 --display-name "OSU Expert"
        """
    )
    
    parser.add_argument(
        'agent_name',
        help='Name of the agent directory to deploy'
    )
    
    parser.add_argument(
        '--project',
        default=DEFAULT_GCP_PROJECT_ID,
        help=f'GCP project ID (default: {DEFAULT_GCP_PROJECT_ID})'
    )
    
    parser.add_argument(
        '--region',
        default=DEFAULT_GCP_REGION,
        help=f'GCP region (default: {DEFAULT_GCP_REGION})'
    )
    
    parser.add_argument(
        '--staging-bucket',
        help='GCS staging bucket (default: gs://<project-id>-staging)'
    )
    
    parser.add_argument(
        '--display-name',
        help='Display name for the deployed agent (default: <agent-name>-agent)'
    )
    
    args = parser.parse_args()
    
    # Determine base directory (where this script is located)
    script_dir = Path(__file__).parent.resolve()
    
    # Set defaults based on agent name
    staging_bucket = args.staging_bucket or f"gs://{args.project}-staging"
    display_name = args.display_name or f"{args.agent_name}-agent"
    
    print(f"\n{'='*60}")
    print("ADK Agent Deployment Script")
    print(f"{'='*60}")
    print(f"Agent: {args.agent_name}")
    print(f"Project: {args.project}")
    print(f"Region: {args.region}")
    print(f"Staging Bucket: {staging_bucket}")
    print(f"Display Name: {display_name}")
    print(f"{'='*60}")
    
    try:
        # Find the deployable directory
        agent_dir = find_agent_directory(args.agent_name, script_dir)
        print(f"\n✓ Found deployable directory: {agent_dir}")
        
        # Create staging bucket if needed
        create_staging_bucket(args.project, args.region, staging_bucket)
        
        # Deploy the agent
        deploy_agent(agent_dir, args.project, args.region, staging_bucket, display_name)
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n✗ Deployment cancelled by user.")
        sys.exit(1)


if __name__ == "__main__":
    main()
