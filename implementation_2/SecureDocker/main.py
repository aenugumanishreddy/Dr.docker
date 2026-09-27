import subprocess
subprocess.run(["trivy", "image", "-f", "json", "-o", "result.json", "nginx"], check=True)