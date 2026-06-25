import cv2
import numpy as np

# mouse callback function
def show_hsv(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        hsv_pixel = hsv_frame[y, x]
        print(f"HSV at ({x},{y}) = {hsv_pixel}")

cap = cv2.VideoCapture(0)

cv2.namedWindow("Frame")
cv2.setMouseCallback("Frame", show_hsv)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to HSV
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Show frame
    cv2.imshow("Frame", frame)
    cv2.imshow("HSV", hsv_frame)

    key = cv2.waitKey(1)
    if key == 27:  # ESC to exit
        break

cap.release()
cv2.destroyAllWindows()