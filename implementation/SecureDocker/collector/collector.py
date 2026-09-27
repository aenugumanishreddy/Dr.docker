import requests
from database.db import connect

def collect_images():

    url = "https://hub.docker.com/v2/repositories/library/?page_size=20"

    response = requests.get(url)

    data = response.json()

    conn = connect()
    cursor = conn.cursor()

    for repo in data["results"]:

        name = repo["name"]
        pulls = repo["pull_count"]
        updated = repo["last_updated"]

        cursor.execute(
            "INSERT INTO images(name,pulls,last_updated) VALUES (?,?,?)",
            (name, pulls, updated)
        )

    conn.commit()
    conn.close()

    print("Images collected successfully")