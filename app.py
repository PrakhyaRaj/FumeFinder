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


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()


def send_telegram_alert(message):
    if not BOT_TOKEN or not CHAT_ID:
        print("Telegram alert disabled: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=10)
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
