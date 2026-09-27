import requests
from database.db import connect

def collect_images(limit=20):

    url = f"https://hub.docker.com/v2/repositories/library/?page_size={limit}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching images from Docker Hub: {e}")
        return False

    conn = connect()
    cursor = conn.cursor()

    for repo in data.get("results", []):

        name = repo["name"]
        pulls = repo["pull_count"]
        updated = repo["last_updated"]

        # Check for duplicates
        cursor.execute("SELECT id FROM images WHERE name=?", (name,))
        row = cursor.fetchone()

        if row:
            # Update existing to prevent DB bloat
            cursor.execute("""
                UPDATE images
                SET pulls=?, last_updated=?
                WHERE name=?
            """, (pulls, updated, name))
        else:
            # Insert new
            cursor.execute(
                "INSERT INTO images(name,pulls,last_updated) VALUES (?,?,?)",
                (name, pulls, updated)
            )

    conn.commit()
    conn.close()

    print(f"Successfully synced up to {limit} images from Docker Hub.")
    return True