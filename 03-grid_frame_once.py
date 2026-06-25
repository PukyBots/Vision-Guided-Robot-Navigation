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