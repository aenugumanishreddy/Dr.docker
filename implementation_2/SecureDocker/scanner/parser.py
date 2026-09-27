import json
from database.db import connect

def parse_and_store(image_id, json_file="result.json"):

    try:
        with open(json_file, "r") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading JSON file {json_file}: {e}")
        return

    conn = connect()
    cursor = conn.cursor()

    # Initialize counts
    critical = 0
    high = 0
    medium = 0
    low = 0
    secrets = 0

    # Loop through results
    for result in data.get("Results", []):
        # Extract Vulns
        vulnerabilities = result.get("Vulnerabilities", [])
        for vuln in vulnerabilities:
            severity = vuln.get("Severity", "").upper()

            if severity == "CRITICAL":
                critical += 1
            elif severity == "HIGH":
                high += 1
            elif severity == "MEDIUM":
                medium += 1
            elif severity == "LOW":
                low += 1

        # Extract Secrets
        detected_secrets = result.get("Secrets", [])
        secrets += len(detected_secrets)

    # Insert into DB
    cursor.execute("""
        INSERT INTO scan_results
        (image_id, critical, high, medium, low, secrets, risk_score, risk_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (image_id, critical, high, medium, low, secrets, 0, "PENDING"))

    conn.commit()
    conn.close()

    print("Scan results stored successfully")