import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import subprocess
import tempfile
import sys
from database.db import connect

# -----------------------------
# PAGE SETTINGS
# -----------------------------
st.set_page_config(
    page_title="SecureDocker Dashboard",
    page_icon="🔐",
    layout="wide"
)

if 'theme' not in st.session_state:
    st.session_state.theme = 'Dark 🌙'

st.sidebar.markdown("### 🎨 Appearance")
selected_theme = st.sidebar.radio("Theme Selector", ["Dark 🌙", "Light ☀️"], index=0 if st.session_state.theme == 'Dark 🌙' else 1)

if selected_theme != st.session_state.theme:
    st.session_state.theme = selected_theme
    st.experimental_rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚠️ System Administration")
if st.sidebar.button("🗑️ Factory Reset Database", use_container_width=True, type="primary", help="Wipe all scan results and completely reset the engine to start a fresh presentation."):
    with st.spinner("Purging all database records..."):
        conn = connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM scan_results;")
        cur.execute("DELETE FROM images;")
        try:
            # Try to reset the auto-increment counters if they exist
            cur.execute("DELETE FROM sqlite_sequence WHERE name='scan_results';")
            cur.execute("DELETE FROM sqlite_sequence WHERE name='images';")
        except Exception:
            pass
        conn.commit()
        conn.close()
        st.session_state.page = 'welcome'
        st.sidebar.success("Database Completely Wiped! Ready for Presentation.")
        st.experimental_rerun()

if st.session_state.theme == 'Dark 🌙':
    bg_color = "#0b0f19"
    text_color = "#e2e8f0"
    header_color = "#f8fafc"
    card_bg = "rgba(30, 41, 59, 0.7)"
    card_border = "rgba(255, 255, 255, 0.05)"
    metric_val = "#38bdf8"
    metric_lbl = "#94a3b8"
    input_bg = "#1e293b"
    input_border = "#334155"
    divider = "#334155"
    sidebar_bg = "linear-gradient(180deg, #0f172a 0%, #312e81 100%)"
else:
    bg_color = "#f8fafc"
    text_color = "#1e293b"
    header_color = "#0f172a"
    card_bg = "rgba(255, 255, 255, 1)"
    card_border = "rgba(0, 0, 0, 0.1)"
    metric_val = "#0284c7"
    metric_lbl = "#475569"
    input_bg = "#ffffff"
    input_border = "#cbd5e1"
    divider = "#e2e8f0"
    sidebar_bg = "linear-gradient(180deg, #f0f9ff 0%, #dbeafe 50%, #e0e7ff 100%)"

st.markdown(
    f"""
    <style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    /* Global Body & Typography */
    .stApp {{
        background-color: {bg_color};
        font-family: 'Inter', sans-serif;
        color: {text_color};
    }}
    
    /* Sidebar Animated Gradients */
    [data-testid="stSidebar"] {{
        background: {sidebar_bg} !important;
        border-right: 1px solid {divider};
    }}
    
    [data-testid="stSidebar"] > div:first-child {{
        background: transparent !important;
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: {header_color} !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px;
    }}

    /* Metric Cards (Glassmorphism & Hover Effects) */
    div[data-testid="metric-container"] {{
        background: {card_bg};
        border: 1px solid {card_border};
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        backdrop-filter: blur(10px);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    div[data-testid="metric-container"]:hover {{
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2), 0 4px 6px -2px rgba(0, 0, 0, 0.1);
    }}
    [data-testid="stMetricValue"] {{
        font-size: 2.2rem !important;
        color: {metric_val} !important;
        font-weight: 600 !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 1.05rem !important;
        color: {metric_lbl} !important;
        font-weight: 400 !important;
    }}

    /* Buttons (Gradients & Shadows) */
    .stButton>button {{
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        letter-spacing: 0.3px;
        box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        background: linear-gradient(135deg, #ef4444, #b91c1c);
        box-shadow: 0 6px 12px rgba(239, 68, 68, 0.3);
        transform: scale(1.02);
        color: white;
    }}

    /* Inputs and Selectors */
    .stTextInput label, .stSelectbox label, .stRadio label, .stFileUploader label, p, span {{
        color: {text_color} !important;
    }}
    .stTextInput>div>div>input, .stSelectbox>div>div>div {{
        border-radius: 8px;
        border: 1px solid {input_border} !important;
        background-color: {input_bg} !important;
        color: {text_color} !important;
        transition: all 0.2s ease;
    }}
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus {{
        border-color: #38bdf8 !important;
        box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
    }}

    /* Tables */
    [data-testid="stDataFrame"] {{
        border-radius: 10px;
        border: 1px solid {divider};
        overflow: hidden;
    }}

    /* Alerts and Callouts */
    .stAlert {{
        border-radius: 10px;
        border: none;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    /* Divider */
    hr {{
        border-top: 1px solid {divider};
    }}
    </style>
    """,
    unsafe_allow_html=True
)


