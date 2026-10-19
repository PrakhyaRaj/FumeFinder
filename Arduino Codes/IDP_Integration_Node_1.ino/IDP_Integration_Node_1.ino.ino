#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>

const char* ssid = "*****";
const char* password = "*****";
const char* serverURL =  "http://10.20.120.145:8502/data";  // check your PC IP via ipconfig

#define MQ135_DOUT D5
#define LED_GREEN  D1
#define LED_RED    D2
#define BUZZER     D7
#define MQ2_THRESHOLD 300

void setup() {
  Serial.begin(115200);
  delay(1000);

  pinMode(MQ135_DOUT, INPUT);
  pinMode(LED_GREEN, OUTPUT);
  pinMode(LED_RED, OUTPUT);
  pinMode(BUZZER, OUTPUT);

  digitalWrite(LED_RED, HIGH);
  digitalWrite(LED_GREEN, LOW);
  Serial.println("Warming up...");

  for (int i = 30; i > 0; i--) {
    Serial.println("Warmup: " + String(i) + "s remaining");
    delay(1000);
  }

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected. IP: " + WiFi.localIP().toString());

  digitalWrite(LED_RED, LOW);
  digitalWrite(LED_GREEN, HIGH);
  Serial.println("Ready. Monitoring...");
}

void loop() {
  int mq2Raw = analogRead(A0);
  int mq135Alert = digitalRead(MQ135_DOUT);
  bool gasDetected = (mq2Raw > MQ2_THRESHOLD) || (mq135Alert == LOW);

  if (gasDetected) {
    digitalWrite(LED_RED, HIGH);
    digitalWrite(LED_GREEN, LOW);
    digitalWrite(BUZZER, HIGH);
  } else {
    digitalWrite(LED_RED, LOW);
    digitalWrite(LED_GREEN, HIGH);
    digitalWrite(BUZZER, LOW);
  }

  Serial.println("MQ2: " + String(mq2Raw) + " | MQ135: " + String(mq135Alert == LOW ? "GAS" : "CLEAR") + " | Status: " + String(gasDetected ? "ALERT" : "SAFE"));

  // Send to dashboard
  if (WiFi.status() == WL_CONNECTED) {
    WiFiClient client;
    HTTPClient http;
    String payload = "{\"mq2\":" + String(mq2Raw) +
                     ",\"mq135_alert\":" + String(mq135Alert == LOW ? 1 : 0) +
                     ",\"gas_detected\":" + String(gasDetected ? 1 : 0) + "}";

    http.begin(client, serverURL);
    http.addHeader("Content-Type", "application/json");
    int httpCode = http.POST(payload);
    Serial.println("HTTP: " + String(httpCode));
    http.end();
  }

  delay(2000);
}
