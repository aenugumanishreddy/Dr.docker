from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import sys

# Ensure root directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from database.db import connect
from scanner.parser import parse_and_store
from risk_engine import update_risk
from policy_engine.enforcer import check_policy

app = Flask(__name__)

@app.route('/api/v1/scan', methods=['POST'])
def scan_image():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    image_name = data.get("image_name")
    
    if not image_name:
        return jsonify({"error": "Missing 'image_name' in JSON body"}), 400

    print(f"📥 Received webhook to scan: {image_name}")

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
        json_file_path = tmp_file.name

    try:
        # Pull if needed (optional, Trivy does this implicitly, but explicitly pulling ensures image is local)
        print(f"🔄 Running Trivy on {image_name}...")
        subprocess.run(["trivy", "image", "-f", "json", "-o", json_file_path, image_name], check=True)

        # Insert placeholder to DB
        conn = connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO images(name,pulls,last_updated) VALUES (?,?,?)",
            (image_name, 0, "ci_cd_webhook")
        )
        image_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Parse and Update Risk
        parse_and_store(image_id, json_file=json_file_path)
        update_risk(image_id)

        # Check Policy
        action, reason = check_policy(image_name)
        
        response_payload = {
            "image": image_name,
            "policy_action": action,
            "reason": reason
        }

        if action in ["BLOCK", "REVIEW"]:
            print(f"🚫 Webhook returning 406 - Policy Failed: {reason}")
            return jsonify(response_payload), 406  # Not Acceptable - Fail the CI/CD build
        else:
            print(f"✅ Webhook returning 200 - Policy Passed: {reason}")
            return jsonify(response_payload), 200  # OK - Pass the CI/CD build

    except subprocess.CalledProcessError as e:
        print(f"❌ Trivy scan failed for {image_name}.")
        return jsonify({"error": "Trivy scan failed", "details": str(e)}), 500
    except Exception as e:
        print(f"❌ Internal Server Error: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        if os.path.exists(json_file_path):
            os.remove(json_file_path)

if __name__ == '__main__':
    print("🚀 Starting SecureDocker CI/CD Webhook Server on port 5000...")
    app.run(host='0.0.0.0', port=5000)
