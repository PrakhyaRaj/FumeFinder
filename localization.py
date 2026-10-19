# ============================================
# FUME-FINDER: localization.py
# Core CS algorithm — zone identification
# from multi-sensor signal strength comparison
#
# Variable names match the dashboard exactly:
#   zone1, zone2, zone3 → same as data["zone1"] etc.
#
# Test it by running: python localization.py
# ============================================

def localize_leak(zone1_val, zone2_val, zone3_val,
                  danger_threshold=300, margin=50):
    """
    Identifies which zone has the gas leak.

    Args:
        zone1_val         : reading from node 1 (matches data["zone1"])
        zone2_val         : reading from node 2 (matches data["zone2"])
        zone3_val         : reading from node 3 (matches data["zone3"])
        danger_threshold  : value above which gas is flagged as leak
                            (same as danger_threshold slider in dashboard)
        margin            : if top two readings differ by less than this,
                            it's a boundary leak — still activates top fan

    Returns dict:
        zone (int)        : 0=no leak, 1=Zone1, 2=Zone2, 3=Zone3
        confidence (str)  : "high" or "medium"
        message (str)     : human readable result
        all_readings (dict): raw values for logging
    """
    readings  = {1: zone1_val, 2: zone2_val, 3: zone3_val}
    zone_names = {
        0: "None",
        1: "Zone 1 (Left)",
        2: "Zone 2 (Center)",
        3: "Zone 3 (Right)"
    }

    # No zone above threshold → no leak
    if not any(v > danger_threshold for v in readings.values()):
        return {
            "zone": 0,
            "confidence": "high",
            "message": "No leak detected — all zones normal",
            "all_readings": readings
        }

    # Sort zones highest to lowest
    sorted_zones = sorted(readings.items(), key=lambda x: x[1], reverse=True)
    top_zone, top_val = sorted_zones[0]
    sec_zone, sec_val = sorted_zones[1]

    # Boundary check — two zones very close in reading
    if abs(top_val - sec_val) <= margin and sec_val > danger_threshold:
        return {
            "zone": top_zone,
            "confidence": "medium",
            "message": (
                f"Leak between {zone_names[top_zone]} and "
                f"{zone_names[sec_zone]} — fan activated in {zone_names[top_zone]}"
            ),
            "all_readings": readings
        }

    return {
        "zone": top_zone,
        "confidence": "high",
        "message": f"Leak localized to {zone_names[top_zone]}",
        "all_readings": readings
    }


# ── Calibration helper ────────────────────────
def suggest_threshold(baseline_readings, multiplier=3.0):
    """
    Suggests a danger_threshold value from clean-air readings.
    Run once when hardware is connected in a clean room.

    Args:
        baseline_readings : list of MQ-2 readings in clean air
        multiplier        : safety factor (3.0 recommended)

    Returns:
        suggested threshold as int
    """
    avg = sum(baseline_readings) / len(baseline_readings)
    suggested = int(avg * multiplier)
    print(f"  Baseline average          : {avg:.1f}")
    print(f"  Suggested threshold (×{multiplier}) : {suggested}")
    return suggested


# ══════════════════════════════════════════════
# TESTS — run: python localization.py
# ══════════════════════════════════════════════

def run_tests():
    print("=" * 55)
    print("FUME-FINDER: Localization Algorithm Tests")
    print("=" * 55)

    tests = [
        # (z1,  z2,  z3,  expected_zone, description)
        (80,   85,   78,  0, "Normal air — no leak"),
        (650,  120,  80,  1, "Clear leak at Zone 1"),
        (90,   680,  95,  2, "Clear leak at Zone 2"),
        (75,   88,   700, 3, "Clear leak at Zone 3"),
        (620,  580,  90,  1, "Boundary leak Zone1-Zone2 (Zone1 higher)"),
        (310,  85,   88,  1, "Weak leak just above threshold at Zone 1"),
        (200,  200,  200, 0, "All zones equal, below threshold"),
    ]

    passed = 0
    for z1, z2, z3, expected, desc in tests:
        result = localize_leak(z1, z2, z3)
        ok = result["zone"] == expected
        passed += ok
        tag = "PASS" if ok else "FAIL"
        print(f"\n  [{tag}] {desc}")
        print(f"         Inputs  : Zone1={z1}  Zone2={z2}  Zone3={z3}")
        print(f"         Output  : zone={result['zone']}  confidence={result['confidence']}")
        print(f"         Message : {result['message']}")

    print("\n" + "=" * 55)
    print(f"  Result: {passed}/{len(tests)} tests passed")
    print("=" * 55)

    print("\n  Calibration demo (sample clean-air readings):")
    suggest_threshold([78, 82, 75, 80, 79, 83, 77])


if __name__ == "__main__":
    run_tests()