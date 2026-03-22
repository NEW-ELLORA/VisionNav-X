#include <WiFi.h>
#include <WebServer.h>

// ===== WiFi Credentials =====
const char* ssid = " wifi name ";
const char* password = " password ";

WebServer server(80);

// ===== Motor A (Left) =====
const uint8_t A_RPWM = 32;
const uint8_t A_LPWM = 33;
const uint8_t A_R_EN = 26;
const uint8_t A_L_EN = 25;

// ===== Motor B (Right) =====
const uint8_t B_RPWM = 12;
const uint8_t B_LPWM = 13;
const uint8_t B_R_EN = 14;
const uint8_t B_L_EN = 27;

unsigned long lastCommandTime = 0;
const unsigned long WATCHDOG_TIMEOUT = 1000; // Stop if no command for 1 second

void stopMotors() {
  analogWrite(A_RPWM, 0);
  analogWrite(A_LPWM, 0);
  analogWrite(B_RPWM, 0);
  analogWrite(B_LPWM, 0);
}

void rotateRight(int speed) {
  analogWrite(A_RPWM, speed);
  analogWrite(A_LPWM, 0);
  analogWrite(B_RPWM, speed);
  analogWrite(B_LPWM, 0);
}

void rotateLeft(int speed) {
  analogWrite(A_RPWM, 0);
  analogWrite(A_LPWM, speed);
  analogWrite(B_RPWM, 0);
  analogWrite(B_LPWM, speed);
}

void moveForward(int speed) {
  // Mirrored wiring: A_RPWM=Forward, B_LPWM=Forward
  analogWrite(A_RPWM, speed);
  analogWrite(A_LPWM, 0);
  analogWrite(B_RPWM, 0);
  analogWrite(B_LPWM, speed);
}

void handleMove() {
  lastCommandTime = millis(); // Reset watchdog
  if (server.hasArg("cmd")) {
    int cmd = server.arg("cmd").toInt();
    int speed = 100;
    
    if (server.hasArg("speed")) {
      speed = server.arg("speed").toInt();
      speed = constrain(speed, 0, 255);
    }

    if (cmd == 1) rotateRight(speed);
    else if (cmd == 2) rotateLeft(speed);
    else if (cmd == 3) moveForward(speed);
    else stopMotors();
    
    server.send(200, "text/plain", "OK");
  } else {
    server.send(400, "text/plain", "Missing cmd");
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(A_RPWM, OUTPUT); pinMode(A_LPWM, OUTPUT);
  pinMode(A_R_EN, OUTPUT); pinMode(A_L_EN, OUTPUT);
  pinMode(B_RPWM, OUTPUT); pinMode(B_LPWM, OUTPUT);
  pinMode(B_R_EN, OUTPUT); pinMode(B_L_EN, OUTPUT);

  digitalWrite(A_R_EN, HIGH); digitalWrite(A_L_EN, HIGH);
  digitalWrite(B_R_EN, HIGH); digitalWrite(B_L_EN, HIGH);

  stopMotors();

  WiFi.setAutoReconnect(true);
  WiFi.begin(ssid, password);
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500); Serial.print(".");
  }
  Serial.println("\nConnected!");

  server.on("/", []() { server.send(200, "text/plain", "Ready"); });
  server.on("/move", handleMove);
  server.begin();
}

void loop() {
  server.handleClient();
  
  // Safety Watchdog
  if (millis() - lastCommandTime > WATCHDOG_TIMEOUT) {
    stopMotors();
  }
}
