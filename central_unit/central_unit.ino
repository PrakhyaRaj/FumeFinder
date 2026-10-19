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
const char* ssid     = "Manya's Y100A 5G";      // Same as sensor nodes
const char* password = "Manyay14";
// ────────────────────────────────────────────

// ── Sensor Node IP Addresses ─────────────────
// After uploading code to each ESP8266, check
// their IP address in Serial Monitor and paste here
const char* node1IP = "172.20.10.101";
const char* node2IP = "172.20.10.102";
const char* node3IP = "172.20.10.103";
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

void setup() {
  Serial.begin(115200);

  // Setup output pins
  pinMode(RELAY_FAN1, OUTPUT);
  pinMode(RELAY_FAN2, OUTPUT);
  pinMode(RELAY_FAN3, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(LED_GREEN,  OUTPUT);
  pinMode(LED_RED,    OUTPUT);

  // All fans OFF at start
  digitalWrite(RELAY_FAN1, RELAY_OFF);
  digitalWrite(RELAY_FAN2, RELAY_OFF);
  digitalWrite(RELAY_FAN3, RELAY_OFF);
  digitalWrite(BUZZER_PIN, LOW);
  digitalWrite(LED_GREEN,  HIGH); // Green ON = system normal
  digitalWrite(LED_RED,    LOW);  // Red OFF = no alert

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Central unit connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("Connected! IP: ");
  Serial.println(WiFi.localIP());
  Serial.println("Fume-Finder Central Unit Ready.");

  Serial.println("Fume-Finder Central Unit Ready.");
  if (MDNS.begin("fumefinder-central")) {
    Serial.println("Central mDNS started");
  }
}

void loop() {
  // ── Step 1: Poll all 3 sensor nodes ────────
  fetchNodeData(node1IP, mq2_node1, leak_node1);
  fetchNodeData(node2IP, mq2_node2, leak_node2);
  fetchNodeData(node3IP, mq2_node3, leak_node3);

  // ── Step 2: Print all readings ─────────────
  Serial.println("─────────────────────────────");
  Serial.print("Node 1 (Zone A): MQ2="); Serial.print(mq2_node1);
  Serial.print(" Leak="); Serial.println(leak_node1 ? "YES" : "no");
  Serial.print("Node 2 (Zone B): MQ2="); Serial.print(mq2_node2);
  Serial.print(" Leak="); Serial.println(leak_node2 ? "YES" : "no");
  Serial.print("Node 3 (Zone C): MQ2="); Serial.print(mq2_node3);
  Serial.print(" Leak="); Serial.println(leak_node3 ? "YES" : "no");

  // ── Step 3: Localization algorithm ─────────
  leakZone = localizeZone();

  // ── Step 4: Control outputs ─────────────────
  controlOutputs(leakZone);

  // ── Step 5: Print status for Streamlit ──────
  // Streamlit reads this via serial
  Serial.print("STATUS:");
  Serial.print(leakZone);
  Serial.print(",");
  Serial.print(mq2_node1);
  Serial.print(",");
  Serial.print(mq2_node2);
  Serial.print(",");
  Serial.println(mq2_node3);

  delay(2000); // Poll every 2 seconds
}

// ── Fetch data from one sensor node ──────────
void fetchNodeData(const char* ip, int &mq2Val, bool &leakVal) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = "http://" + String(ip) + "/data";
  http.begin(url);

  int httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();

    // Parse JSON response
    StaticJsonDocument<200> doc;
    DeserializationError error = deserializeJson(doc, payload);
    if (!error) {
      mq2Val  = doc["mq2"].as<int>();
      leakVal = doc["leak"].as<bool>();
    }
  } else {
    Serial.print("Failed to reach node at ");
    Serial.println(ip);
  }
  http.end();
}

// ── Localization Algorithm ───────────────────
// Compares MQ-2 readings from all 3 nodes
// Node with highest reading = leak zone
int localizeZone() {
  bool anyLeak = leak_node1 || leak_node2 || leak_node3;
  if (!anyLeak) return 0; // No leak

  // Find zone with highest MQ-2 reading
  if (mq2_node1 >= mq2_node2 && mq2_node1 >= mq2_node3) return 1;
  if (mq2_node2 >= mq2_node1 && mq2_node2 >= mq2_node3) return 2;
  if (mq2_node3 >= mq2_node1 && mq2_node3 >= mq2_node2) return 3;

  return 0;
}

// ── Control fans, buzzer, LEDs ───────────────
void controlOutputs(int zone) {
  if (zone == 0) {
    // No leak — all fans off, green LED on
    digitalWrite(RELAY_FAN1, RELAY_OFF);
    digitalWrite(RELAY_FAN2, RELAY_OFF);
    digitalWrite(RELAY_FAN3, RELAY_OFF);
    digitalWrite(BUZZER_PIN, LOW);
    digitalWrite(LED_GREEN,  HIGH);
    digitalWrite(LED_RED,    LOW);
    Serial.println("Status: ALL CLEAR");
  } else {
    // Leak detected — activate fan in affected zone only
    digitalWrite(RELAY_FAN1, zone == 1 ? RELAY_ON : RELAY_OFF);
    digitalWrite(RELAY_FAN2, zone == 2 ? RELAY_ON : RELAY_OFF);
    digitalWrite(RELAY_FAN3, zone == 3 ? RELAY_ON : RELAY_OFF);
    digitalWrite(BUZZER_PIN, HIGH);  // Buzzer ON
    digitalWrite(LED_GREEN,  LOW);   // Green OFF
    digitalWrite(LED_RED,    HIGH);  // Red ON
    Serial.print("ALERT: Leak detected in Zone ");
    Serial.println(zone == 1 ? "A" : zone == 2 ? "B" : "C");
  }
}
