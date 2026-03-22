# 🔷 1. Libraries

```cpp
#include <WiFi.h>
#include <WebServer.h>
```

* WiFi.h → Enables ESP32 WiFi functionality
* WebServer.h → Creates a local HTTP server on ESP32

👉 This allows your robot to be controlled via web requests (like from Python/OpenCV ArUco detection system)

# 🔷 2. WiFi Credentials

```cpp
const char* ssid = "HELLO";
const char* password = "4567890123";
```

* Stores WiFi SSID and password
* ESP32 connects to this network

# 🔷 3. Web Server Initialization

```cpp
WebServer server(80);
```

* Creates a web server on port 80 (HTTP default)

Will listen for commands like:

```
http://ESP_IP/move?cmd=3&speed=120
```

# 🔷 4. Motor Pin Definitions

## Motor A (Left)

```cpp
const uint8_t A_RPWM = 32;
const uint8_t A_LPWM = 33;
const uint8_t A_R_EN = 26;
const uint8_t A_L_EN = 25;
```

## Motor B (Right)

```cpp
const uint8_t B_RPWM = 12;
const uint8_t B_LPWM = 13;
const uint8_t B_R_EN = 14;
const uint8_t B_L_EN = 27;
```

👉 These are L298N / motor driver pins:

* RPWM → Forward direction PWM
* LPWM → Reverse direction PWM
* EN → Enable motor driver channel

# 🔷 5. Watchdog Variables

```cpp
unsigned long lastCommandTime = 0;
const unsigned long WATCHDOG_TIMEOUT = 1000;
```

* Stores last time a command was received
* Timeout = 1000 ms (1 second)

👉 If no command → robot stops (safety feature)

# 🔷 6. Motor Control Functions

## 🛑 Stop Motors

```cpp
void stopMotors() {
  analogWrite(A_RPWM, 0);
  analogWrite(A_LPWM, 0);
  analogWrite(B_RPWM, 0);
  analogWrite(B_LPWM, 0);
}
```

* Sends 0 PWM → no voltage → motors stop

## 🔄 Rotate Right

```cpp
void rotateRight(int speed) {
  analogWrite(A_RPWM, speed);
  analogWrite(A_LPWM, 0);
  analogWrite(B_RPWM, speed);
  analogWrite(B_LPWM, 0);
}
```

* Both motors rotate in same direction
  👉 Robot turns right (depending on wiring)

## 🔄 Rotate Left

```cpp
void rotateLeft(int speed) {
  analogWrite(A_RPWM, 0);
  analogWrite(A_LPWM, speed);
  analogWrite(B_RPWM, 0);
  analogWrite(B_LPWM, speed);
}
```

* Reverse direction of both motors
  👉 Robot turns left

## ⬆️ Move Forward

```cpp
void moveForward(int speed) {
  analogWrite(A_RPWM, speed);
  analogWrite(A_LPWM, 0);
  analogWrite(B_RPWM, 0);
  analogWrite(B_LPWM, speed);
}
```

⚠️ Important:

* Left motor uses A_RPWM
* Right motor uses B_LPWM

👉 This is due to mirrored wiring

# 🔷 7. Command Handler (Core Logic 🔥)

```cpp
void handleMove() {
```

👉 This function runs when `/move` endpoint is hit

## Reset Watchdog

```cpp
lastCommandTime = millis();
```

* Updates last command time

## Check Command Exists

```cpp
if (server.hasArg("cmd")) {
```

* Checks if URL has cmd parameter

## Read Command

```cpp
int cmd = server.arg("cmd").toInt();
```

* Converts command to integer

Example:

* cmd=1 → rotateRight

## Default Speed

```cpp
int speed = 100;
```

## Custom Speed

```cpp
if (server.hasArg("speed")) {
  speed = server.arg("speed").toInt();
  speed = constrain(speed, 0, 255);
}
```

* Reads speed from URL
* Limits it between 0–255 (PWM range)

## Command Execution

```cpp
if (cmd == 1) rotateRight(speed);
else if (cmd == 2) rotateLeft(speed);
else if (cmd == 3) moveForward(speed);
else stopMotors();
```

👉 Mapping:

| cmd  | Action  |
| ---- | ------- |
| 1    | Right   |
| 2    | Left    |
| 3    | Forward |
| else | Stop    |

## Send Response

```cpp
server.send(200, "text/plain", "OK");
```

* Sends HTTP success response

## Error Case

```cpp
server.send(400, "text/plain", "Missing cmd");
```

* If no command → error response

# 🔷 8. Setup Function

```cpp
void setup() {
```

## Serial Start

```cpp
Serial.begin(115200);
```

* Starts serial monitor

## Pin Modes

```cpp
pinMode(A_RPWM, OUTPUT); ...
```

* Sets all motor pins as OUTPUT

## Enable Motors

```cpp
digitalWrite(A_R_EN, HIGH);
digitalWrite(A_L_EN, HIGH);
digitalWrite(B_R_EN, HIGH);
digitalWrite(B_L_EN, HIGH);
```

* Enables motor driver channels

## Stop Motors Initially

```cpp
stopMotors();
```

## WiFi Connection

```cpp
WiFi.setAutoReconnect(true);
WiFi.begin(ssid, password);

while (WiFi.status() != WL_CONNECTED) {
  delay(500); Serial.print(".");
}
```

* Waits until WiFi connects

## Confirmation

```cpp
Serial.println("\nConnected!");
```

## Server Routes

```cpp
server.on("/", []() { server.send(200, "text/plain", "Ready"); });
```

* Root endpoint → returns "Ready"

```cpp
server.on("/move", handleMove);
```

* /move endpoint → controls robot

## Start Server

```cpp
server.begin();
```

# 🔷 9. Loop Function

```cpp
void loop() {
```

## Handle Requests

```cpp
server.handleClient();
```

* Continuously listens for HTTP requests

## Safety Watchdog

```cpp
if (millis() - lastCommandTime > WATCHDOG_TIMEOUT) {
  stopMotors();
}
```

👉 If no command received in 1 second:

* Robot automatically stops
* Prevents runaway robot 🔥

# 🔷 🔥 Final Working Summary

👉 Flow:

* ESP32 connects to WiFi
* Starts web server
* Your PC (ArUco detection code) sends HTTP commands
* ESP32 receives `/move?cmd=X&speed=Y`
* Executes motor function
* If no command → stops automatically

# 🔷 🚀 How It Connects to ArUco System

Your OpenCV code will:

* Detect marker ID

* Convert it into command:

  * ID 1 → cmd=1 (right)
  * ID 2 → cmd=2 (left)
  * ID 3 → cmd=3 (forward)

* Send HTTP request to ESP32
