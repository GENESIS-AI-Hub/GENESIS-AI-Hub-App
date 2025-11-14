import subprocess
import sys
import os

# --- Configuration ---
# These are your project-specific values
GCP_PROJECT_ID = "genesis-hub-osu-test"
GCP_REGION = "us-west1"
STAGING_BUCKET = f"gs://{GCP_PROJECT_ID}-staging"
DISPLAY_NAME = "genesis-hub-agent-orchestrator"
AGENT_DIR = "orchestrator" # The directory containing your agent's code
# ---------------------

def create_staging_bucket():
    """Creates the GCS staging bucket if it doesn't exist."""
    print(f"Checking for staging bucket: {STAGING_BUCKET}")
    check_bucket_cmd = ["gsutil", "ls", STAGING_BUCKET]
    try:
        subprocess.run(check_bucket_cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        print("Staging bucket already exists.")
    except subprocess.CalledProcessError:
        print("Staging bucket not found. Creating...")
        create_bucket_cmd = ["gsutil", "mb", "-p", GCP_PROJECT_ID, "-l", GCP_REGION, STAGING_BUCKET]
        try:
            subprocess.run(create_bucket_cmd, check=True, capture_output=True, text=True, encoding='utf-8')
            print(f"Successfully created bucket: {STAGING_BUCKET}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating bucket: {e.stderr}")
            sys.exit(1)

def deploy_agent():
    """Runs the ADK deploy command."""
    print(f"\nDeploying agent from '{AGENT_DIR}' directory...")
    
    # Get the current environment's PATH and add the local bin dir
    env = os.environ.copy()
    user_bin_path = "(Not found)"
    try:
        user_base_cmd = [sys.executable, "-m", "site", "--user-base"]
        user_base = subprocess.run(user_base_cmd, check=True, capture_output=True, text=True, encoding='utf-8').stdout.strip()
        user_bin_path = os.path.join(user_base, "bin")
        if user_bin_path not in env.get("PATH", ""):
            print(f"Dynamically adding '{user_bin_path}' to PATH.")
            env["PATH"] = f"{user_bin_path}:{env.get('PATH', '')}"
    except Exception:
        print(f"Warning: Could not determine pip user base path. Using system PATH.")
    
    deploy_cmd = [
        "adk", "deploy", "agent_engine",
        f"--project={GCP_PROJECT_ID}",
        f"--region={GCP_REGION}",
        f"--staging_bucket={STAGING_BUCKET}",
        f"--display_name={DISPLAY_NAME}",
        AGENT_DIR
    ]
    
    print("Running command:")
    print(" ".join(deploy_cmd))
    print("\nThis may take several minutes...")
    
    try:
        # --- ROBUST ERROR CHECKING ---
        # Run the command and stream output in real-time
        # We'll also capture it to check for failure text.
        process = subprocess.Popen(
            deploy_cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8'
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
            print("\n--- Agent deployment FAILED ---")
            if "Deploy failed:" not in full_stderr:
                 print(full_stderr, file=sys.stderr)
            sys.exit(1)
        else:
            print("\nAgent deployment successful!")
        # --- END CHANGE ---
            
    except FileNotFoundError:
        print(f"\nError: 'adk' command not found.")
        print(f"We dynamically checked this path: {user_bin_path}")
        print("Please run: find / -name adk 2>/dev/null")
        sys.exit(1)

if __name__ == "__main__":
    create_staging_bucket()
    deploy_agent()