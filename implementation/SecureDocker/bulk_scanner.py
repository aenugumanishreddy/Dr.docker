from database.db import connect
import os
from scanner.parser import parse_and_store
from risk_engine import update_risk

def scan_bulk(limit=10):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM images LIMIT ?", (limit,))
    images = cursor.fetchall()
    for image_id, name in images:
        print(f"\n🔍 Scanning {name}...")

        json_file = f"result_{image_id}.json"

        # 🔥 STEP 1: Pull image
        pull_status = os.system(f"docker pull {name}")

        if pull_status != 0:
            print(f"❌ Skipping {name} (docker pull failed)")
            continue

        # 🔥 STEP 2: Run Trivy scan
        scan_status = os.system(
            f"trivy image --scanners vuln -f json -o {json_file} {name}"
        )

        if scan_status != 0:
            print(f"❌ Skipping {name} (scan failed)")
            continue
            
        # 🔥 STEP 3: Check JSON exists
        if not os.path.exists(json_file):
            print(f"❌ Skipping {name} (no result file)")
            continue

        # 🔥 STEP 4: Parse + risk
        try:
            parse_and_store(image_id, json_file=json_file)
            update_risk(image_id)
            print(f"✅ Completed {name}")
        except Exception as e:
            print(f"❌ Error processing {name}: {e}")
            continue
    conn.close()

    print("\n✅ Bulk scanning completed!")