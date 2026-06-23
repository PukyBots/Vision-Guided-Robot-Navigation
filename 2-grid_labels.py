import cv2
import numpy as np

cap = cv2.VideoCapture(0)

while True:

    ret, frame = cap.read()
    if not ret:
        break

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

    if contours:

        # largest contour should be the arena/grid
        largest = max(contours, key=cv2.contourArea)

        area = cv2.contourArea(largest)

        if area > 50000:

            x, y, w, h = cv2.boundingRect(largest)

            cv2.rectangle(
                display,
                (x, y),
                (x+w, y+h),
                (0,255,0),
                3
            )

            cell_w = w / 5.0
            cell_h = h / 5.0

            # draw grid
            for i in range(6):

                px = int(x + i*cell_w)
                py = int(y + i*cell_h)

                cv2.line(
                    display,
                    (px, y),
                    (px, y+h),
                    (255,0,0),
                    2
                )

                cv2.line(
                    display,
                    (x, py),
                    (x+w, py),
                    (255,0,0),
                    2
                )

            # labels
            for row in range(5):
                for col in range(5):

                    cx = int(x + (col + 0.5)*cell_w)
                    cy = int(y + (row + 0.5)*cell_h)

                    cv2.putText(
                        display,
                        f"({row},{col})",
                        (cx-25, cy),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0,0,255),
                        2
                    )

    cv2.imshow("Threshold", thresh)
    cv2.imshow("Grid Labels", display)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()