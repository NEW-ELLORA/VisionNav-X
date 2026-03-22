import cv2
import cv2.aruco as aruco
import numpy as np
import requests
import math
import time

# ===============================
# ESP32 CONFIG & SESSION
# ===============================
ESP_IP = "http://10.163.199.85"
session = requests.Session() 

print("Connecting to ESP32...")
try:
    r = session.get(ESP_IP, timeout=1.0)
    print("ESP32 Connected")
except:
    print("ESP32 Not reachable (continuing anyway)")

# ===============================
# CAMERA START
# ===============================
print("Starting Camera...")
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera not detected!")
    exit()

# ===============================
# ARUCO SETUP
# ===============================
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, parameters)

last_command = -1
last_speed = -1
last_time = 0

def send_command(cmd, speed=0):
    global last_command, last_speed, last_time
    
    now = time.time()
    # PACE COMMANDS: Wait at least 50ms between requests to avoid hanging ESP32
    if now - last_time < 0.05 and cmd != 0:
        return

    # Filter move commands for stability
    if cmd == last_command and abs(speed - last_speed) < 15 and cmd != 0:
        return
        
    try:
        session.get(f"{ESP_IP}/move?cmd={cmd}&speed={speed}", timeout=0.5)
        last_command = cmd
        last_speed = speed
        last_time = now
    except:
        pass

print("System Running... Press 'ESC' to exit | 'F' to toggle Fullscreen")

# Create a resizable window
cv2.namedWindow("ArUco Rotation Controller", cv2.WINDOW_NORMAL)
# Set window to Fullscreen
cv2.setWindowProperty("ArUco Rotation Controller", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        ret, frame = cap.read()
        if not ret: break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = detector.detectMarkers(gray)

        bot_center, target_center, front_point = None, None, None

        if ids is not None:
            ids_flat = ids.flatten()
            for i, marker_id in enumerate(ids_flat):
                pts = corners[i][0]
                center = pts.mean(axis=0).astype(int)
                
                # Debug: Show ID on screen
                cv2.putText(frame, f"ID:{marker_id}", (center[0], center[1]-10), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                if marker_id == 3: # BOT
                    bot_center = center
                    front_point = ((pts[0] + pts[1]) / 2).astype(int)
                    # RED LINE: Bot orientation
                    cv2.line(frame, tuple(bot_center), tuple(front_point), (0, 0, 255), 4)
                elif marker_id == 7: # TARGET
                    target_center = center
                    cv2.circle(frame, tuple(center), 10, (0, 255, 0), -1)

        # ===============================
        # ALIGNMENT LOGIC & PATH DRAWING
        # ===============================
        if bot_center is not None and target_center is not None:
            # BLUE LINE: Path from bot to target
            cv2.line(frame, tuple(bot_center), tuple(target_center), (255, 0, 0), 3)

            bot_vec = np.array(front_point) - np.array(bot_center)
            target_vec = np.array(target_center) - np.array(bot_center)
            cross = bot_vec[0] * target_vec[1] - bot_vec[1] * target_vec[0]
            dot = bot_vec[0] * target_vec[0] + bot_vec[1] * target_vec[1]
            angle = math.degrees(math.atan2(cross, dot))
            angle_abs = abs(angle)
            
            # DISTANCE TO TARGET
            dist = math.sqrt((target_center[0]-bot_center[0])**2 + (target_center[1]-bot_center[1])**2)

            cv2.putText(frame, f"Angle: {round(angle, 2)} | Dist: {int(dist)}", (30, 50), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            if angle_abs < 6: # STAGE 1: ALIGNED
                if dist > 60: # Move forward if not close enough
                    speed = 120 # Moderate speed for forward
                    send_command(3, speed) # 3 = Forward
                    status_text, status_color = "ALIGNED - MOVING FORWARD", (255, 255, 0)
                else:
                    send_command(0)
                    status_text, status_color = "TARGET REACHED", (0, 255, 0)
            elif angle_abs < 25: # STAGE 2: NEAR (Slow Turn)
                speed = 85
                send_command(1 if angle > 0 else 2, speed)
                status_text, status_color = "SLOW ADJUST", (0, 165, 255)
            else: # STAGE 3: FAR (Normal Turn)
                speed = int(100 + min(100, angle_abs))
                send_command(1 if angle > 0 else 2, speed)
                status_text, status_color = "ROTATING", (255, 255, 0)

            cv2.putText(frame, status_text, (30, 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        else:
            send_command(0)
            status_text = "MARKER LOST - STOPPED"
            if bot_center is None: status_text = "BOT LOST - STOPPED"
            if target_center is None and bot_center is not None: status_text = "TARGET LOST - STOPPED"
            cv2.putText(frame, status_text, (30, 100), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)

        cv2.imshow("ArUco Rotation Controller", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27: # ESC
            break
        elif key == ord('f') or key == ord('F'):
            # Toggle Fullscreen
            is_full = cv2.getWindowProperty("ArUco Rotation Controller", cv2.WND_PROP_FULLSCREEN)
            cv2.setWindowProperty("ArUco Rotation Controller", cv2.WND_PROP_FULLSCREEN, 
                                  cv2.WINDOW_NORMAL if is_full == cv2.WINDOW_FULLSCREEN else cv2.WINDOW_FULLSCREEN)

finally:
    send_command(0)
    session.close()
    cap.release()
    cv2.destroyAllWindows()

