import cv2
import numpy as np

cap = cv2.VideoCapture(0)

ret, frame = cap.read()
if not ret:
    print("Failed to capture frame")
    exit()

display = frame.copy()

gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

_, thresh = cv2.threshold(
    gray,
    180,
    255,
    cv2.THRESH_BINARY
)

kernel = np.ones((3,3), np.uint8)
thresh = cv2.morphologyEx(
    thresh,
    cv2.MORPH_CLOSE,
    kernel,
    iterations=2
)

contours, _ = cv2.findContours(
    thresh,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

    
if len(contours) > 0:

    largest = max(contours, key=cv2.contourArea)

    x, y, w, h = cv2.boundingRect(largest)

    print(f"Grid Bounding Box: x={x}, y={y}, w={w}, h={h}")

    cell_w = w / 5.0
    cell_h = h / 5.0

    # Draw grid
    for i in range(6):

        px = int(x + i * cell_w)
        py = int(y + i * cell_h)

        cv2.line(
            display,
            (px, y),
            (px, y + h),
            (0, 255, 0),
            2
        )

        cv2.line(
            display,
            (x, py),
            (x + w, py),
            (0, 255, 0),
            2
        )

    # Draw labels
    for row in range(5):
        for col in range(5):

            cx = int(x + (col + 0.5) * cell_w)
            cy = int(y + (row + 0.5) * cell_h)

            cv2.putText(
                display,
                f"({row},{col})",
                (cx - 25, cy),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
                cv2.LINE_AA
            )

# =====================================
# Detect BLUE and RED bonuses
# =====================================

hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# ---------- BLUE ----------
lower_blue = np.array([90, 80, 80])
upper_blue = np.array([130, 255, 255])

blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)

# ---------- RED ----------
lower_red1 = np.array([0, 80, 80])
upper_red1 = np.array([10, 255, 255])

lower_red2 = np.array([170, 80, 80])
upper_red2 = np.array([180, 255, 255])

red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)

red_mask = cv2.bitwise_or(red_mask1, red_mask2)

# Remove noise
kernel = np.ones((5,5), np.uint8)

blue_mask = cv2.morphologyEx(
    blue_mask,
    cv2.MORPH_OPEN,
    kernel
)

red_mask = cv2.morphologyEx(
    red_mask,
    cv2.MORPH_OPEN,
    kernel
)

# =====================================
# BLUE OBJECTS
# =====================================

blue_contours, _ = cv2.findContours(
    blue_mask,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

for cnt in blue_contours:

    area = cv2.contourArea(cnt)

    if area < 1600:
        continue

    bx, by, bw, bh = cv2.boundingRect(cnt)

    cx = bx + bw//2
    cy = by + bh//2

    col = int((cx - x) / cell_w)
    row = int((cy - y) / cell_h)

    if 0 <= row < 5 and 0 <= col < 5:

        print(f"Blue bonus found at ({row},{col})")

        cv2.rectangle(
            display,
            (bx, by),
            (bx+bw, by+bh),
            (255,0,0),
            3
        )

        cv2.putText(
            display,
            f"BLUE ({row},{col})",
            (bx, by-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255,0,0),
            2
        )

# =====================================
# RED OBJECTS
# =====================================

red_contours, _ = cv2.findContours(
    red_mask,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

for cnt in red_contours:

    area = cv2.contourArea(cnt)

    if area < 1600:
        continue

    bx, by, bw, bh = cv2.boundingRect(cnt)

    cx = bx + bw//2
    cy = by + bh//2

    col = int((cx - x) / cell_w)
    row = int((cy - y) / cell_h)

    if 0 <= row < 5 and 0 <= col < 5:

        print(f"Red bonus found at ({row},{col})")

        cv2.rectangle(
            display,
            (bx, by),
            (bx+bw, by+bh),
            (0,0,255),
            3
        )

        cv2.putText(
            display,
            f"RED ({row},{col})",
            (bx, by-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0,0,255),
            2
        )
        
# ---------------------------
# Display forever
# ---------------------------
while True:

    cv2.imshow("Threshold", thresh)
    cv2.imshow("Grid Labels", display)

    key = cv2.waitKey(1)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()