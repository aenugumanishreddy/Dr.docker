import json
from database.db import connect

def parse_and_store(image_id, json_file="result.json"):

    conn = connect()
    cursor = conn.cursor()

    with open(json_file, "r") as f:
        data = json.load(f)

    # Initialize counts
    critical = 0
    high = 0
    medium = 0
    low = 0
    secrets = 0

    # Loop through results
    for result in data.get("Results", []):
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

    # Simple risk scoring formula
    risk_score = (critical * 5) + (high * 4) + (medium * 3) + (low * 1)

    # Risk level classification
    if risk_score > 100:
        risk_level = "CRITICAL"
    elif risk_score > 50:
        risk_level = "HIGH"
    elif risk_score > 20:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    # Insert into DB
    cursor.execute("""
        INSERT INTO scan_results
        (image_id, critical, high, medium, low, secrets, risk_score, risk_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (image_id, critical, high, medium, low, secrets, risk_score, risk_level))

    conn.commit()
    conn.close()

    print("Scan results stored successfully")