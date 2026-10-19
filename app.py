import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import io
import requests
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import os


BOT_TOKEN = "8776310870:AAGbPtWtVcZUhxI3p04NmdCB0UG6G6rW5VM"
CHAT_ID = "8589780398"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
        return True
    except Exception as e:
        print("Telegram Error:", e)
        return False

# ---- HTTP receiver ----
DATA_FILE = "latest_sensor_data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"mq2": 0, "mq135_alert": 0, "gas_detected": 0, "timestamp": "N/A"}, f)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length)
        data = json.loads(body)
        data["timestamp"] = datetime.now().strftime("%H:%M:%S")
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        pass

def run_server():
    server = HTTPServer(("0.0.0.0", 8502), Handler)
    server.serve_forever()

if "server_started" not in st.session_state:
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    st.session_state.server_started = True

# ---- Read latest data (must be before sidebar) ----
try:
    with open(DATA_FILE, "r") as f:
        latest_data = json.load(f)
except:
    latest_data = {"mq2": 0, "mq135_alert": 0, "gas_detected": 0, "timestamp": "N/A"}

# Page configuration
st.set_page_config(
    page_title="Fume-Finder | Lab Safety Monitor",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- SESSION STATE ---------------- #
if 'history' not in st.session_state:
    st.session_state.history = []
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = []
if 'sound_played' not in st.session_state:
    st.session_state.sound_played = False
if 'last_telegram_alert' not in st.session_state:
    st.session_state.last_telegram_alert = 0
if 'last_alert_logged' not in st.session_state:
    st.session_state.last_alert_logged = False
if 'notifications' not in st.session_state:
    st.session_state.notifications = []

# ---- CSS ----
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #f0f2f5;
    }

    section[data-testid="stSidebar"] {
        background-color: #1a1f2e;
        border-right: 1px solid #2d3548;
    }
    section[data-testid="stSidebar"] * {
        color: #c8d0e0 !important;
    }
    section[data-testid="stSidebar"] .stSlider label,
    section[data-testid="stSidebar"] .stCheckbox label {
        color: #c8d0e0 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #ffffff !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] .stButton > button {
        background-color: #2d3548;
        color: #c8d0e0 !important;
        border: 1px solid #3d4a6a;
        border-radius: 6px;
        width: 100%;
        font-size: 0.8rem;
        padding: 0.4rem 0.8rem;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #3d4a6a;
        border-color: #5a6fa0;
    }

    /* Main content cards */
    .ff-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 24px;
        border: 1px solid #e2e6ed;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        margin-bottom: 16px;
    }

    /* Zone cards */
    .zone-card {
        border-radius: 10px;
        padding: 24px 16px;
        text-align: center;
        height: 100%;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .zone-label {
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 4px;
        color: #6b7280;
    }
    .zone-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 12px;
    }
    .zone-value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 2.4rem;
        font-weight: 700;
        line-height: 1;
        margin: 8px 0;
    }
    .zone-sub {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1rem;
        margin: 4px 0;
    }
    .zone-status {
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 10px;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
    }
    .zone-ts {
        font-size: 0.72rem;
        color: #9ca3af;
        margin-top: 8px;
    }

    /* Zone states */
    .zone-safe   { background: #f0fdf4; border: 1.5px solid #86efac; }
    .zone-warn   { background: #fffbeb; border: 1.5px solid #fcd34d; }
    .zone-danger { background: #fff1f2; border: 1.5px solid #fca5a5; box-shadow: 0 0 0 3px rgba(239,68,68,0.12); }
    .zone-idle   { background: #eef2ff; border: 1.5px dashed #a5b4fc; }

    .badge-safe   { background: #dcfce7; color: #166534; }
    .badge-warn   { background: #fef9c3; color: #92400e; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    .badge-idle   { background: #e0e7ff; color: #3730a3; }

    /* Floor plan */
    .fp-cell {
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .fp-safe   { background: #f0fdf4; border: 1.5px solid #86efac; color: #166534; }
    .fp-danger { background: #fff1f2; border: 2px solid #f87171;   color: #991b1b; }
    .fp-idle   { background: #eef2ff; border: 1.5px dashed #a5b4fc; color: #3730a3; }
    .fp-wait   { background: #fffbeb; border: 1.5px solid #fcd34d; color: #92400e; }

    /* Notification toast */
    .notif-toast {
        background: #1a1f2e;
        color: #e2e8f0;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 12px 16px;
        font-size: 0.82rem;
        margin-bottom: 8px;
        font-family: 'Inter', sans-serif;
    }
    .notif-toast.notif-alert {
        border-left-color: #ef4444;
    }
    .notif-toast.notif-telegram {
        border-left-color: #3b82f6;
    }
    .notif-toast.notif-ok {
        border-left-color: #22c55e;
    }
    .notif-time {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        color: #64748b;
        margin-bottom: 2px;
    }

    /* Section header */
    .section-header {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 12px;
        padding-bottom: 6px;
        border-bottom: 1px solid #e5e7eb;
    }

    /* Metric override */
    [data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e6ed;
        border-radius: 10px;
        padding: 16px !important;
    }

    /* Page header bar */
    .page-header {
        background: #1a1f2e;
        border-radius: 12px;
        padding: 20px 32px;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .page-header-title {
        font-size: 1.4rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.01em;
    }
    .page-header-sub {
        font-size: 0.78rem;
        color: #94a3b8;
        margin-top: 2px;
    }
    .page-header-badge {
        background: #22c55e22;
        border: 1px solid #22c55e55;
        color: #4ade80;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 4px 12px;
        border-radius: 20px;
        letter-spacing: 0.06em;
    }
    .page-header-badge.badge-waiting {
        background: #f59e0b22;
        border-color: #f59e0b55;
        color: #fbbf24;
    }

    /* Dark mode overrides */
    .dark-mode .stApp { background-color: #0f1117 !important; }
    .dark-mode .ff-card { background: #1a1f2e !important; border-color: #2d3548 !important; }
    </style>
""", unsafe_allow_html=True)

# Dark mode
if st.session_state.get("dark_mode", False):
    st.markdown("""<style>
    .stApp { background-color: #0f1117 !important; }
    .ff-card { background: #1a1f2e !important; border-color: #2d3548 !important; }
    .zone-safe   { background: #0d2416 !important; border-color: #166534 !important; }
    .zone-warn   { background: #1c1600 !important; border-color: #92400e !important; }
    .zone-danger { background: #1c0a0a !important; border-color: #991b1b !important; }
    .zone-idle   { background: #0f1240 !important; border-color: #3730a3 !important; }
    .zone-title, .zone-value, .zone-sub { color: #e2e8f0 !important; }
    .zone-ts { color: #64748b !important; }
    [data-testid="stMetric"] { background: #1a1f2e !important; border-color: #2d3548 !important; }
    </style>""", unsafe_allow_html=True)

if 'last_incident' not in st.session_state:
    st.session_state.last_incident = datetime.now()

# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("### 🔬 Fume-Finder")
    st.markdown('<div style="height:1px;background:#2d3548;margin:8px 0 16px;"></div>', unsafe_allow_html=True)

    dark_mode = st.toggle("Dark Mode", value=st.session_state.get("dark_mode", False))
    st.session_state.dark_mode = dark_mode

    st.markdown('<div style="height:1px;background:#2d3548;margin:16px 0;"></div>', unsafe_allow_html=True)
    st.markdown("### ⚠️ Thresholds")
    danger_threshold  = st.slider("Danger level (raw)", 100, 1000, 300)
    warning_threshold = st.slider("Warning level (raw)", 50, 500, 150)

    st.markdown('<div style="height:1px;background:#2d3548;margin:16px 0;"></div>', unsafe_allow_html=True)
    st.markdown("### 🔄 Refresh")
    auto_refresh     = st.checkbox("Auto-refresh", value=True)
    refresh_interval = st.slider("Interval (sec)", 1, 10, 3, disabled=not auto_refresh)

    st.markdown('<div style="height:1px;background:#2d3548;margin:16px 0;"></div>', unsafe_allow_html=True)
    st.markdown("### 📊 Export")
    if st.button("Export CSV"):
        if st.session_state.history:
            df_export = pd.DataFrame(st.session_state.history)
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="Download",
                data=csv,
                file_name=f"fumefinder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("No data yet")

    if st.button("Clear History"):
        st.session_state.alert_history = []
        st.session_state.history = []
        st.session_state.notifications = []
        st.rerun()

    st.markdown('<div style="height:1px;background:#2d3548;margin:16px 0;"></div>', unsafe_allow_html=True)
    st.markdown("### 🖥️ System")
    node_online = latest_data["timestamp"] != "N/A"
    st.markdown(f'<div style="color:{"#4ade80" if node_online else "#fbbf24"};font-size:0.8rem;">● {"Node 1 Online" if node_online else "Awaiting Node 1"}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:#94a3b8;font-size:0.75rem;margin-top:4px;">Danger: {danger_threshold} &nbsp;|&nbsp; Warning: {warning_threshold}</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:#64748b;font-size:0.72rem;margin-top:4px;">{datetime.now().strftime("%d %b %Y, %H:%M:%S")}</div>', unsafe_allow_html=True)

    st.markdown('<div style="height:1px;background:#2d3548;margin:16px 0;"></div>', unsafe_allow_html=True)
    st.markdown('<div style="color:#475569;font-size:0.7rem;">RV College of Engineering<br>Interdisciplinary Project · 2026</div>', unsafe_allow_html=True)

# ---- DATA ----
mq2_val      = latest_data.get("mq2", 0)
mq135_alert  = latest_data.get("mq135_alert", 0)
gas_detected = latest_data.get("gas_detected", 0)
timestamp    = latest_data.get("timestamp", "N/A")
zone1_online = timestamp != "N/A"

if not zone1_online:
    zone1_state = "idle";   zone1_text = "AWAITING SIGNAL"; zone1_display = "—"
elif gas_detected or mq2_val > danger_threshold:
    zone1_state = "danger"; zone1_text = "GAS DETECTED";    zone1_display = str(mq2_val)
elif mq2_val > warning_threshold:
    zone1_state = "warn";   zone1_text = "ELEVATED";        zone1_display = str(mq2_val)
else:
    zone1_state = "safe";   zone1_text = "NORMAL";          zone1_display = str(mq2_val)

risk_score = min((mq2_val / danger_threshold) * 100, 100) if danger_threshold else 0

st.session_state.history.append({
    'Time': timestamp,
    'MQ2 Raw': mq2_val,
    'MQ135 Alert': mq135_alert,
    'Gas Detected': gas_detected,
    'Risk Score (%)': round(risk_score, 1),
    'Status': zone1_text
})
if len(st.session_state.history) > 50:
    st.session_state.history.pop(0)

# ---- TELEGRAM + NOTIFICATIONS ----
current_time = time.time()
telegram_sent_this_cycle = False
if (gas_detected or mq2_val > danger_threshold) and (current_time - st.session_state.last_telegram_alert > 30):
    alert_msg = f"""🚨 *GAS LEAK ALERT* 🚨\n\n📍 Zone: Zone 1\n📊 MQ-2 Raw: {mq2_val}\n🧪 MQ-135: {"ALERT" if mq135_alert else "CLEAR"}\n🕒 Time: {timestamp}\n\n❗ Immediate action required!"""
    success = send_telegram_alert(alert_msg)
    st.session_state.last_telegram_alert = current_time
    telegram_sent_this_cycle = True
    st.session_state.notifications.insert(0, {
        "type": "telegram",
        "msg": f"Telegram alert dispatched — Zone 1 · MQ-2: {mq2_val}",
        "time": datetime.now().strftime("%H:%M:%S")
    })

if (gas_detected or mq2_val > danger_threshold) and not st.session_state.last_alert_logged:
    st.session_state.alert_history.append({
        'time': timestamp, 'zone': 'Zone 1',
        'value': mq2_val, 'mq135': mq135_alert, 'risk_score': risk_score
    })
    st.session_state.last_alert_logged = True
    st.session_state.notifications.insert(0, {
        "type": "alert",
        "msg": f"Gas leak recorded in alert log — Zone 1 · Risk: {risk_score:.0f}%",
        "time": datetime.now().strftime("%H:%M:%S")
    })
elif not gas_detected and mq2_val <= danger_threshold:
    if st.session_state.last_alert_logged:
        st.session_state.notifications.insert(0, {
            "type": "ok",
            "msg": "Zone 1 returned to safe levels",
            "time": datetime.now().strftime("%H:%M:%S")
        })
    st.session_state.last_alert_logged = False

# keep only last 20 notifications
st.session_state.notifications = st.session_state.notifications[:20]

# ---- PAGE HEADER ----
node_badge_class = "page-header-badge" if zone1_online else "page-header-badge badge-waiting"
node_badge_text  = "● SYSTEM ACTIVE" if zone1_online else "● AWAITING NODE"
st.markdown(f"""
<div class="page-header">
    <div>
        <div class="page-header-title">🔬 Fume-Finder</div>
        <div class="page-header-sub">Smart Laboratory Gas Leak Detection &amp; Localization System &nbsp;·&nbsp; RV College of Engineering</div>
    </div>
    <div class="{node_badge_class}">{node_badge_text}</div>
</div>
""", unsafe_allow_html=True)

# ---- ALERT BANNER ----
alert_count = len([a for a in st.session_state.alert_history if a.get('value', 0) > danger_threshold])
if alert_count > 3:
    st.error(f"🚨 **ESCALATION — {alert_count} consecutive alerts recorded. Evacuate immediately.**")
elif gas_detected or mq2_val > danger_threshold:
    st.error("🚨 **Gas leak detected in Zone 1. Telegram alert dispatched.**")
elif mq2_val > warning_threshold:
    st.warning("⚠️ **Elevated gas levels in Zone 1. Monitoring closely.**")
else:
    st.success("✅ All monitored zones within safe parameters.")

st.markdown("---")

# ---- RISK + STATUS ROW ----
col_risk1, col_risk2, col_risk3 = st.columns([2, 1, 1])

with col_risk1:
    st.markdown('<div class="section-header">Risk Assessment</div>', unsafe_allow_html=True)
    st.progress(risk_score / 100)
    if risk_score > 80:
        st.error(f"**Critical** — {risk_score:.0f}% · Immediate action required")
    elif risk_score > 50:
        st.warning(f"**High** — {risk_score:.0f}% · Monitor closely")
    elif risk_score > 20:
        st.info(f"**Moderate** — {risk_score:.0f}% · Normal monitoring")
    else:
        st.success(f"**Low** — {risk_score:.0f}% · Safe conditions")

with col_risk2:
    st.markdown('<div class="section-header">Signal Quality</div>', unsafe_allow_html=True)
    if zone1_online:
        st.markdown(f"""<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:12px 16px;">
            <div style="font-size:0.72rem;font-weight:600;color:#166534;letter-spacing:0.08em;">● CONNECTED</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:#374151;margin-top:4px;">Last packet: {timestamp}</div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""<div style="background:#fffbeb;border:1px solid #fcd34d;border-radius:8px;padding:12px 16px;">
            <div style="font-size:0.72rem;font-weight:600;color:#92400e;letter-spacing:0.08em;">⏳ WAITING</div>
            <div style="font-size:0.78rem;color:#6b7280;margin-top:4px;">No packets received</div>
        </div>""", unsafe_allow_html=True)

with col_risk3:
    st.markdown('<div class="section-header">Node Status</div>', unsafe_allow_html=True)
    st.markdown(f"""<div style="background:#{'f0fdf4' if zone1_online else 'fffbeb'};border:1px solid #{'86efac' if zone1_online else 'fcd34d'};border-radius:8px;padding:12px 16px;">
        <div style="font-size:0.72rem;font-weight:600;color:#{'166534' if zone1_online else '92400e'};letter-spacing:0.08em;">{'● NODE 1 ACTIVE' if zone1_online else '⏳ NODE 1 PENDING'}</div>
        <div style="font-size:0.78rem;color:#6b7280;margin-top:4px;">Nodes 2–3: central unit pending</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ---- ZONE CARDS ----
st.markdown('<div class="section-header">Sensor Zones</div>', unsafe_allow_html=True)
zcol1, zcol2, zcol3 = st.columns(3)

with zcol1:
    st.markdown(f"""
    <div class="zone-card zone-{zone1_state}">
        <div class="zone-label">Zone 1 · Active Node</div>
        <div class="zone-title">Lab Section A</div>
        <div class="zone-value" style="color:{'#dc2626' if zone1_state=='danger' else '#d97706' if zone1_state=='warn' else '#16a34a' if zone1_state=='safe' else '#4338ca'};">{zone1_display}</div>
        <div class="zone-sub" style="color:#6b7280;">MQ-135: {"🔴 GAS" if mq135_alert else "🟢 Clear"}</div>
        <div class="zone-status badge-{zone1_state}">{zone1_text}</div>
        <div class="zone-ts">Updated {timestamp}</div>
    </div>
    """, unsafe_allow_html=True)

with zcol2:
    st.markdown("""
    <div class="zone-card zone-idle">
        <div class="zone-label">Zone 2 · Pending</div>
        <div class="zone-title">Lab Section B</div>
        <div style="font-size:2rem;margin:12px 0;">📡</div>
        <div class="zone-sub" style="color:#4338ca;font-size:0.85rem;">Node hardware ready</div>
        <div class="zone-status badge-idle">AWAITING LINK</div>
        <div class="zone-ts">Central unit integration pending</div>
    </div>
    """, unsafe_allow_html=True)

with zcol3:
    st.markdown("""
    <div class="zone-card zone-idle">
        <div class="zone-label">Zone 3 · Pending</div>
        <div class="zone-title">Lab Section C</div>
        <div style="font-size:2rem;margin:12px 0;">📡</div>
        <div class="zone-sub" style="color:#4338ca;font-size:0.85rem;">Node hardware ready</div>
        <div class="zone-status badge-idle">AWAITING LINK</div>
        <div class="zone-ts">Central unit integration pending</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ---- FLOOR PLAN ----
st.markdown('<div class="section-header">Lab Floor Plan — Zone Status</div>', unsafe_allow_html=True)
fp1, fp2, fp3 = st.columns(3)

fp1_class = "fp-danger" if (gas_detected or mq2_val > danger_threshold) else "fp-wait" if not zone1_online else "fp-safe"
fp1_icon  = "🔴" if (gas_detected or mq2_val > danger_threshold) else "⏳" if not zone1_online else "🟢"
fp1_label = "Leak Detected" if (gas_detected or mq2_val > danger_threshold) else "Awaiting signal" if not zone1_online else "Normal"

with fp1:
    st.markdown(f'<div class="fp-cell {fp1_class}">{fp1_icon} Zone 1<br><span style="font-weight:400;font-size:0.78rem;">{fp1_label}</span></div>', unsafe_allow_html=True)
with fp2:
    st.markdown('<div class="fp-cell fp-idle">📡 Zone 2<br><span style="font-weight:400;font-size:0.78rem;">Awaiting central unit</span></div>', unsafe_allow_html=True)
with fp3:
    st.markdown('<div class="fp-cell fp-idle">📡 Zone 3<br><span style="font-weight:400;font-size:0.78rem;">Awaiting central unit</span></div>', unsafe_allow_html=True)

st.markdown("---")

# ---- LIVE GRAPH ----
st.markdown('<div class="section-header">Live Sensor Readings — MQ-2 Raw</div>', unsafe_allow_html=True)
df = pd.DataFrame(st.session_state.history)
if len(df) > 1:
    st.line_chart(df.set_index('Time')[['MQ2 Raw']], height=220)
else:
    st.caption("Waiting for data to populate chart...")

st.markdown("---")

# ---- SUMMARY METRICS ----
st.markdown('<div class="section-header">Summary Statistics</div>', unsafe_allow_html=True)
mc1, mc2, mc3, mc4 = st.columns(4)
with mc1:
    st.metric("MQ-2 Raw", mq2_val, delta="DANGER" if mq2_val > danger_threshold else "WARNING" if mq2_val > warning_threshold else "Normal")
with mc2:
    st.metric("MQ-135", "ALERT" if mq135_alert else "CLEAR")
with mc3:
    st.metric("Danger Threshold", danger_threshold)
with mc4:
    st.metric("Active Alerts", len([a for a in st.session_state.alert_history]))

st.markdown("---")

# ---- NOTIFICATIONS PANEL ----
st.markdown('<div class="section-header">Notifications</div>', unsafe_allow_html=True)
if st.session_state.notifications:
    for n in st.session_state.notifications[:8]:
        icon = "🔴" if n["type"] == "alert" else "📨" if n["type"] == "telegram" else "🟢"
        st.markdown(f"""<div class="notif-toast notif-{n['type']}">
            <div class="notif-time">{n['time']}</div>
            {icon} {n['msg']}
        </div>""", unsafe_allow_html=True)
else:
    st.markdown('<div style="color:#9ca3af;font-size:0.82rem;padding:8px 0;">No notifications this session.</div>', unsafe_allow_html=True)

st.markdown("---")

# ---- ALERT LOG ----
st.markdown('<div class="section-header">Alert History Log</div>', unsafe_allow_html=True)
if st.session_state.alert_history:
    for alert in st.session_state.alert_history[-10:][::-1]:
        st.warning(f"🔔 {alert['time']} — Zone 1 · MQ-2: {alert['value']} · MQ-135: {'ALERT' if alert['mq135'] else 'Clear'} · Risk: {alert['risk_score']:.0f}%")
    if len(st.session_state.alert_history) > 3:
        st.error(f"⚠️ Escalation threshold reached — {len(st.session_state.alert_history)} alerts logged. Recommend lab inspection.")
else:
    st.success("No alerts recorded this session.")

st.markdown("---")

# ---- EVENT LOG ----
st.markdown('<div class="section-header">Real-Time Event Log</div>', unsafe_allow_html=True)
if not zone1_online:
    st.info(f"🕒 {datetime.now().strftime('%H:%M:%S')} — Waiting for Node 1 to establish connection...")
elif gas_detected or mq2_val > danger_threshold:
    st.error(f"🕒 {timestamp} — GAS DETECTED · Zone 1 · MQ-2: {mq2_val} · MQ-135: {'ALERT' if mq135_alert else 'Clear'}")
elif mq2_val > warning_threshold:
    st.warning(f"🕒 {timestamp} — Elevated levels · Zone 1 · MQ-2: {mq2_val} · Monitoring closely")
else:
    st.success(f"🕒 {timestamp} — All clear · Zone 1 · MQ-2: {mq2_val} · MQ-135: Clear")

st.markdown("---")
st.markdown('<div style="text-align:center;color:#9ca3af;font-size:0.72rem;padding:8px 0;">Fume-Finder · Smart Laboratory Safety System · RVCE Bangalore · 2026</div>', unsafe_allow_html=True)

# Auto-refresh
if auto_refresh:
    placeholder = st.empty()
    for i in range(refresh_interval, 0, -1):
        placeholder.markdown(f'<div style="color:#9ca3af;font-size:0.75rem;text-align:right;">Refreshing in {i}s...</div>', unsafe_allow_html=True)
        time.sleep(1)
    st.rerun()