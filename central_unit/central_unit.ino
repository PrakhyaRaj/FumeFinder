// ============================================
// FUME-FINDER: Central Unit Code (ESP32)
// Polls 3 sensor nodes, runs localization,
// controls relay fans, buzzer, and LEDs
// ============================================

#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <ESPmDNS.h>

// ── WiFi Credentials ────────────────────────
const char* ssid     = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
// ────────────────────────────────────────────

// ── Sensor Node IP Addresses ─────────────────
// After uploading code to each ESP8266, check
// their IP address in Serial Monitor and paste here
const char* node1IP = "192.168.1.101";
const char* node2IP = "192.168.1.102";
const char* node3IP = "192.168.1.103";
// ────────────────────────────────────────────

// ── Pin Definitions (ESP32) ──────────────────
#define RELAY_FAN1  25    // GPIO 25 → Relay IN1 → Fan Zone A
#define RELAY_FAN2  26    // GPIO 26 → Relay IN2 → Fan Zone B
#define RELAY_FAN3  27    // GPIO 27 → Relay IN3 → Fan Zone C
#define BUZZER_PIN  32    // GPIO 32 → Buzzer +
#define LED_GREEN   33    // GPIO 33 → 220Ω → Green LED +
#define LED_RED     34    // GPIO 34 → 220Ω → Red LED +
// ────────────────────────────────────────────

// ── Relay Logic ──────────────────────────────
// Most relay modules are ACTIVE LOW
// LOW = relay ON (fan runs)
// HIGH = relay OFF (fan stops)
#define RELAY_ON  LOW
#define RELAY_OFF HIGH
// ────────────────────────────────────────────

// Sensor data storage
int mq2_node1 = 0, mq2_node2 = 0, mq2_node3 = 0;
bool leak_node1 = false, leak_node2 = false, leak_node3 = false;
int leakZone = 0; // 0=none, 1=zone A, 2=zone B, 3=zone C
