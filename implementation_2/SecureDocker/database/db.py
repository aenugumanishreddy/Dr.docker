import sqlite3

def connect():
    return sqlite3.connect("securedocker.db")

def init_db():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS images(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        pulls INTEGER,
        last_updated TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scan_results(
        image_id INTEGER,
        critical INTEGER,
        high INTEGER,
        medium INTEGER,
        low INTEGER,
        secrets INTEGER,
        risk_score INTEGER,
        risk_level TEXT,
        FOREIGN KEY(image_id) REFERENCES images(id)
    )
    """)

    conn.commit()
    conn.close()