import subprocess
import json

def analyze_docker_smells(image_name):
    """
    Uses 'docker inspect' to check for common anti-patterns or 'smells'
    in the raw container configuration metadata as outlined in literature.
    """
    smells = {
        "runs_as_root": False,
        "uses_latest_tag": False,
        "exposed_ports": [],
        "env_vars": []
    }

    # Tag check
    if ":" not in image_name or image_name.endswith(":latest"):
        smells["uses_latest_tag"] = True

    try:
        # We need the image locally to inspect it properly.
        print(f"Forensics: Ensuring {image_name} is locally available...")
        subprocess.run(["docker", "pull", image_name], check=True, capture_output=True)

        result = subprocess.run(["docker", "inspect", image_name], capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        if not data or len(data) == 0:
            return smells

        config = data[0].get("Config", {})

        # User check (blank user strings usually mean Root is implicit in Docker)
        user = config.get("User", "")
        if user == "" or user == "0" or user.lower() == "root":
            smells["runs_as_root"] = True
        
        # Port check
        exposed = config.get("ExposedPorts", {})
        if exposed:
            smells["exposed_ports"] = list(exposed.keys())

        # Environment Vars
        env = config.get("Env", [])
        smells["env_vars"] = [e.split('=')[0] for e in env if '=' in e] # Keys only

    except Exception as e:
        print(f"Forensics failed to inspect {image_name}: {e}")

    return smells

def extract_image_history(image_name):
    """
    Uses 'docker history' to tear down the image and expose its parent/child
    layer hierarchy and the original Dockerfile commands used to build it.
    """
    layers = []
    try:
        # Use json format for easy parsing
        cmd = ["docker", "history", "--no-trunc", "--format", "{{json .}}", image_name]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        for line in result.stdout.strip().split('\n'):
            if line:
                layer_data = json.loads(line)
                layers.append({
                    "id": layer_data.get("ID", "<missing>"),
                    "created": layer_data.get("CreatedSince", ""),
                    "size": layer_data.get("Size", "0B"),
                    "command": layer_data.get("CreatedBy", "").strip()[:100] + "..." # Truncate long cmds for UI
                })
    except Exception as e:
        print(f"Forensics failed to extract history for {image_name}: {e}")

    return layers
