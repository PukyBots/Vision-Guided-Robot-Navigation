import cv2
import numpy as np

cap = cv2.VideoCapture(0)  # Replace with RTSP URL if needed

while True:
    ret, frame = cap.read()
    if not ret:
        break

    display = frame.copy()

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect bright (white) grid lines
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)

    # Connect broken lines if necessary
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(
        thresh,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_SIMPLE
    )

    cells = []

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        area = w * h

        # Adjust these values for your setup
        if 2000 < area < 50000:
            cells.append((x, y, w, h))

    # Remove duplicates
    filtered = []
    for cell in cells:
        x, y, w, h = cell

        duplicate = False
        for fx, fy, fw, fh in filtered:
            if abs(x - fx) < 10 and abs(y - fy) < 10:
                duplicate = True
                break

        if not duplicate:
            filtered.append(cell)

    # Sort by rows then columns
    filtered.sort(key=lambda b: (b[1], b[0]))

    # Expecting 25 cells
    if len(filtered) >= 25:

        filtered = filtered[:25]

        # Sort into rows
        rows = []

        current_row = [filtered[0]]

        for box in filtered[1:]:
            if abs(box[1] - current_row[0][1]) < 30:
                current_row.append(box)
            else:
                rows.append(sorted(current_row, key=lambda b: b[0]))
                current_row = [box]

        rows.append(sorted(current_row, key=lambda b: b[0]))

        # Draw labels
        # Draw labels
        for r, row_boxes in enumerate(rows[:5]):

            row_boxes = sorted(row_boxes, key=lambda b: b[0])

            for c, (x, y, w, h) in enumerate(row_boxes[:5]):

                cv2.rectangle(
                    display,
                    (x, y),
                    (x + w, y + h),
                    (0, 255, 0),
                    2
                )

                label = f"({r},{c})"

                # center of box
                text_x = x + w // 2 - 20
                text_y = y + h // 2

                cv2.putText(
                    display,
                    label,
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                    cv2.LINE_AA
                )

    cv2.imshow("Detected Grid", display)
    cv2.imshow("Threshold", thresh)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()