import sys
import os
import subprocess
import tempfile
from database.db import connect
from scanner.parser import parse_and_store
from risk_engine import update_risk

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def scan_bulk(limit=10):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM images LIMIT ?", (limit,))
    db_images = cursor.fetchall()
    
    images_to_scan = []
    if not db_images:
        print("\n⚠️ Database is empty! Loading predefined demo registry images...")
        demo_list = ["redis:latest", "nginx:latest", "ubuntu:22.04", "node:18", "debian:11", "postgres:15", "alpine:latest", "mysql:8", "java:8", "centos:7"]
        for img in demo_list[:limit]:
            cursor.execute("INSERT INTO images (name, pulls, last_updated) VALUES (?, 0, 'manual')", (img,))
            image_id = cursor.lastrowid
            conn.commit()
            images_to_scan.append((image_id, img))
    else:
        images_to_scan = db_images

    for image_id, name in images_to_scan:
        print(f"\n🔍 Scanning {name}...")

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
            json_file = tmp_file.name

        try:
            # 🔥 STEP 1: Pull image
            subprocess.run(["docker", "pull", name], check=True)

            # 🔥 STEP 2: Run Trivy scan
            subprocess.run(["trivy", "image", "--scanners", "vuln", "-f", "json", "-o", json_file, name], check=True)

            # 🔥 STEP 3: Check JSON exists
            if not os.path.exists(json_file):
                print(f"❌ Skipping {name} (no result file)")
                continue

            # 🔥 STEP 4: Parse + risk
            parse_and_store(image_id, json_file=json_file)
            update_risk(image_id)
            print(f"✅ Completed {name}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Skipping {name} (command failed)")
            continue
        except Exception as e:
            print(f"❌ Error processing {name}: {e}")
            continue
        finally:
            if os.path.exists(json_file):
                os.remove(json_file)
    conn.close()

    print("\n✅ Bulk scanning completed!")