def set_page(page_name):
    st.session_state.page = page_name
    st.experimental_rerun()


def inject_dot_grid():
    components.html(
        '''
        <script>
            const doc = window.parent.document;
            if (!doc.getElementById('antigravity-canvas')) {
                const canvas = doc.createElement('canvas');
                canvas.id = 'antigravity-canvas';
                canvas.style.position = 'fixed';
                canvas.style.top = '0';
                canvas.style.left = '0';
                canvas.style.width = '100vw';
                canvas.style.height = '100vh';
                canvas.style.pointerEvents = 'none';
                canvas.style.zIndex = '0';
                canvas.style.transition = 'opacity 0.5s ease';
                
                const stApp = doc.querySelector('.stApp');
                if (stApp) {
                    stApp.appendChild(canvas);
                } else {
                    doc.body.appendChild(canvas);
                }

                const ctx = canvas.getContext('2d');
                let width = doc.documentElement.clientWidth;
                let height = doc.documentElement.clientHeight;
                
                function resize() {
                    width = doc.documentElement.clientWidth;
                    height = doc.documentElement.clientHeight;
                    canvas.width = width;
                    canvas.height = height;
                }
                doc.defaultView.addEventListener('resize', resize);
                resize();

                let mouse = { x: width/2, y: height/2 };

                doc.addEventListener('mousemove', (e) => {
                    mouse.x = e.clientX;
                    mouse.y = e.clientY;
                });

                function draw() {
                    ctx.clearRect(0, 0, width, height);

                    const spacing = 35;
                    const glowRadius = 250; 

                    for (let x = 0; x < width; x += spacing) {
                        for (let y = 0; y < height; y += spacing) {
                            const dx = x - mouse.x;
                            const dy = y - mouse.y;
                            const dist = Math.sqrt(dx * dx + dy * dy);

                            let opacity = 0.05; 
                            let size = 1.0; 
                            
                            if (dist < glowRadius) {
                                const intensity = 1 - (dist / glowRadius);
                                opacity = 0.05 + (intensity * 0.8);
                                size = 1.0 + (intensity * 1.5);
                            }

                            ctx.beginPath();
                            ctx.arc(x, y, size, 0, Math.PI * 2);
                            ctx.fillStyle = `rgba(56, 189, 248, ${opacity})`; 
                            ctx.fill();
                        }
                    }
                    requestAnimationFrame(draw);
                }
                draw();
            } else {
                doc.getElementById('antigravity-canvas').style.opacity = '1';
            }
        </script>
        ''',
        height=0,
        width=0
    )

def hide_dot_grid():
    components.html(
        '''
        <script>
            const doc = window.parent.document;
            const canvas = doc.getElementById('antigravity-canvas');
            if (canvas) {
                canvas.style.opacity = '0';
            }
        </script>
        ''',
        height=0,
        width=0
    )

