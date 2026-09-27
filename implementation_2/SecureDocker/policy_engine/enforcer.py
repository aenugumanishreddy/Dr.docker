import subprocess
import os
import sys

# Support running directly from the policy_engine directory or root
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from database.db import connect

def check_policy(image_name):
    """
    Evaluates the security policy for a given image.
    Returns a tuple: (Action, Reason)
    Actions: "BLOCK", "REVIEW", "ALLOW", "SCAN_REQUIRED"
    """
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT s.risk_level 
        FROM images i
        JOIN scan_results s ON i.id = s.image_id
        WHERE i.name = ?
        ORDER BY i.id DESC
        LIMIT 1
    """, (image_name,))
    
    row = cursor.fetchone()
    conn.close()

    if not row:
        return "SCAN_REQUIRED", "No scan data found for this image in the database."

    risk_level = row[0]

    if risk_level == "CRITICAL":
        return "BLOCK", f"CRITICAL risk vulnerabilities detected. Policy Engine enforced termination."
    elif risk_level == "HIGH":
        return "REVIEW", f"HIGH risk vulnerabilities present. Manual override or careful review required."
    else:
        # PENDING, MEDIUM, LOW
        return "ALLOW", f"Risk level ({risk_level}) is acceptable. Safe to deploy."


def run_secure_container(image_name, docker_args=None):
    """
    Intercepts the docker run command and applies the policy.
    In Streamlit, this returns a tuple (Success Boolean, Message).
    """
    if docker_args is None:
        docker_args = []

    action, reason = check_policy(image_name)

    if action == "BLOCK":
        msg = f"🚫 [POLICY VIOLATION] Image '{image_name}' blocked! Reason: {reason}"
        print(msg)
        return False, msg

    elif action == "SCAN_REQUIRED":
        msg = f"⚠️ [POLICY WARNING] Image '{image_name}' cannot be deployed. Reason: {reason}"
        print(msg)
        return False, msg

    else:
        # ALLOW or REVIEW - Proceed with container deployment
        print(f"✅ [POLICY CLEARED] Image '{image_name}' passed policy checks. Deploying...")
        
        # Execute the container
        # Since this might run in Streamlit, we will run in detached mode by default if not specified
        if "-d" not in docker_args and "--detach" not in docker_args:
            docker_args.append("-d")

        try:
            cmd = ["docker", "run"] + docker_args + [image_name]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            container_id = result.stdout.strip()
            msg = f"Container successfully deployed! ID: {container_id}"
            return True, msg
        except subprocess.CalledProcessError as e:
            msg = f"Docker failed to start container. Error: {e.stderr}"
            return False, msg

# Direct CLI override support
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python enforcer.py <image_name> [docker_run_args...]")
        sys.exit(1)
    
    img = sys.argv[1]
    args = sys.argv[2:]
    
    success, message = run_secure_container(img, args)
    if not success:
        sys.exit(1)
