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
const char* ssid     = "Manya's Y100A 5G";      // Replace with your WiFi name
const char* password = "Manyay14";  // Replace with your WiFi password
// ────────────────────────────────────────────

// ── Pin Definitions ─────────────────────────
#define MQ2_AO_PIN  A0        // MQ-2 analog output → A0
#define MQ135_DO_PIN D5       // MQ-135 digital output → D5
// ────────────────────────────────────────────

// ── Threshold ───────────────────────────────
#define GAS_THRESHOLD 400     // Analog value above which gas is detected
                              // Adjust this after testing (0-1023 range)
// ────────────────────────────────────────────

ESP8266WebServer server(80);

int mq2Value   = 0;
int mq135Value = 0;
bool leakDetected = false;

void setup() {
  Serial.begin(115200);
  pinMode(MQ135_DO_PIN, INPUT);
  WiFi.mode(WIFI_STA);
  Serial.println();
  Serial.print("Node ");
  Serial.print(NODE_ID);
  Serial.println(" starting...");

  // Fixed IP — Node 2 will always be 172.20.10.102
  IPAddress local_IP(172, 20, 10, 102);
  IPAddress gateway(172, 20, 10, 1);
  IPAddress subnet(255, 255, 255, 0);
  WiFi.config(local_IP, gateway, subnet);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    Serial.println(WiFi.status());
  }
  Serial.println();
  Serial.print("Connected! IP address: ");
  Serial.println(WiFi.localIP());

  // ── HTTP endpoint: /data ─────────────────
  // ESP32 will call this URL to get sensor readings
  server.on("/data", []() {
    String json = "{";
    json += "\"node_id\":" + String(NODE_ID) + ",";
    json += "\"mq2\":" + String(mq2Value) + ",";
    json += "\"mq135\":" + String(mq135Value) + ",";
    json += "\"leak\":" + String(leakDetected ? "true" : "false");
    json += "}";
    server.send(200, "application/json", json);
  });

  server.begin();
  Serial.println("HTTP server started");

  // mDNS — gives node a fixed name on the network
  String mdnsName = "fumefinder-node" + String(NODE_ID);
  if (MDNS.begin(mdnsName)) {
    Serial.print("mDNS started: http://");
    Serial.print(mdnsName);
    Serial.println(".local/data");
  } else {
    Serial.println("mDNS failed — use IP address instead");
  }

  Serial.println("Warming up sensors (30 seconds)...");
  delay(30000); // MQ sensors need ~30s warm-up time
  Serial.println("Sensor warm-up complete. Reading started.");
}

void loop() {
  MDNS.update();
  server.handleClient();

  // Read MQ-2 analog value (0-1023)
  mq2Value = analogRead(MQ2_AO_PIN);

  // Read MQ-135 digital value (HIGH = gas detected above threshold)
  mq135Value = digitalRead(MQ135_DO_PIN);

  // Leak detected if EITHER sensor triggers
  leakDetected = (mq2Value > GAS_THRESHOLD) || (mq135Value == HIGH);

  // Print to serial monitor for debugging
  Serial.print("Node ");
  Serial.print(NODE_ID);
  Serial.print(" | MQ-2: ");
  Serial.print(mq2Value);
  Serial.print(" | MQ-135 DO: ");
  Serial.print(mq135Value);
  Serial.print(" | Leak: ");
  Serial.println(leakDetected ? "YES" : "no");

  delay(2000); // Read every 2 seconds
}
