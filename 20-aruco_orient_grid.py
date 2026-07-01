import cv2
import cv2.aruco as aruco
import numpy as np
import math

cap = cv2.VideoCapture(0)

aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()

# Grid reference directions
GRID = {
    "EAST": 0,
    "SOUTH": 90,
    "WEST": 180,
    "NORTH": 270
}

while True:

    ret, frame = cap.read()
    if not ret:
        break

    corners, ids, _ = aruco.detectMarkers(
        frame,
        aruco_dict,
        parameters=parameters
    )

    if ids is not None:

        marker = corners[0][0]

        tl = marker[0]
        tr = marker[1]

        # Orientation of top edge
        dx = tr[0] - tl[0]
        dy = tr[1] - tl[1]

        angle = math.degrees(math.atan2(dy, dx))

        if angle < 0:
            angle += 360

        # Robot center
        cx = int(np.mean(marker[:,0]))
        cy = int(np.mean(marker[:,1]))

        # Draw arrow
        length = 60
        endx = int(cx + length*np.cos(math.radians(angle)))
        endy = int(cy + length*np.sin(math.radians(angle)))

        cv2.arrowedLine(frame, (cx,cy), (endx,endy),
                        (255,255,0), 3)

        cv2.circle(frame,(cx,cy),5,(0,0,255),-1)

        print(f"\nRobot Angle : {angle:.2f}°")

        # Difference from each grid direction
        for direction, ref in GRID.items():

            diff = (angle - ref + 180) % 360 - 180

            print(f"{direction:6s}: {diff:+6.2f}°")

        # Closest direction
        closest = min(
            GRID,
            key=lambda d: abs((angle-GRID[d]+180)%360-180)
        )

        cv2.putText(frame,
                    f"{closest} ({angle:.1f})",
                    (20,40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,255,0),
                    2)

    cv2.imshow("Robot Orientation", frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()