def show_welcome():
    inject_dot_grid()
    st.markdown('''
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700&display=swap');
        
        /* The glowing mesh background effect */
        .antigravity-bg {
            position: fixed;
            top: 50%;
            left: 50%;
            width: 900px;
            height: 900px;
            background: linear-gradient(120deg, rgba(236, 72, 153, 0.2), rgba(139, 92, 246, 0.3), rgba(59, 130, 246, 0.2), rgba(20, 184, 166, 0.2));
            background-size: 200% 200%;
            border-radius: 50%;
            filter: blur(100px);
            z-index: -1;
            transform: translate(-50%, -50%);
            animation: meshGlow 8s ease infinite alternate;
        }

        @keyframes meshGlow {
            0% { background-position: 0% 50%; transform: translate(-50%, -45%) scale(1); }
            50% { background-position: 100% 50%; transform: translate(-50%, -55%) scale(1.1); }
            100% { background-position: 0% 50%; transform: translate(-50%, -45%) scale(1); }
        }

        .welcome-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 65vh;
            text-align: center;
            font-family: 'Outfit', sans-serif;
        }

        .icon-container {
            font-size: 90px;
            margin-bottom: 10px;
            animation: float 4s ease-in-out infinite, fadeInStagger 1s forwards;
            opacity: 0;
            filter: drop-shadow(0 0 30px rgba(56, 189, 248, 0.3));
        }

        /* Fluid Gradient Typography exactly like Antigravity */
        h1.welcome-title {
            font-size: 5.5rem !important;
            font-weight: 700 !important;
            letter-spacing: -2px;
            margin-bottom: 5px;
            color: transparent;
            background: linear-gradient(300deg, #ec4899, #8b5cf6, #3b82f6, #14b8a6);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -moz-background-clip: text;
            animation: fluidGradient 6s ease infinite, fadeInStagger 1s forwards 0.2s;
            opacity: 0;
        }

        p.welcome-subtitle {
            font-size: 1.4rem;
            color: #94a3b8;
            font-weight: 300;
            max-width: 600px;
            animation: fadeInStagger 1s forwards 0.4s;
            opacity: 0;
        }

        /* Button wrappers for the stagger effect */
        .btn-wrapper {
            animation: fadeInStagger 1s forwards 0.6s;
            opacity: 0;
            width: 100%;
        }

        /* Animations */
        @keyframes orbFloat {
            0% { transform: translate(-50%, -50%) scale(1); }
            100% { transform: translate(-50%, -55%) scale(1.1); }
        }

        @keyframes fluidGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes fadeInStagger {
            0% { opacity: 0; transform: translateY(30px); filter: blur(10px); }
            100% { opacity: 1; transform: translateY(0); filter: blur(0); }
        }

        @keyframes float {
            0% { transform: translateY(0px) rotate(-5deg); filter: drop-shadow(0 10px 15px rgba(56,189,248,0.2)); }
            50% { transform: translateY(-15px) rotate(5deg); filter: drop-shadow(0 25px 20px rgba(56,189,248,0.4)); }
            100% { transform: translateY(0px) rotate(-5deg); filter: drop-shadow(0 10px 15px rgba(56,189,248,0.2)); }
        }

        </style>
        
        <div class="antigravity-bg"></div>
        <div class="welcome-container">
            <div class="icon-container">🐳</div>
            <h1 class="welcome-title">Dr.Docker</h1>
            <p class="welcome-subtitle">The next generation container vulnerability and operational risk analysis engine.</p>
        </div>
        <br>
    ''', unsafe_allow_html=True)
    
    st.markdown('<div class="btn-wrapper">', unsafe_allow_html=True)
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
    
    with col1:
        if st.button("🔍 Scan New Image", use_container_width=True):
            set_page('scan_new')
            
    with col2:
        if st.button("📂 Select Existing Image", use_container_width=True):
            set_page('scan_existing')
            
    with col3:
        if st.button("⚡ Bulk Scan", use_container_width=True):
            set_page('bulk_scan')

    with col4:
        if st.button("🐳 Docker Forensics", use_container_width=True):
            set_page('forensics')

    with col5:
        if st.button("📜 Scan History", use_container_width=True):
            set_page('scan_history')
            
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
        <div style="text-align: center; margin-top: 120px; padding: 20px; opacity: 0.4;">
            <p style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 600; letter-spacing: 3px; color: {text_color}; text-transform: uppercase; margin-bottom: 0;">
                © 2026 Dr.Docker Security Labs • All Rights Reserved
            </p>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; letter-spacing: 1px; color: {text_color}; margin-top: 8px;">
                Engineered for the Next Generation of Containerized Threat Analysis.
            </p>
        </div>
    """, unsafe_allow_html=True)

def show_dashboard(active_tab):
    hide_dot_grid()
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
    if active_tab == 'scan_new':
        st.subheader("🔍 Scan New Image")

        scan_mode = st.radio("Choose Scan Method:", ["From Registry (Name/URL)", "Upload Archive (.tar)"])
        
        user_image = None
        uploaded_file = None
        
        if scan_mode == "From Registry (Name/URL)":
            user_image = st.text_input("Docker Target URL (e.g. redis, nginx)", help="Type the exact library name or external registry URL tag here.")
        else:
            uploaded_file = st.file_uploader("Upload Docker Image Archive (.tar)", type=["tar"])

        if st.button("Scan Now"):
            from scanner.parser import parse_and_store
            from risk_engine import update_risk

            if scan_mode == "From Registry (Name/URL)" and user_image:
                with st.spinner(f"🔄 Scanning {user_image}... please wait"):
                    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
                        json_file_path = tmp_file.name

                    try:
                        subprocess.run(["trivy", "image", "-f", "json", "-o", json_file_path, user_image], check=True)

                        conn = connect()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO images(name,pulls,last_updated) VALUES (?,?,?)",
                            (user_image, 0, "manual")
                        )
                        image_id = cursor.lastrowid
                        conn.commit()
                        conn.close()

                        parse_and_store(image_id, json_file=json_file_path)
                        update_risk(image_id)
                        st.success("✅ Scan completed!")
                    except Exception as e:
                        st.error("❌ Scan failed! Trivy was unable to locate or index this container architecture.")
                    finally:
                        if os.path.exists(json_file_path):
                            os.remove(json_file_path)

            elif scan_mode == "Upload Archive (.tar)" and uploaded_file is not None:
                with st.spinner(f"🔄 Scanning uploaded archive {uploaded_file.name}... please wait"):
                    with tempfile.NamedTemporaryFile(suffix=".tar", delete=False) as tmp_tar:
                        tmp_tar.write(uploaded_file.getbuffer())
                        tar_path = tmp_tar.name

                    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
                        json_file_path = tmp_file.name

                    try:
                        subprocess.run(["trivy", "image", "--input", tar_path, "-f", "json", "-o", json_file_path], check=True)

                        image_name = f"uploaded_{uploaded_file.name}"
                        conn = connect()
                        cursor = conn.cursor()
                        cursor.execute(
                            "INSERT INTO images(name,pulls,last_updated) VALUES (?,?,?)",
                            (image_name, 0, "manual_upload")
                        )
                        image_id = cursor.lastrowid
                        conn.commit()
                        conn.close()

                        parse_and_store(image_id, json_file=json_file_path)
                        update_risk(image_id)
                        st.success("✅ Scan completed!")
                    except Exception as e:
                        st.error(f"❌ Scan failed! The uploaded archive {uploaded_file.name} may be corrupted or invalid.")
                    finally:
                        if os.path.exists(json_file_path):
                            os.remove(json_file_path)
                        if os.path.exists(tar_path):
                            os.remove(tar_path)
            else:
                st.warning("⚠️ Please provide an image name or upload an archive before scanning.")

    # -----------------------------
    # SELECT EXISTING IMAGE
    # -----------------------------
    if active_tab == 'scan_existing':
        st.subheader("📂 Select Existing Image")

        # --> NEW SYNC FEATURE <--
        st.markdown("##### 🌐 Sync from Docker Hub")
        colA, colB = st.columns([3, 1])
        with colA:
            sync_limit = st.slider("Number of trending images to fetch", min_value=10, max_value=100, step=10, value=20)
        with colB:
            st.write("")
            st.write("")
            if st.button("Sync Now", use_container_width=True):
                with st.spinner(f"Syncing top {sync_limit} images..."):
                    from collector.collector import collect_images
                    success = collect_images(limit=sync_limit)
                    if success:
                        st.success(f"Synced {sync_limit} images!")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to sync images.")
        
        st.markdown("---")
        # --> END SYNC FEATURE <--

        conn = connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM images")
        db_results = cursor.fetchall()
        conn.close()
        
        if not db_results:
            st.warning("⚠️ No images found in database. The database is currently empty.")
            st.info("💡 Presentation Tip: Use the 'Scan New Image' tab to manually index an image, or use 'Bulk Scan' to automatically populate the database with top commercial registries.")
        else:
            image_list = [row[0] for row in db_results]
            selected_image = st.selectbox("Choose Image from Database", image_list)

            if st.button("Scan Selected Image"):

                with st.spinner(f"🔄 Scanning {selected_image}..."):
                    from scanner.parser import parse_and_store
                    from risk_engine import update_risk

                    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_file:
                        json_file_path = tmp_file.name

                    try:
                        subprocess.run(["trivy", "image", "-f", "json", "-o", json_file_path, selected_image], check=True)

                        conn = connect()
                        cursor = conn.cursor()
                        cursor.execute("SELECT id FROM images WHERE name=?", (selected_image,))
                        image_id = cursor.fetchone()[0]
                        conn.close()

                        parse_and_store(image_id, json_file=json_file_path)
                        update_risk(image_id)
                        st.success("✅ Scan completed!")
                    except Exception as e:
                        st.error("❌ Scan failed! The image engine could not retrieve the manifest. Please check if this registry name is valid.")
                    finally:
                        if os.path.exists(json_file_path):
                            os.remove(json_file_path)

    # -----------------------------
    # BULK SCAN BUTTON 🔥
    # -----------------------------
    if active_tab == 'bulk_scan':
        st.subheader("⚡ Bulk Scan (Large Scale)")

        if st.button("Run Bulk Scan (10 Images)"):
            from bulk_scanner import scan_bulk

            with st.spinner("🔄 Running bulk scan..."):
                scan_bulk(10)

            st.success("✅ Bulk scan completed!")

    # -----------------------------
    # DOCKER FORENSICS
    # -----------------------------
    if active_tab == 'forensics':
        st.subheader("🐳 Docker Image Forensics & Anatomy (Offline)")
        st.info("Because this module interacts natively with your physical Docker Daemon Engine to extract layers, you must ensure Docker Desktop is running locally.")
        
        forensic_image = st.text_input("Target Image Registry URL (e.g. redis:latest)", help="Type the registry name exactly as it appears in Docker Desktop.")
        
        if st.button("Extract Layers & Configurations"):
            if forensic_image:
                with st.spinner(f"Initiating deep teardown of {forensic_image}..."):
                    from scanner.forensics import analyze_docker_smells, extract_image_history
                    
                    smells = analyze_docker_smells(forensic_image)
                    layers = extract_image_history(forensic_image)
                    
                    if not layers:
                        st.error(f"Failed to extract {forensic_image}. Ensure Docker Desktop is running and image is accessible.")
                    else:
                        st.success("Tear-down Complete! See anatomical details below.")
                        
                        colA, colB = st.columns(2)
                        with colA:
                            st.markdown("### ⚠️ Configuration 'Smells'")
                            if smells['uses_latest_tag']:
                                st.warning("Tag: Uses volatile ':latest' tag (Implicit mutable dependency)")
                            else:
                                st.success("Tag: Uses pinned version tag")
                                
                            if smells['runs_as_root']:
                                st.error("User: Container runs as **ROOT**! Severe Isolation Risk.")
                            else:
                                st.success("User: Non-root user specified.")
                                
                            if smells['exposed_ports']:
                                st.info(f"Ports Exposed: {', '.join(smells['exposed_ports'])}")
                            else:
                                st.write("Ports Exposed: None explicitly declared")
                        
                        with colB:
                            st.markdown("### 🧩 Environmental Anomalies")
                            if smells['env_vars']:
                                st.write("Declared Environment Keys:")
                                st.code('\\n'.join(smells['env_vars']))
                            else:
                                st.write("No configured environment variables found.")
                                
                        st.markdown("---")
                        st.markdown("---")
                        
                        with st.expander("🧬 View Full Image Layer Ancestry Tree", expanded=False):
                            st.write(f"The image depends on {len(layers)} distinct filesystem layers mapped below:")
                            # Removed local import of pandas to fix UnboundLocalError
                            df_layers = pd.DataFrame(layers)
                            st.dataframe(df_layers[['id', 'size', 'created', 'command']], use_container_width=True)

    # -----------------------------
    # SCAN HISTORY (Full Audit Trail)
    # -----------------------------
    if active_tab == 'scan_history':
        st.subheader("📜 Full Scan History & Audit Trail")
        st.info("This view shows **every** scan ever recorded in the database, including duplicate scans. Use this as your complete forensic audit log.")

        conn_hist = connect()
        cursor_hist = conn_hist.cursor()
        cursor_hist.execute("""
            SELECT s.rowid as scan_id, i.name, s.critical, s.high, s.medium, s.low,
                   s.secrets, s.risk_score, s.risk_level, i.last_updated
            FROM images i
            JOIN scan_results s ON i.id = s.image_id
            ORDER BY s.rowid DESC
        """)
        hist_rows = cursor_hist.fetchall()
        conn_hist.close()

        hist_cols = ["Scan #", "Image", "Critical", "High", "Medium", "Low", "Secrets", "Risk Score", "Risk Level", "Timestamp"]
        hist_df = pd.DataFrame(hist_rows, columns=hist_cols)

        if hist_df.empty:
            st.warning("No scan history found. Please scan an image first.")
        else:
            # Summary metrics
            hcol1, hcol2, hcol3, hcol4 = st.columns(4)
            hcol1.metric("Total Scans Recorded", len(hist_df))
            hcol2.metric("Unique Images Scanned", hist_df["Image"].nunique())
            hcol3.metric("Most Scanned Image", hist_df["Image"].value_counts().index[0])
            hcol4.metric("Latest Risk Level", hist_df.iloc[0]["Risk Level"])

            st.markdown("---")

            # Per-image expandable history
            st.subheader("🔎 Per-Image Scan Timeline")
            unique_images = hist_df["Image"].unique()
            for img_name in unique_images:
                img_hist = hist_df[hist_df["Image"] == img_name]
                latest_level = img_hist.iloc[0]["Risk Level"]
                scan_count = len(img_hist)
                with st.expander(f"{img_name} — {scan_count} scan(s) — Latest: {latest_level}", expanded=False):
                    st.dataframe(
                        img_hist[["Scan #", "Critical", "High", "Medium", "Low", "Secrets", "Risk Score", "Risk Level", "Timestamp"]],
                        use_container_width=True
                    )

            st.markdown("---")

            # Full raw table
            with st.expander("📋 View Complete Raw Audit Log", expanded=False):
                st.dataframe(hist_df, use_container_width=True)

    st.markdown("---")

    # -----------------------------
    # FETCH DATA (Latest scan per image only)
    # -----------------------------
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT i.name, s.critical, s.high, s.medium, s.low,
               s.secrets, s.risk_score, s.risk_level
        FROM images i
        JOIN scan_results s ON i.id = s.image_id
        WHERE s.rowid = (
            SELECT MAX(s2.rowid)
            FROM scan_results s2
            WHERE s2.image_id = i.id
        )
    """)

    rows = cursor.fetchall()
    conn.close()

    # -----------------------------
    # DATAFRAME
    # -----------------------------
    columns = ["Image", "Critical", "High", "Medium", "Low", "Secrets", "Risk Score", "Risk Level"]
    df = pd.DataFrame(rows, columns=columns)
    df = df.drop_duplicates(subset=["Image"], keep="first")
    df = df.sort_values(by="Risk Score", ascending=False)

    if df.empty:
        st.warning("⚠️ No scan data available. Please scan an image.")

    # -----------------------------
    # TOP RISKY
    # -----------------------------
    st.subheader("🏆 Top Risky Images")
    top_risky = df.head(5)
    st.dataframe(top_risky[["Image", "Risk Score", "Risk Level"]], use_container_width=True)

    # -----------------------------
    # METRICS
    # -----------------------------
    st.subheader("📊 Overview")

    # Fetch Latest Scan Result
    conn_latest = connect()
    cursor_latest = conn_latest.cursor()
    cursor_latest.execute("""
        SELECT i.name, s.risk_score, s.risk_level
        FROM images i
        JOIN scan_results s ON i.id = s.image_id
        ORDER BY s.rowid DESC LIMIT 1
    """)
    latest_scan = cursor_latest.fetchone()
    conn_latest.close()
    
    if latest_scan:
        name, score, level = latest_scan
        color = "red" if level == "CRITICAL" else "orange" if level == "HIGH" else "yellow" if level == "MEDIUM" else "green"
        st.info(f"💥 **LATEST SCAN COMPLETED:** `{name}` | Risk Score: **{score}** | Level: **{level}**")

    # Fetch Cumulative Historical Stats
    conn_stats = connect()
    cur_stats = conn_stats.cursor()
    cur_stats.execute("SELECT COUNT(*), SUM(critical), SUM(high), AVG(risk_score) FROM scan_results")
    raw_stats = cur_stats.fetchone()
    conn_stats.close()
    
    tot_scans = raw_stats[0] if raw_stats[0] else 0
    tot_crit = raw_stats[1] if raw_stats[1] else 0
    tot_high = raw_stats[2] if raw_stats[2] else 0
    avg_score = int(raw_stats[3]) if raw_stats[3] else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Scans Processed", tot_scans, help="Total number of container scans evaluated cumulatively over time.")
    col2.metric("Total Critical Hits", int(tot_crit), help="Cumulative count of CRITICAL vulnerabilities detected.")
    col3.metric("Total High Hits", int(tot_high), help="Cumulative count of HIGH severity findings.")
    col4.metric("Historic Avg Risk", avg_score, help="The historical moving average of risk scores detected by the engine.")

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
        ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
        help="Quick-filter the database to only show images of a specific threat level."
    )

    if risk_filter != "ALL":
        filtered_df = df[df["Risk Level"] == risk_filter]
    else:
        filtered_df = df

    # -----------------------------
    # TABLE ACCORDION
    # -----------------------------
    with st.expander("📋 View Raw Database CSV Feed", expanded=False):
        st.write(f"Showing {len(filtered_df)} results in database.")
        st.dataframe(filtered_df, use_container_width=True)

    st.markdown("---")

    # -----------------------------
    # RISK STATUS (Deduplicated & Grouped)
    # -----------------------------
    st.subheader("🚨 Risk Status")

    risk_groups = filtered_df.groupby(["Risk Level", "Image"]).size().reset_index(name="Scan Count")
    risk_groups = risk_groups.sort_values(by="Risk Level", ascending=True,
                                          key=lambda x: x.map({"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "PENDING": 4}))

    for _, grp in risk_groups.iterrows():
        label = grp["Image"]
        count_str = f" ×{grp['Scan Count']}" if grp["Scan Count"] > 1 else ""
        if grp["Risk Level"] == "CRITICAL":
            st.error(f"🚨 {label}{count_str} → CRITICAL RISK")
        elif grp["Risk Level"] == "HIGH":
            st.warning(f"⚠️ {label}{count_str} → HIGH RISK")
        elif grp["Risk Level"] == "MEDIUM":
            st.info(f"ℹ️ {label}{count_str} → MEDIUM RISK")
        else:
            st.success(f"✅ {label}{count_str} → LOW RISK")

    st.markdown("---")

    # -----------------------------
    # DECISION SYSTEM & POLICY ENGINE
    # -----------------------------
    st.subheader("🚦 Deployment Policy Engine")

    policy_df = filtered_df.drop_duplicates(subset=["Image"], keep="first")
    for index, row in policy_df.iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        img_name = row["Image"]

        with col1:
            if row["Risk Level"] == "CRITICAL":
                st.error(f"❌ {img_name} → BLOCK DEPLOYMENT")
            elif row["Risk Level"] == "HIGH":
                st.warning(f"⚠️ {img_name} → REVIEW BEFORE DEPLOY")
            elif row["Risk Level"] == "MEDIUM":
                st.info(f"ℹ️ {img_name} → CAN DEPLOY WITH CAUTION")
            else:
                st.success(f"✅ {img_name} → SAFE TO DEPLOY")
                
        with col2:
            st.write("") # Padding
            if st.button(f"🚀 Deploy", key=f"deploy_{index}", help="Simulate a production intercept. The Policy Engine runs logic to refuse or allow this spawn."):
                with st.spinner(f"Enforcing policy on {img_name}..."):
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    try:
                        from policy_engine.enforcer import run_secure_container
                        success, str_msg = run_secure_container(img_name)
                        if success:
                            st.success(str_msg)
                        else:
                            st.error(str_msg)
                    except Exception as e:
                        st.error(f"Engine Error: {e}")

        with col3:
            st.write("") # Padding
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            try:
                from scanner.reporting import generate_audit_report
                report_data = generate_audit_report(img_name)
                safe_name = img_name.replace(':', '_').replace('/', '_')
                st.download_button(
                    label="📄 Download Audit",
                    data=report_data,
                    file_name=f"{safe_name}_audit_report.txt",
                    mime="text/plain",
                    key=f"dl_{index}",
                    help="Auto-generates a text-based Security Audit file containing CVE distributions to hand to evaluators."
                )
            except Exception as e:
                st.error(f"Report Gen Error: {e}")

    st.markdown("---")

    # -----------------------------
    # CHARTS & DATA STORYTELLING
    # -----------------------------
    import altair as alt

    st.subheader("📈 Vulnerability Distribution (By Severity)")
    
    if len(df) > 0:
        # Melt dataframe to stack the colors correctly in Altair
        melted_df = df.reset_index().melt(
            id_vars=["Image"], 
            value_vars=["Critical", "High", "Medium", "Low"], 
            var_name="Severity", value_name="Count"
        )
        # Filter out 0 counts for a cleaner chart
        melted_df = melted_df[melted_df["Count"] > 0]
        
        domain = ["Critical", "High", "Medium", "Low"]
        range_colors = ["#e11d48", "#f97316", "#eab308", "#3b82f6"] # Red, Orange, Yellow, Blue
        
        dist_chart = alt.Chart(melted_df).mark_bar().encode(
            x=alt.X('Image:N', title="", sort="-y"),
            y=alt.Y('sum(Count):Q', title="Total Vulnerabilities"),
            color=alt.Color('Severity:N', scale=alt.Scale(domain=domain, range=range_colors)),
            tooltip=["Image", "Severity", "Count"]
        ).interactive()

        st.altair_chart(dist_chart, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)
        colA, colB = st.columns(2)
        
        with colA:
            st.subheader("🥧 Risk Level Distribution")
            
            pie_domain = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "PENDING"]
            pie_range = ["#e11d48", "#f97316", "#eab308", "#3b82f6", "#94a3b8"]
            
            risk_pie = alt.Chart(df).mark_arc(innerRadius=60, cornerRadius=5).encode(
                theta=alt.Theta(field="Risk Level", aggregate="count"),
                color=alt.Color(field="Risk Level", type="nominal", scale=alt.Scale(domain=pie_domain, range=pie_range)),
                tooltip=["Risk Level", "count()"]
            ).interactive()
            st.altair_chart(risk_pie, use_container_width=True)
            
        with colB:
            st.subheader("🎯 Risk Score vs Total Vulns")
            df["Total_Vulns"] = df[["Critical", "High", "Medium", "Low"]].sum(axis=1)
            scatter = alt.Chart(df).mark_circle(size=120).encode(
                x=alt.X('Total_Vulns:Q', title="Total CVEs Found"),
                y=alt.Y('Risk Score:Q', title="Final Severity Score"),
                color=alt.Color('Risk Level:N', scale=alt.Scale(domain=pie_domain, range=pie_range)),
                tooltip=["Image", "Risk Score", "Total_Vulns"]
            ).interactive()
            st.altair_chart(scatter, use_container_width=True)
    else:
        st.info("No data available to generate charts. Please scan an image first.")

    st.markdown("---")

    # -----------------------------
    # FOOTER
    # -----------------------------
    st.markdown(f"""
        <hr style="border-color: rgba(255,255,255,0.05); margin-top: 4rem;">
        <div style="text-align: center; margin-top: 20px; padding: 20px; opacity: 0.4;">
            <p style="font-family: 'Inter', sans-serif; font-size: 0.75rem; font-weight: 600; letter-spacing: 3px; color: {text_color}; text-transform: uppercase; margin-bottom: 0;">
                © 2026 Dr.Docker Security Labs • All Rights Reserved
            </p>
            <p style="font-family: 'Inter', sans-serif; font-size: 0.7rem; letter-spacing: 1px; color: {text_color}; margin-top: 8px;">
                Engineered for the Next Generation of Containerized Threat Analysis.
            </p>
        </div>
    """, unsafe_allow_html=True)
# Main routing logic
if 'page' not in st.session_state:
    st.session_state.page = 'welcome'

if st.session_state.page == 'welcome':
    show_welcome()
else:
    # Add a back button
    if st.button("⬅️ Back to Home"):
        set_page('welcome')
    show_dashboard(st.session_state.page)
