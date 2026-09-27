from database.db import connect

def calculate_risk(critical, high, medium, low, secrets):
    # weight-based scoring
    score = (
        critical * 10 +
        high * 7 +
        medium * 5 +
        low * 2 +
        secrets * 8
    )

    # determine risk level
    if score >= 80:
        level = "CRITICAL"
    elif score >= 50:
        level = "HIGH"
    elif score >= 20:
        level = "MEDIUM"
    else:
        level = "LOW"

    return score, level


def update_risk(image_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT critical, high, medium, low, secrets
        FROM scan_results
        WHERE image_id = ?
    """, (image_id,))

    row = cursor.fetchone()

    if row:
        critical, high, medium, low, secrets = row

        score, level = calculate_risk(critical, high, medium, low, secrets)

        cursor.execute("""
            UPDATE scan_results
            SET risk_score = ?, risk_level = ?
            WHERE image_id = ?
        """, (score, level, image_id))

        conn.commit()

        print("Risk updated:", score, level)

    conn.close()