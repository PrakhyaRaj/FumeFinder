# ============================================
# FUME-FINDER: data_connector.py
# Hardware bridge — replaces simulated data
# when ESP32 is physically connected.
#
# HOW TO SWITCH DASHBOARD TO REAL HARDWARE:
# In your dashboard file, replace the
# get_sensor_data() function definition with:
#
#   from data_connector import get_sensor_data
#
# That single line swap is all that's needed.
# Everything else in the dashboard stays the same.
# ============================================

import serial
import serial.tools.list_ports
import time

BAUD_RATE    = 115200
READ_TIMEOUT = 2   # seconds to wait for serial data

# ── Auto-detect ESP32 port ───────────────────
def find_esp32_port():
    """
    Tries to find the ESP32 serial port automatically.
    ESP32 shows up as CH340, CP210x, or similar USB-Serial chip.
    """
    for p in serial.tools.list_ports.comports():
        if any(chip in p.description for chip in
               ["CH340", "CP210", "UART", "USB Serial", "USB-SERIAL"]):
            return p.device
    # Fallback: return first available port if auto-detect fails
    ports = serial.tools.list_ports.comports()
    return ports[0].device if ports else None


# ── Main function ─────────────────────────────
def get_sensor_data(port=None):
    """
    Reads one STATUS line from ESP32 via USB serial.

    Returns the same dict format as the dashboard's
    simulated get_sensor_data() so zero dashboard changes needed.

    ESP32 must be sending lines in this format:
    STATUS:leakZone,mq2_zone1,mq2_zone2,mq2_zone3
    Example line:
    STATUS:1,650,120,80

    Args:
        port : COM port string e.g. "COM3" or "/dev/ttyUSB0"
               Leave None for auto-detection.

    Returns:
        dict matching dashboard's expected format
    """
    if port is None:
        port = find_esp32_port()

    if port is None:
        print("ERROR: No serial port found. Is ESP32 plugged in?")
        return _fallback_data()

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=READ_TIMEOUT)
        time.sleep(0.3)

        # Read up to 20 lines looking for a STATUS line
        for _ in range(20):
            if ser.in_waiting:
                raw = ser.readline().decode("utf-8", errors="ignore").strip()
                if raw.startswith("STATUS:"):
                    ser.close()
                    return _parse_status(raw)

        ser.close()
        print("WARNING: No STATUS line from ESP32 — check central_unit.ino")
        return _fallback_data()

    except serial.SerialException as e:
        print(f"Serial error: {e}")
        return _fallback_data()


# ── Parse STATUS line ─────────────────────────
def _parse_status(line):
    """
    Parses: STATUS:leakZone,mq2_1,mq2_2,mq2_3
    Returns dict in same format as dashboard simulation.
    """
    try:
        parts     = line.replace("STATUS:", "").split(",")
        leak_zone = int(parts[0])
        z1        = int(parts[1])
        z2        = int(parts[2])
        z3        = int(parts[3])

        # Map to dashboard's expected keys
        return {
            "zone1"    : z1,
            "zone2"    : z2,
            "zone3"    : z3,
            "timestamp": time.strftime("%H:%M:%S"),
            # leak_zone included as bonus — dashboard ignores it
            # but localization.py can use it for verification
            "leak_zone": leak_zone,
        }
    except (IndexError, ValueError) as e:
        print(f"Parse error on '{line}': {e}")
        return _fallback_data()


# ── Safe fallback when hardware unreachable ───
def _fallback_data():
    return {
        "zone1"    : 0,
        "zone2"    : 0,
        "zone3"    : 0,
        "timestamp": time.strftime("%H:%M:%S"),
        "leak_zone": 0,
    }


# ── Utility: list all available ports ────────
def list_ports():
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("No serial ports found.")
        return
    for p in ports:
        print(f"  {p.device} — {p.description}")


# ── Quick test: run python data_connector.py ──
if __name__ == "__main__":
    print("Available serial ports:")
    list_ports()
    print()
    print("Attempting to read from ESP32...")
    data = get_sensor_data()
    print("Data received:")
    for k, v in data.items():
        print(f"  {k}: {v}")