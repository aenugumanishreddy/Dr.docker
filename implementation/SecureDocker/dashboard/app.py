import streamlit as st
import pandas as pd
import os
from database.db import connect

# -----------------------------
# PAGE SETTINGS
# -----------------------------
st.set_page_config(
    page_title="SecureDocker Dashboard",
    page_icon="🔐",
    layout="wide"
)

st.markdown(
    """
    <style>
    body {background-color: #0e1117; color: white;}
    </style>
    """,
    unsafe_allow_html=True
)

# -----------------------------
# TITLE
# -----------------------------
st.title("🔐 SecureDocker - Container Security Dashboard")

if st.button("🔄 Refresh Dashboard"):
    st.experimental_rerun()

st.markdown("### Real-time Vulnerability & Risk Analysis")
st.markdown("---")

# -----------------------------
# USER INPUT SECTION
# -----------------------------
st.subheader("🔍 Scan New Image")

user_image = st.text_input("Enter Docker Image (e.g., nginx, redis)")

if st.button("Scan Now"):

    if user_image:
        with st.spinner(f"🔄 Scanning {user_image}... please wait"):

            os.system(f"trivy image -f json -o user_result.json {user_image}")

            from scanner.parser import parse_and_store
            from risk_engine import update_risk

            conn = connect()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO images(name,pulls,last_updated) VALUES (?,?,?)",
                (user_image, 0, "manual")
            )
            image_id = cursor.lastrowid
            conn.commit()
            conn.close()

            if not os.path.exists("user_result.json"):
                st.error("❌ Scan failed! Please check image name.")
            else:
                parse_and_store(image_id, json_file="user_result.json")
                update_risk(image_id)
                st.success("✅ Scan completed!")

# -----------------------------
# SELECT EXISTING IMAGE
# -----------------------------
st.subheader("📂 Select Existing Image")

conn = connect()
cursor = conn.cursor()
cursor.execute("SELECT name FROM images")
image_list = [row[0] for row in cursor.fetchall()]
conn.close()

selected_image = st.selectbox("Choose Image from Database", image_list)

if st.button("Scan Selected Image"):

    with st.spinner(f"🔄 Scanning {selected_image}..."):
        os.system(f"trivy image -f json -o selected.json {selected_image}")

        from scanner.parser import parse_and_store
        from risk_engine import update_risk

        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM images WHERE name=?", (selected_image,))
        image_id = cursor.fetchone()[0]
        conn.close()

        if not os.path.exists("selected.json"):
            st.error("❌ Scan failed!")
        else:
            parse_and_store(image_id, json_file="selected.json")
            update_risk(image_id)
            st.success("✅ Scan completed!")

# -----------------------------
# BULK SCAN BUTTON 🔥
# -----------------------------
st.subheader("⚡ Bulk Scan (Large Scale)")

if st.button("Run Bulk Scan (10 Images)"):
    from bulk_scanner import scan_bulk

    with st.spinner("🔄 Running bulk scan..."):
        scan_bulk(10)

    st.success("✅ Bulk scan completed!")

st.markdown("---")

# -----------------------------
# FETCH DATA
# -----------------------------
conn = connect()
cursor = conn.cursor()

cursor.execute("""
    SELECT i.name, s.critical, s.high, s.medium, s.low,
           s.secrets, s.risk_score, s.risk_level
    FROM images i
    JOIN scan_results s ON i.id = s.image_id
""")

rows = cursor.fetchall()
conn.close()

# -----------------------------
# DATAFRAME
# -----------------------------
columns = ["Image", "Critical", "High", "Medium", "Low", "Secrets", "Risk Score", "Risk Level"]
df = pd.DataFrame(rows, columns=columns)
df = df.sort_values(by="Risk Score", ascending=False)

if df.empty:
    st.warning("⚠️ No scan data available. Please scan an image.")

# -----------------------------
# TOP RISKY
# -----------------------------
st.subheader("🏆 Top Risky Images")
top_risky = df.head(5)
st.table(top_risky[["Image", "Risk Score", "Risk Level"]])

# -----------------------------
# METRICS
# -----------------------------
st.subheader("📊 Overview")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Images", len(df))
col2.metric("Total Critical", int(df["Critical"].sum()))
col3.metric("Total High", int(df["High"].sum()))
col4.metric("Avg Risk Score", int(df["Risk Score"].mean()) if len(df) > 0 else 0)

# -----------------------------
# HIGHEST RISK
# -----------------------------
st.subheader("🥇 Highest Risk Image")

if not df.empty:
    top = df.iloc[0]
    st.error(f"{top['Image']} → {top['Risk Level']} (Score: {top['Risk Score']})")

st.markdown("---")

# -----------------------------
# FILTER
# -----------------------------
st.subheader("🔍 Filter by Risk Level")

risk_filter = st.selectbox(
    "Select Risk Level",
    ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"]
)

if risk_filter != "ALL":
    filtered_df = df[df["Risk Level"] == risk_filter]
else:
    filtered_df = df

# -----------------------------
# TABLE
# -----------------------------
st.subheader("📋 Scan Results Table")
st.write(f"Showing {len(filtered_df)} results")
st.dataframe(filtered_df, use_container_width=True)

st.markdown("---")

# -----------------------------
# RISK STATUS
# -----------------------------
st.subheader("🚨 Risk Status")

for index, row in filtered_df.iterrows():
    if row["Risk Level"] == "CRITICAL":
        st.error(f"🚨 {row['Image']} → CRITICAL RISK")
    elif row["Risk Level"] == "HIGH":
        st.warning(f"⚠️ {row['Image']} → HIGH RISK")
    elif row["Risk Level"] == "MEDIUM":
        st.info(f"ℹ️ {row['Image']} → MEDIUM RISK")
    else:
        st.success(f"✅ {row['Image']} → LOW RISK")

st.markdown("---")

# -----------------------------
# DECISION SYSTEM
# -----------------------------
st.subheader("🚦 Deployment Decision")

for index, row in filtered_df.iterrows():
    if row["Risk Level"] == "CRITICAL":
        st.error(f"❌ {row['Image']} → BLOCK DEPLOYMENT")
    elif row["Risk Level"] == "HIGH":
        st.warning(f"⚠️ {row['Image']} → REVIEW BEFORE DEPLOY")
    elif row["Risk Level"] == "MEDIUM":
        st.info(f"ℹ️ {row['Image']} → CAN DEPLOY WITH CAUTION")
    else:
        st.success(f"✅ {row['Image']} → SAFE TO DEPLOY")

st.markdown("---")

# -----------------------------
# CHARTS
# -----------------------------
st.subheader("📈 Vulnerability Distribution")
chart_data = df[["Critical", "High", "Medium", "Low"]]
st.bar_chart(chart_data)

st.subheader("🥧 Risk Level Distribution")
risk_counts = df["Risk Level"].value_counts()
st.bar_chart(risk_counts)

st.markdown("---")

# -----------------------------
# FOOTER
# -----------------------------
st.markdown("🔐 SecureDocker | DevSecOps Dashboard")

