# 🔷 1. Imports

```python
import cv2
import cv2.aruco as aruco
import numpy as np
import requests
import math
import time
```

- cv2 → Core module of OpenCV  
- cv2.aruco → ArUco marker detection module  
- numpy → Vector/matrix operations  
- requests → Sends HTTP requests to ESP32  
- math → Trigonometric calculations  
- time → Timing control  


# 🔷 2. ESP32 Configuration

```python
ESP_IP = "http://10.163.199.85"
session = requests.Session()
```

- Stores ESP32 server IP  
- Session() → Reuses TCP connection (faster than new requests every time)  


# 🔷 3. Connection Check

```python
r = session.get(ESP_IP, timeout=1.0)
```

- Sends HTTP GET request to ESP32  
- timeout=1.0 → waits max 1 second  

👉 Used to verify ESP32 is reachable  


# 🔷 4. Camera Initialization

```python
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    exit()
```

- Opens default camera (index 0)  
- Checks if camera started successfully  


# 🔷 5. ArUco Setup

```python
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)
```

- Loads dictionary with:
  - 4×4 grid markers  
  - 50 unique IDs  

- Sets detection parameters (thresholding, corner refinement, etc.)  
- Creates detector object (optimized pipeline)  


# 🔷 6. Command Memory (Optimization)

```python
last_command = -1
last_speed = -1
last_time = 0
```

👉 Used to:

- Avoid sending repeated commands  
- Reduce ESP32 lag  


# 🔷 7. send_command Function (VERY IMPORTANT 🔥)

```python
def send_command(cmd, speed=0):
```

- Sends movement command to ESP32  


## ⏱ Rate Limiting

```python
if now - last_time < 0.05 and cmd != 0:
    return
```

- Minimum 50 ms gap between commands  

👉 Prevents ESP32 overload  


## 🔁 Command Filtering

```python
if cmd == last_command and abs(speed - last_speed) < 15 and cmd != 0:
    return
```

- If same command + small speed change → ignore  

👉 Improves stability  


## 🌐 HTTP Request

```python
session.get(f"{ESP_IP}/move?cmd={cmd}&speed={speed}", timeout=0.5)
```

- Sends GET request:
```
/move?cmd=3&speed=120
```

👉 This directly controls your ESP32 bot  


# 🔷 8. Window Setup

```python
cv2.namedWindow("ArUco Rotation Controller", cv2.WINDOW_NORMAL)
cv2.setWindowProperty(...)
```

- Creates resizable window  
- Sets fullscreen mode  


# 🔷 9. Main Loop

```python
while True:
```

## 📷 Frame Capture

```python
ret, frame = cap.read()
```

- Captures one frame from camera  


## ⚫ Grayscale Conversion

```python
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
```

- Converts to grayscale  

👉 Required for ArUco detection  


## 🔍 Marker Detection

```python
corners, ids, rejected = detector.detectMarkers(gray)
```

Outputs:

- corners → marker corner coordinates  
- ids → detected marker IDs  
- rejected → false candidates  


# 🔷 10. Marker Processing

```python
for i, marker_id in enumerate(ids_flat):
```

- Loops through detected markers  


## 📍 Center Calculation

```python
center = pts.mean(axis=0).astype(int)
```

👉 Computes centroid:

```
center = (x1 + x2 + x3 + x4) / 4
```


## 🏷 Display ID

```python
cv2.putText(...)
```

- Draws marker ID on screen  


# 🔷 11. Bot & Target Identification

## 🤖 Bot Marker (ID = 3)

```python
bot_center = center
front_point = ((pts[0] + pts[1]) / 2)
```

- bot_center → robot position  
- front_point → direction vector  

👉 Uses top edge of marker to define orientation  


## 🔴 Orientation Line

```python
cv2.line(frame, bot_center, front_point, (0,0,255), 4)
```

- Red line shows where robot is facing  


## 🎯 Target Marker (ID = 7)

```python
target_center = center
```

- Marks goal position  


# 🔷 12. Vector Mathematics (CORE LOGIC 🔥)

## ➡️ Direction Vectors

```python
bot_vec = front_point - bot_center
target_vec = target_center - bot_center
```

- bot_vec → robot facing direction  
- target_vec → direction to target  


## ✖ Cross Product

```python
cross = bot_vec[0] * target_vec[1] - bot_vec[1] * target_vec[0]
```

👉 Determines rotation direction:

- > 0 → rotate right  
- < 0 → rotate left  


## • Dot Product

```python
dot = bot_vec[0] * target_vec[0] + bot_vec[1] * target_vec[1]
```

👉 Measures alignment  


## 📐 Angle Calculation

```python
angle = math.degrees(math.atan2(cross, dot))
```

This computes:

```
θ = tan⁻¹(cross / dot)
```

👉 Gives signed angle between vectors  


## 📏 Distance

```python
dist = math.sqrt(...)
```

👉 Euclidean distance:

```
d = (x2 - x1)^2 + (y2 - y1)^2
```


# 🔷 13. Decision Logic (AI Behavior 🔥)

## ✅ Stage 1: Aligned

```python
if angle_abs < 6:
```

- Robot almost facing target  

```python
if dist > 60:
    send_command(3, 120)
```

👉 Move forward  


## ⚠️ Stage 2: Slight Misalignment

```python
elif angle_abs < 25:
    send_command(1 if angle > 0 else 2, 85)
```

👉 Slow correction  


## 🔄 Stage 3: Large Error

```python
else:
    speed = 100 + min(100, angle_abs)
```

👉 Faster rotation for large angles  


# 🔷 14. Safety Condition

```python
else:
    send_command(0)
```

- If markers lost → STOP  


# 🔷 15. Display Output

```python
cv2.putText(frame, status_text, ...)
```

Shows:

- Angle  
- Distance  
- Current state  


# 🔷 16. Exit Controls

```python
key = cv2.waitKey(1)
```

- ESC → Exit  
- F → Toggle fullscreen  


# 🔷 17. Cleanup

```python
send_command(0)
session.close()
cap.release()
cv2.destroyAllWindows()
```

- Stops robot  
- Releases camera  
- Closes window  


# 🔥 FINAL SYSTEM WORKFLOW

👉 Complete pipeline:

- Camera captures frame  
- OpenCV detects ArUco markers  
- Extract:
  - Bot position  
  - Target position  
  - Orientation  

- Compute:
  - Angle (rotation needed)  
  - Distance  

- Decision logic:
  - Rotate / Move / Stop  

- Send HTTP command to ESP32  
- Robot moves  


# 🔷 🚀 One-Line Technical Summary

👉 This system performs real-time visual servoing using ArUco-based pose estimation, vector geometry (cross/dot products), and HTTP-based actuation control of an ESP32-driven robot.
