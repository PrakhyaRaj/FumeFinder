# ============================================
# FUME-FINDER: alert_manager.py
# Sends Telegram notifications when leak detected
# No payment details needed — completely free
#
# SETUP (5 minutes):
# 1. Open Telegram → search @BotFather
# 2. Send /newbot → follow steps → copy the TOKEN it gives you
# 3. Search @userinfobot → start it → copy your Chat ID
# 4. Paste both below
# 5. Run: pip install requests
# ============================================

import requests
import time

# ── PASTE YOUR VALUES HERE ───────────────────
BOT_TOKEN = "PASTE_YOUR_BOT_TOKEN_HERE"
# Example: "7412345678:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

CHAT_ID = "PASTE_YOUR_CHAT_ID_HERE"
# Example: "123456789"
# ────────────────────────────────────────────

# Only sends one alert per zone per this many seconds
# Avoids spamming your phone during a sustained leak
ALERT_COOLDOWN_SECONDS = 30

_last_alert_time = {1: 0, 2: 0, 3: 0}
_last_known_zone = 0

# ── Core send function ────────────────────────
def send_telegram(message: str) -> bool:
    """
    Sends any message to your Telegram via the bot.
    Returns True if successful.
    """
    if BOT_TOKEN == "PASTE_YOUR_BOT_TOKEN_HERE":
        print("[Telegram] Not configured yet — skipping")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 200:
            print("[Telegram] Alert sent successfully")
            return True
        else:
            print(f"[Telegram] Failed — {response.status_code}: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"[Telegram] Network error: {e}")
        return False


# ── Leak alert ────────────────────────────────
def send_leak_alert(zone: int, mq2_readings: dict) -> bool:
    """
    Call this from the dashboard when a leak is detected.

    Args:
        zone: 1, 2, or 3
        mq2_readings: e.g. {"Zone A": 650, "Zone B": 120, "Zone C": 80}

    Returns:
        True if alert was sent
    """
    zone_names = {1: "Zone A", 2: "Zone B", 3: "Zone C"}
    zone_locations = {
        1: "Window side / Corner 1",
        2: "Center area / Corner 2",
        3: "Door side / Corner 3"
    }

    if zone not in zone_names:
        return False

    # Cooldown check
    now = time.time()
    if now - _last_alert_time[zone] < ALERT_COOLDOWN_SECONDS:
        print(f"[Telegram] Cooldown active — skipping Zone {zone} alert")
        return False

    zone_name = zone_names[zone]
    location  = zone_locations[zone]
    timestamp = time.strftime("%H:%M:%S")

    readings_text = "\n".join(
        [f"  • {k}: `{v} ppm`" for k, v in mq2_readings.items()]
    )

    message = (
        f"🚨 *FUME-FINDER ALERT*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"*Gas leak detected!*\n\n"
        f"📍 *Location:* {zone_name}\n"
        f"🗺 *Area:* {location}\n"
        f"🕐 *Time:* {timestamp}\n\n"
        f"*Sensor readings:*\n{readings_text}\n\n"
        f"✅ Exhaust fan activated in {zone_name}\n"
        f"⚠️ Please evacuate and check the area."
    )

    success = send_telegram(message)
    if success:
        _last_alert_time[zone] = now
    return success


# ── Clear alert ───────────────────────────────
def send_clear_alert(zone: int) -> bool:
    """
    Call this when gas clears and zone returns to normal.
    """
    zone_names = {1: "Zone A", 2: "Zone B", 3: "Zone C"}
    if zone not in zone_names:
        return False

    message = (
        f"✅ *FUME-FINDER: All Clear*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Gas levels returned to normal.\n\n"
        f"📍 *Zone cleared:* {zone_names[zone]}\n"
        f"🕐 *Time:* {time.strftime('%H:%M:%S')}\n\n"
        f"Fan deactivated. Area is safe."
    )
    return send_telegram(message)


# ── Smart trigger: call this every dashboard loop ──
def check_and_alert(current_zone: int, mq2_readings: dict):
    """
    Handles both leak alerts and clear alerts automatically.
    Call this once per dashboard refresh cycle.

    Example usage in dashboard:
        from alert_manager import check_and_alert
        check_and_alert(data["leak_zone"], {
            "Zone A": data["node1"]["mq2"],
            "Zone B": data["node2"]["mq2"],
            "Zone C": data["node3"]["mq2"],
        })
    """
    global _last_known_zone

    if current_zone != 0:
        # New leak or continuing leak
        send_leak_alert(current_zone, mq2_readings)

    elif current_zone == 0 and _last_known_zone != 0:
        # Leak just cleared
        send_clear_alert(_last_known_zone)

    _last_known_zone = current_zone


# ── Test: run python alert_manager.py to verify ──
def test_connection():
    print("Testing Telegram connection...")
    success = send_telegram(
        "🔬 *Fume-Finder Test*\n"
        "If you see this, your Telegram alert is working!"
    )
    if success:
        print("✅ Check your Telegram app!")
    else:
        print("❌ Failed — check BOT_TOKEN and CHAT_ID above")


if __name__ == "__main__":
    test_connection()