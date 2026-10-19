import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import io
import random
import requests
from localization import localize_leak


BOT_TOKEN = "8776310870:AAGbPtWtVcZUhxI3p04NmdCB0UG6G6rW5VM"
CHAT_ID = "8589780398"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot8776310870:AAGbPtWtVcZUhxI3p04NmdCB0UG6G6rW5VM/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)
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

if 'offline_flags' not in st.session_state:
    st.session_state.offline_flags = {"Zone 1": False, "Zone 2": False, "Zone 3": False}


# Custom CSS for styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .zone-card {
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        transition: all 0.3s ease;
    }
    .danger {
        background-color: #ffebee;
        border: 2px solid #ef5350;
        box-shadow: 0 4px 15px rgba(239, 83, 80, 0.3);
    }
    .warning {
        background-color: #fff3e0;
        border: 2px solid #ff9800;
    }
    .safe {
        background-color: #e8f5e8;
        border: 2px solid #4caf50;
    }
    .status-text {
        font-size: 24px;
        font-weight: bold;
    }
    .ppm-value {
        font-size: 48px;
        font-weight: bold;
        margin: 10px 0;
    }
    .connection-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: bold;
    }
    .connection-excellent {
        background-color: #4caf50;
        color: white;
    }
    .connection-good {
        background-color: #8bc34a;
        color: white;
    }
    .connection-fair {
        background-color: #ff9800;
        color: white;
    }
    .connection-poor {
        background-color: #ef5350;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Dark mode CSS
if st.session_state.get("dark_mode", False):
    st.markdown("""
        <style>
        .stApp {
            background-color: #1e1e2e;
            color: #ffffff;
        }
        .stMarkdown, .stTitle, .stCaption {
            color: #ffffff;
        }
        .zone-card {
            background-color: #2d2d3d !important;
            color: #ffffff !important;
        }
        .danger {
            background-color: #4a1a1a !important;
            border: 2px solid #ef5350 !important;
        }
        .warning {
            background-color: #4a3a1a !important;
            border: 2px solid #ff9800 !important;
        }
        .safe {
            background-color: #1a4a1a !important;
            border: 2px solid #4caf50 !important;
        }
        </style>
    """, unsafe_allow_html=True)

# Initialize session state variables
if 'alert_history' not in st.session_state:
    st.session_state.alert_history = []

if 'last_incident' not in st.session_state:
    st.session_state.last_incident = datetime.now()

if 'connection_quality' not in st.session_state:
    st.session_state.connection_quality = "Excellent"

if 'offline_flags' not in st.session_state:
    st.session_state.offline_flags = {"Zone 1": False, "Zone 2": False, "Zone 3": False}

# Title and header
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    st.title("🔬 Fume-Finder")
    st.caption("Smart Laboratory Gas Leak Detection & Localization System")
    st.markdown("---")

# Sidebar for controls
with st.sidebar:
    st.header("⚙️ Controls")

    # Dark Mode Toggle
    dark_mode = st.toggle("🌙 Dark Mode")
    st.session_state.dark_mode = dark_mode

    st.markdown("---")

    # Threshold Sliders
    st.subheader("⚠️ Threshold Settings")
    danger_threshold = st.slider("🚨 Danger Threshold (ppm)", 100, 1000, 300)
    warning_threshold = st.slider("⚠️ Warning Threshold (ppm)", 50, 500, 150)

    st.markdown("---")

    # Auto-refresh Toggle
    auto_refresh = st.checkbox("🔄 Auto-refresh Dashboard", value=True)
    refresh_interval = st.slider("Refresh Interval (seconds)", 1, 10, 3, disabled=not auto_refresh)

    st.markdown("---")

    # Export CSV Button
    st.subheader("📊 Data Export")
    if st.button("📥 Export Data as CSV"):
        if 'history' in st.session_state and len(st.session_state.history) > 0:
            df_export = pd.DataFrame(st.session_state.history)
            csv = df_export.to_csv(index=False)
            st.download_button(
                label="📎 Download CSV",
                data=csv,
                file_name=f"fume_finder_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            st.balloons()
        else:
            st.warning("No data available to export yet")

    st.markdown("---")

    # Reset Data Button
    if st.button("🔄 Reset Alert History"):
        st.session_state.alert_history = []
        st.session_state.history = []
        st.success("Alert history cleared!")
        time.sleep(1)
        st.rerun()

    st.markdown("---")

    # System Info
    st.subheader("🖥️ System Status")
    st.success("🟢 System Online")
    st.info(f"📅 Time: {datetime.now().strftime('%H:%M:%S')}")
    st.info(f"📡 Connected Nodes: 3/3")
    st.warning(f"⚠️ Danger Threshold: {danger_threshold} ppm")
    st.info(f"⚡ Warning Threshold: {warning_threshold} ppm")

    st.markdown("---")
    st.caption("RV College of Engineering")
    st.caption("Interdisciplinary Project | 2026")


# Simulated sensor data
def get_sensor_data():
    """Simulate sensor readings - replace with actual API call"""
    # Simulate occasional offline behavior (5% chance for demo)
    zone1_online = random.random() > 0.05
    zone2_online = random.random() > 0.05
    zone3_online = random.random() > 0.05

    st.session_state.offline_flags = {
        "Zone 1": not zone1_online,
        "Zone 2": not zone2_online,
        "Zone 3": not zone3_online
    }

    return {
        "zone1": random.randint(50, 500) if zone1_online else 0,
        "zone2": random.randint(50, 500) if zone2_online else 0,
        "zone3": random.randint(50, 500) if zone3_online else 0,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }


# Get data
data = get_sensor_data()

# Determine peak value and affected zone
zones = {
    "Zone 1 (Left)": data["zone1"],
    "Zone 2 (Center)": data["zone2"],
    "Zone 3 (Right)": data["zone3"]
}
max_zone = max(zones, key=zones.get)
max_value = zones[max_zone]

# Feature 24: Zone Risk Score Calculation
risk_score = min((max_value / danger_threshold) * 100, 100)

# Initialize session state for history
if 'history' not in st.session_state:
    st.session_state.history = []

# Add current reading to history
st.session_state.history.append({
    'Time': datetime.now().strftime("%H:%M:%S"),
    'Zone 1 (ppm)': data["zone1"],
    'Zone 2 (ppm)': data["zone2"],
    'Zone 3 (ppm)': data["zone3"],
    'Peak (ppm)': max_value,
    'Risk Score (%)': risk_score,
    'Status': 'DANGER' if max_value > danger_threshold else 'WARNING' if max_value > warning_threshold else 'NORMAL'
})

# Keep only last 50 readings
if len(st.session_state.history) > 50:
    st.session_state.history.pop(0)


# Feature 2: Connection Quality Indicator
def get_connection_quality():
    """Simulate connection quality based on random factor"""
    qualities = ["Excellent", "Good", "Fair", "Poor"]
    weights = [0.6, 0.25, 0.1, 0.05]  # Mostly Excellent/Good
    return random.choices(qualities, weights=weights)[0]


connection_quality = get_connection_quality()
quality_colors = {
    "Excellent": "🟢",
    "Good": "🟡",
    "Fair": "🟠",
    "Poor": "🔴"
}

# Feature 3: Offline Detection Flag
offline_zones = [zone for zone, offline in st.session_state.offline_flags.items() if offline]

# Localization algorithm — identifies zone with highest reading
result = localize_leak(data["zone1"], data["zone2"], data["zone3"],
                       danger_threshold=danger_threshold)
leak_zone_num = result["zone"]
zone_map = {0: None, 1: "Zone 1", 2: "Zone 2", 3: "Zone 3"}
affected_zone = zone_map[leak_zone_num]

# Feature 15: Escalation Alert (Repeated Warnings)
alert_count = len([a for a in st.session_state.alert_history if a['value'] > danger_threshold])
if alert_count > 3:
    st.error("🚨 MULTIPLE ALERTS DETECTED! Evacuate immediately!")
elif alert_count > 1:
    st.warning(f"⚠️ {alert_count} alerts in last {len(st.session_state.alert_history)} readings")

# Display main alert
if max_value > danger_threshold:
    st.error(f"🚨 **ALERT! Gas leak detected in {max_zone}!** 🚨")
elif max_value > warning_threshold:
    st.warning(f"⚠️ **Warning: Elevated gas levels in {max_zone}** ⚠️")
else:
    st.success("✅ All zones normal. No gas leak detected.")

# Feature 24: Display Risk Score
st.markdown("---")
col_risk1, col_risk2, col_risk3 = st.columns([2, 1, 1])
with col_risk1:
    st.subheader("📊 System Risk Assessment")
    st.progress(risk_score / 100)
    st.caption(f"⚠️ Current Risk Level: {risk_score:.0f}%")

    # Risk level color coding
    if risk_score > 80:
        st.error("🔴 CRITICAL RISK - Immediate action required")
    elif risk_score > 50:
        st.warning("🟠 HIGH RISK - Monitor closely")
    elif risk_score > 20:
        st.info("🟡 MEDIUM RISK - Normal monitoring")
    else:
        st.success("🟢 LOW RISK - Safe conditions")

# Feature 2: Connection Quality Display
with col_risk2:
    st.subheader("📡 Connection Status")
    st.markdown(f"""
    <div>
        <span class="connection-badge connection-{connection_quality.lower()}">
            {quality_colors[connection_quality]} {connection_quality}
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Signal Strength: {connection_quality}")

# Feature 3: Offline Detection Display
with col_risk3:
    st.subheader("🔌 Node Status")
    if offline_zones:
        st.warning(f"⚠️ Offline: {', '.join(offline_zones)}")
        for zone in offline_zones:
            st.caption(f"🔴 {zone} - No signal")
    else:
        st.success("✅ All nodes online")
        st.caption("All 3 zones reporting")

st.markdown("---")

# Zone displays
col1, col2, col3 = st.columns(3)

# Zone 1
with col1:
    value = data["zone1"]
    if st.session_state.offline_flags["Zone 1"]:
        status = "warning"
        status_text = "⚠️ OFFLINE"
        display_value = "No Data"
    else:
        if leak_zone_num == 1 and value > danger_threshold:
            status = "danger"
            status_text = "⚠️ LEAK SOURCE"
        elif value > danger_threshold:
            status = "warning"
            status_text = "⚠️ ELEVATED"
        elif value > warning_threshold:
            status = "warning"
            status_text = "⚠️ ELEVATED"
        else:
            status = "safe"
            status_text = "✅ NORMAL"
        display_value = f"{value} ppm"

    st.markdown(f"""
    <div class="zone-card {status}">
        <h2>📍 ZONE 1</h2>
        <h3>(Left Side)</h3>
        <div class="ppm-value">{display_value}</div>
        <div class="status-text">{status_text}</div>
        <p>MQ-2 / MQ-135</p>
    </div>
    """, unsafe_allow_html=True)

# Zone 2
with col2:
    value = data["zone2"]
    if st.session_state.offline_flags["Zone 2"]:
        status = "warning"
        status_text = "⚠️ OFFLINE"
        display_value = "No Data"
    else:
        if leak_zone_num == 2 and value > danger_threshold:
            status = "danger"
            status_text = "⚠️ LEAK SOURCE"
        elif value > danger_threshold:
            status = "warning"
            status_text = "⚠️ ELEVATED"
        elif value > warning_threshold:
            status = "warning"
            status_text = "⚠️ ELEVATED"
        else:
            status = "safe"
            status_text = "✅ NORMAL"
        display_value = f"{value} ppm"

    st.markdown(f"""
    <div class="zone-card {status}">
        <h2>📍 ZONE 2</h2>
        <h3>(Center)</h3>
        <div class="ppm-value">{display_value}</div>
        <div class="status-text">{status_text}</div>
        <p>MQ-2 / MQ-135</p>
    </div>
    """, unsafe_allow_html=True)

# Zone 3
with col3:
    value = data["zone3"]
    if st.session_state.offline_flags["Zone 3"]:
        status = "warning"
        status_text = "⚠️ OFFLINE"
        display_value = "No Data"
    else:
        if leak_zone_num == 3 and value > danger_threshold:
            status = "danger"
            status_text = "⚠️ LEAK SOURCE"
        elif value > danger_threshold:
            status = "warning"
            status_text = "⚠️ ELEVATED"
        elif value > warning_threshold:
            status = "warning"
            status_text = "⚠️ ELEVATED"
        else:
            status = "safe"
            status_text = "✅ NORMAL"
        display_value = f"{value} ppm"

    st.markdown(f"""
    <div class="zone-card {status}">
        <h2>📍 ZONE 3</h2>
        <h3>(Right Side)</h3>
        <div class="ppm-value">{display_value}</div>
        <div class="status-text">{status_text}</div>
        <p>MQ-2 / MQ-135</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Floor Plan Visualization
st.subheader("📋 Lab Floor Plan - Affected Zone Indicator")

floor_col1, floor_col2, floor_col3 = st.columns(3)

# # Determine affected zone
# affected_zone = None
# if not st.session_state.offline_flags["Zone 1"] and data["zone1"] > danger_threshold:
#     affected_zone = "Zone 1"
# elif not st.session_state.offline_flags["Zone 2"] and data["zone2"] > danger_threshold:
#     affected_zone = "Zone 2"
# elif not st.session_state.offline_flags["Zone 3"] and data["zone3"] > danger_threshold:
#     affected_zone = "Zone 3"

# ---------------- TELEGRAM ALERT ---------------- #
current_time = time.time()

if max_value > danger_threshold:

#     alert_msg = f"""
# 🚨 *GAS LEAK ALERT* 🚨

# 📍 Zone: {max_zone}
# 📊 Level: {max_value} ppm
# ⚠️ Risk Score: {risk_score:.0f}%

# 🕒 Time: {datetime.now().strftime('%H:%M:%S')}

# ❗ Immediate action required!
# """
    alert_msg = f"""
🚨 *GAS LEAK ALERT* 🚨

📍 Zone: {max_zone}
📊 Level: {max_value} ppm
🎯 Localization: {result['message'] if affected_zone else 'N/A'}

🕒 Time: {datetime.now().strftime('%H:%M:%S')}

❗ Immediate action required!
"""

    # Anti-spam: send once every 30 sec
    if current_time - st.session_state.last_telegram_alert > 30:
        send_telegram_alert(alert_msg)
        st.session_state.last_telegram_alert = current_time

with floor_col1:
    if affected_zone == "Zone 1":
        st.markdown("""
        <div style="background-color:#ffebee; border:3px solid #ef5350; border-radius:10px; padding:20px; text-align:center;">
            <h3 style="color:#c62828;">🔴 ZONE 1</h3>
            <p>Leak Detected Here!</p>
            <p>Fan Activated →</p>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.offline_flags["Zone 1"]:
        st.markdown("""
        <div style="background-color:#fff3e0; border:2px solid #ff9800; border-radius:10px; padding:20px; text-align:center;">
            <h3 style="color:#e65100;">⚠️ ZONE 1</h3>
            <p>Node Offline</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color:#e8f5e8; border:2px solid #4caf50; border-radius:10px; padding:20px; text-align:center;">
            <h3 style="color:#2e7d32;">🟢 ZONE 1</h3>
            <p>Normal</p>
        </div>
        """, unsafe_allow_html=True)

with floor_col2:
    if affected_zone == "Zone 2":
        st.markdown("""
        <div style="background-color:#ffebee; border:3px solid #ef5350; border-radius:10px; padding:20px; text-align:center;">
            <h3 style="color:#c62828;">🔴 ZONE 2</h3>
            <p>Leak Detected Here!</p>
            <p>Fan Activated →</p>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.offline_flags["Zone 2"]:
        st.markdown("""
        <div style="background-color:#fff3e0; border:2px solid #ff9800; border-radius:10px; padding:20px; text-align:center;">
            <h3 style="color:#e65100;">⚠️ ZONE 2</h3>
            <p>Node Offline</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color:#e8f5e8; border:2px solid #4caf50; border-radius:10px; padding:20px; text-align:center;">
            <h3 style="color:#2e7d32;">🟢 ZONE 2</h3>
            <p>Normal</p>
        </div>
        """, unsafe_allow_html=True)

with floor_col3:
    if affected_zone == "Zone 3":
        st.markdown("""
        <div style="background-color:#ffebee; border:3px solid #ef5350; border-radius:10px; padding:20px; text-align:center;">
            <h3 style="color:#c62828;">🔴 ZONE 3</h3>
            <p>Leak Detected Here!</p>
            <p>Fan Activated →</p>
        </div>
        """, unsafe_allow_html=True)
    elif st.session_state.offline_flags["Zone 3"]:
        st.markdown("""
        <div style="background-color:#fff3e0; border:2px solid #ff9800; border-radius:10px; padding:20px; text-align:center;">
            <h3 style="color:#e65100;">⚠️ ZONE 3</h3>
            <p>Node Offline</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color:#e8f5e8; border:2px solid #4caf50; border-radius:10px; padding:20px; text-align:center;">
            <h3 style="color:#2e7d32;">🟢 ZONE 3</h3>
            <p>Normal</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Live Graph Section
st.subheader("📈 Live Sensor Readings")

df = pd.DataFrame(st.session_state.history)
if len(df) > 0:
    st.line_chart(df.set_index('Time')[['Zone 1 (ppm)', 'Zone 2 (ppm)', 'Zone 3 (ppm)']], height=300)

st.markdown("---")

# Feature 5: Hourly Average Chart
st.subheader("📊 Hourly Average Gas Levels")
if len(df) > 0:
    df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M:%S').dt.hour
    hourly_avg = df.groupby('Hour')[['Zone 1 (ppm)', 'Zone 2 (ppm)', 'Zone 3 (ppm)']].mean()
    st.bar_chart(hourly_avg)
    st.caption("Average gas levels by hour of day")

st.markdown("---")

# Summary Statistics
st.subheader("📊 Summary Statistics")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Peak Value", f"{max_value} ppm",
              delta="DANGER" if max_value > danger_threshold else "WARNING" if max_value > warning_threshold else "Normal")

with col2:
    avg_value = (data["zone1"] + data["zone2"] + data["zone3"]) / 3
    st.metric("Average Reading", f"{avg_value:.0f} ppm")

with col3:
    st.metric("Danger Threshold", f"{danger_threshold} ppm")

with col4:
    st.metric("Active Alerts", "1" if max_value > danger_threshold else "0")

st.markdown("---")

# Feature 15: Alert History Log
st.subheader("📝 Alert History Log")

# Update alert history when leak detected
if max_value > danger_threshold and not st.session_state.get("last_alert_logged", False):
    st.session_state.alert_history.append({
        'time': datetime.now().strftime("%H:%M:%S"),
        'zone': max_zone,
        'value': max_value,
        'risk_score': risk_score
    })
    st.session_state.last_alert_logged = True
elif max_value <= danger_threshold:
    st.session_state.last_alert_logged = False

# Display alert history
if len(st.session_state.alert_history) > 0:
    for alert in st.session_state.alert_history[-10:]:
        st.warning(f"🔔 {alert['time']} - {alert['zone']}: {alert['value']} ppm (Risk: {alert['risk_score']:.0f}%)")
else:
    st.success("✅ No alerts recorded in this session")

# Display escalation warning if multiple alerts
if len(st.session_state.alert_history) > 3:
    st.error(f"⚠️ ESCALATION: {len(st.session_state.alert_history)} alerts recorded! Recommend lab inspection.")

st.markdown("---")

# System Action Log
st.subheader("🕐 Real-Time Event Log")

# Display actions based on current readings
# if data["zone1"] > danger_threshold and not st.session_state.offline_flags["Zone 1"]:
#     st.warning(f"🕒 {data['timestamp']} - LEAK detected in ZONE 1 | Fan 1 ACTIVATED | Level: {data['zone1']} ppm")
# elif data["zone2"] > danger_threshold and not st.session_state.offline_flags["Zone 2"]:
#     st.warning(f"🕒 {data['timestamp']} - LEAK detected in ZONE 2 | Fan 2 ACTIVATED | Level: {data['zone2']} ppm")
# elif data["zone3"] > danger_threshold and not st.session_state.offline_flags["Zone 3"]:
#     st.warning(f"🕒 {data['timestamp']} - LEAK detected in ZONE 3 | Fan 3 ACTIVATED | Level: {data['zone3']} ppm")
# elif data["zone1"] > warning_threshold or data["zone2"] > warning_threshold or data["zone3"] > warning_threshold:
#     st.info(f"🕒 {data['timestamp']} - Elevated gas levels detected | Monitoring closely")
# else:
#     st.success(f"🕒 {data['timestamp']} - All systems normal | No action required")
if affected_zone:
    zone_val = [data["zone1"], data["zone2"], data["zone3"]][leak_zone_num - 1]
    st.warning(
        f"🕒 {data['timestamp']} - LEAK LOCALIZED to {affected_zone} | "
        f"Fan {leak_zone_num} ACTIVATED | Level: {zone_val} ppm | "
        f"Confidence: {result['confidence'].upper()}"
    )
elif data["zone1"] > warning_threshold or data["zone2"] > warning_threshold or data["zone3"] > warning_threshold:
    st.info(f"🕒 {data['timestamp']} - Elevated gas levels detected | Monitoring closely")
else:
    st.success(f"🕒 {data['timestamp']} - All systems normal | No action required")

# Show offline node warnings
for zone in offline_zones:
    st.warning(f"🕒 {data['timestamp']} - {zone} node OFFLINE | Check connection")

st.markdown("---")
st.caption("🔬 Fume-Finder | Smart Laboratory Safety System | RVCE Bangalore")

# Auto-refresh logic
if auto_refresh:
    placeholder = st.empty()
    for i in range(refresh_interval, 0, -1):
        placeholder.info(f"⏳ Refreshing in {i} seconds...")
        time.sleep(1)
    st.rerun()