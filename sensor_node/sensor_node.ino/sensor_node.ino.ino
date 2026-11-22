// ============================================
// FUME-FINDER: Sensor Node Code (ESP8266)
// Upload this to all 3 ESP8266 boards
// Change NODE_ID to 1, 2, or 3 for each board
// ============================================

#include <ESP8266WiFi.h>
#include <ESP8266WebServer.h>
#include <ESP8266mDNS.h>

// ── CHANGE THESE FOR EACH NODE ──────────────
#define NODE_ID 2         // Change to 2 for node 2, 3 for node 3
// ────────────────────────────────────────────

// ── WiFi Credentials ────────────────────────
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
// ────────────────────────────────────────────

// ── Pin Definitions ─────────────────────────
#define MQ2_AO_PIN  A0        // MQ-2 analog output → A0
#define MQ135_DO_PIN D5       // MQ-135 digital output → D5
// ────────────────────────────────────────────

// ── Threshold ───────────────────────────────
#define GAS_THRESHOLD 400     // Adjust after testing (0-1023 range)
// ────────────────────────────────────────────

ESP8266WebServer server(80);

int mq2Value = 0;
int mq135Value = 0;
bool leakDetected = false;
