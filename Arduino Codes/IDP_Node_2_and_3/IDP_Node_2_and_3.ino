#define MQ135_DOUT D5

void setup() {
  Serial.begin(115200);
  delay(1000);
  pinMode(MQ135_DOUT, INPUT);
  Serial.println("Sensor test starting...");
  
  for (int i = 30; i > 0; i--) {
    Serial.println("Warmup: " + String(i) + "s remaining");
    delay(1000);
  }
  Serial.println("Reading...");
}

void loop() {
  int mq2Raw = analogRead(A0);
  int mq135Digital = digitalRead(MQ135_DOUT);

  Serial.println("MQ2 Raw: " + String(mq2Raw) + " | MQ135 Alert: " + String(mq135Digital == LOW ? "GAS" : "CLEAR"));
  delay(1000);
}
