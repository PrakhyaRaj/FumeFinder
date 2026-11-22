import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
import io
import random
import requests
import os
from localization import localize_leak


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
