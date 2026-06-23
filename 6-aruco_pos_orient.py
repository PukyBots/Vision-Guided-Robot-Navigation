import cv2
import cv2.aruco as aruco
import numpy as np
import math

# Initialize USB camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Use new API for ArUco dictionary
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()

print("Starting ArUco detection... Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect markers
    corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None:

        aruco.drawDetectedMarkers(frame, corners, ids)

        for marker_corners, marker_id in zip(corners, ids):

            pts = marker_corners[0]

            tl = pts[0]
            tr = pts[1]
            br = pts[2]
            bl = pts[3]

            # -------------------------
            # Marker center
            # -------------------------
            cx = int(np.mean(pts[:, 0]))
            cy = int(np.mean(pts[:, 1]))

            # -------------------------
            # Orientation
            # Direction = TL -> TR
            # -------------------------
            dx = tr[0] - tl[0]
            dy = tr[1] - tl[1]

            angle = math.degrees(math.atan2(dy, dx))

            if angle < 0:
                angle += 360

            # -------------------------
            # Draw center
            # -------------------------
            cv2.circle(frame, (cx, cy), 5, (0, 255, 0), -1)

            # -------------------------
            # Draw heading arrow
            # -------------------------
            length = 60

            end_x = int(
                cx + length * math.cos(math.radians(angle))
            )

            end_y = int(
                cy + length * math.sin(math.radians(angle))
            )

            cv2.arrowedLine(
                frame,
                (cx, cy),
                (end_x, end_y),
                (255, 0, 0),
                3
            )

            # -------------------------
            # Display info
            # -------------------------
            text = (
                f"ID:{int(marker_id[0])} "
                f"Pos:({cx},{cy}) "
                f"Angle:{angle:.1f}"
            )

            cv2.putText(
                frame,
                text,
                (cx - 80, cy - 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )

            print(
                f"ID={int(marker_id[0])} "
                f"Center=({cx},{cy}) "
                f"Angle={angle:.1f}"
            )

    cv2.imshow("Aruco Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()