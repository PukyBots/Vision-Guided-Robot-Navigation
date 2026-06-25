import cv2
import numpy as np
import cv2.aruco as aruco
import math
import heapq
import time
import paho.mqtt.client as mqtt
from itertools import combinations


BROKER = "192.168.254.180" #RPI IP

client = mqtt.Client()

try:
    client.connect(BROKER, 1883, 60)
    client.loop_start()
    mqtt_connected = True
    print("MQTT Connected")

except Exception as e:
    mqtt_connected = False
    print("MQTT Connection Failed:", e)


def send(cmd):

    global mqtt_connected

    if not mqtt_connected:
        print("MQTT Not Connected")
        return False

    try:

        result = client.publish(
            "robot/cmd",
            cmd
        )

        if result.rc == mqtt.MQTT_ERR_SUCCESS:

            print(f"Sent: {cmd}")
            return True

        else:

            print("Publish Failed")
            return False

    except Exception as e:

        print("MQTT Error:", e)
        mqtt_connected = False
        return False

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


def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal):

    rows = len(grid)
    cols = len(grid[0])

    pq = []

    heapq.heappush(
        pq,
        (0, start)
    )

    came_from = {}

    g_score = {start: 0}

    while pq:

        _, current = heapq.heappop(pq)

        if current == goal:

            path = [current]

            while current in came_from:
                current = came_from[current]
                path.append(current)

            return path[::-1]

        r, c = current

        for dr, dc in [
            (-1,0),
            (1,0),
            (0,-1),
            (0,1)
        ]:

            nr = r + dr
            nc = c + dc

            if not (
                0 <= nr < rows and
                0 <= nc < cols
            ):
                continue

            if grid[nr][nc] == 1:
                continue

            neighbor = (nr, nc)

            tentative_g = (
                g_score[current] + 1
            )

            if (
                neighbor not in g_score or
                tentative_g < g_score[neighbor]
            ):

                came_from[neighbor] = current
                g_score[neighbor] = tentative_g

                f = (
                    tentative_g +
                    heuristic(
                        neighbor,
                        goal
                    )
                )

                heapq.heappush(
                    pq,
                    (f, neighbor)
                )

    return None


    
if len(contours) > 0:

    largest = max(contours, key=cv2.contourArea)

    x, y, w, h = cv2.boundingRect(largest)

    print(f"Grid Bounding Box: x={x}, y={y}, w={w}, h={h}")

    cell_w = w / 4.8
    cell_h = h / 4.8

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

blue_boxes = []
red_boxes = []
obstacles = []


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

    if not (x <= cx <= x + w and y <= cy <= y + h):
        continue

    col = int((cx - x) / cell_w)
    row = int((cy - y) / cell_h)

    if 0 <= row < 5 and 0 <= col < 5:

        print(f"Blue bonus found at ({row},{col})")
        blue_boxes.append((row, col))

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

    if not (x <= cx <= x + w and y <= cy <= y + h):
        continue

    col = int((cx - x) / cell_w)
    row = int((cy - y) / cell_h)

    if 0 <= row < 5 and 0 <= col < 5:

        print(f"Red bonus found at ({row},{col})")
        red_boxes.append((row, col))

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

# =====================================
# BROWN OBSTACLES
# =====================================

hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

# Brown range (may need tuning)
lower_brown = np.array([5, 50, 30])
upper_brown = np.array([25, 255, 200])

arena_mask = np.zeros_like(gray)

cv2.rectangle(
    arena_mask,
    (x, y),
    (x + w, y + h),
    255,
    -1
)

brown_mask = cv2.inRange(
    hsv,
    lower_brown,
    upper_brown
)

brown_mask = cv2.bitwise_and(
    brown_mask,
    brown_mask,
    mask=arena_mask
)

kernel = np.ones((5,5), np.uint8)

brown_mask = cv2.morphologyEx(
    brown_mask,
    cv2.MORPH_OPEN,
    kernel
)

brown_contours, _ = cv2.findContours(
    brown_mask,
    cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_SIMPLE
)

for cnt in brown_contours:

    area = cv2.contourArea(cnt)

    if area < 1000:
        continue

    bx, by, bw, bh = cv2.boundingRect(cnt)

    cx = bx + bw // 2
    cy = by + bh // 2

    col = int((cx - x) / cell_w)
    row = int((cy - y) / cell_h)

    if 0 <= row < 5 and 0 <= col < 5:

        print(f"Obstacle found at ({row},{col})")
        obstacles.append((row, col))

        cv2.rectangle(
            display,
            (bx, by),
            (bx + bw, by + bh),
            (0, 255, 255),
            3
        )

        cv2.putText(
            display,
            f"OBS ({row},{col})",
            (bx, by - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )


# =====================================
# ROBOT DETECTION (ARUCO)
# =====================================

robot_row = None
robot_col = None
robot_angle = None
robot_id = None
robot_direction = None
last_status = ""

def on_message(client, userdata, msg):

    global last_status

    payload = msg.payload.decode()

    print("STATUS:", payload)

    last_status = payload


client.subscribe("robot/status")
client.on_message = on_message

def wait_for(expected, timeout=5):

    global last_status

    start = time.time()

    while True:

        if last_status == expected:
            last_status = ""
            return True

        if time.time() - start > timeout:
            print(f"Timeout waiting for {expected}")
            return False

        time.sleep(0.05)



aruco_dict = aruco.getPredefinedDictionary(
    aruco.DICT_4X4_50
)

parameters = aruco.DetectorParameters()

corners, ids, rejected = aruco.detectMarkers(
    frame,
    aruco_dict,
    parameters=parameters
)

if ids is None:
    print("No ArUco marker detected")
else:
    print("Detected markers:", ids.flatten())


def get_direction(angle):

    if angle >= 315 or angle < 45:
        return "EAST"

    elif 45 <= angle < 135:
        return "SOUTH"

    elif 135 <= angle < 225:
        return "WEST"

    else:
        return "NORTH"


def path_direction(current, nxt):

    r1, c1 = current
    r2, c2 = nxt

    if r2 < r1:
        return "NORTH"

    elif r2 > r1:
        return "SOUTH"

    elif c2 > c1:
        return "EAST"

    else:
        return "WEST"
    

def generate_commands(path, start_direction):

    commands = []

    current_heading = start_direction

    for i in range(len(path)-1):

        desired_heading = path_direction(
            path[i],
            path[i+1]
        )

        if desired_heading != current_heading:

            commands.append(
                f"ROTATE {desired_heading}"
            )

            current_heading = desired_heading

        commands.append(
            "MOVE NORTH"
        )

    return commands   

if ids is not None:

    aruco.drawDetectedMarkers(display, corners, ids)

    # Use first detected marker
    marker = corners[0][0]

    robot_id = int(ids[0][0])

    tl = marker[0]
    tr = marker[1]
    br = marker[2]
    bl = marker[3]

    # Marker center
    cx = int(np.mean(marker[:, 0]))
    cy = int(np.mean(marker[:, 1]))

    # Convert to grid cell
    if x <= cx <= x+w and y <= cy <= y+h:

        robot_col = int((cx - x) / cell_w)
        robot_row = int((cy - y) / cell_h)

        start_x = int(x + robot_col * cell_w)
        start_y = int(y + robot_row * cell_h)

        cv2.rectangle(
            display,
            (start_x, start_y),
            (int(start_x + cell_w), int(start_y + cell_h)),
            (255, 255, 255),
            3
        )

        cv2.putText(
            display,
            "START",
            (start_x + 10, start_y + int(cell_h/2)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 0, 255),
            2,
            cv2.LINE_AA
        )

        # -------------------------
        # Orientation
        # -------------------------
        dx = tr[0] - tl[0]
        dy = tr[1] - tl[1]

        robot_angle = math.degrees(
            math.atan2(dy, dx)
        )

        if robot_angle < 0:
            robot_angle += 360

        robot_direction = get_direction(robot_angle)

        if robot_row is None:
            print("Robot not detected!")
            exit()

   
        print(
            f"Robot ID={robot_id} "
            f"Cell=({robot_row},{robot_col}) "
            f"Angle={robot_angle:.1f}"
            f"Facing={robot_direction}"
        )

    
        # Draw center
        cv2.circle(
            display,
            (cx, cy),
            6,
            (255,255,0),
            -1
        )

        # Draw heading arrow
        length = 50

        end_x = int(
            cx + length *
            math.cos(math.radians(robot_angle))
        )

        end_y = int(
            cy + length *
            math.sin(math.radians(robot_angle))
        )

        cv2.arrowedLine(
            display,
            (cx, cy),
            (end_x, end_y),
            (255,255,0),
            3
        )


goal_row = None
goal_col = None

def mouse_click(event, mx, my, flags, param):
    global goal_row, goal_col, goal_changed

    if event == cv2.EVENT_LBUTTONDOWN:

        if x <= mx <= x + w and y <= my <= y + h:

            new_col = int((mx - x) / cell_w)
            new_row = int((my - y) / cell_h)

            # Update only if goal actually changed
            if (new_row, new_col) != (goal_row, goal_col):

                goal_row = new_row
                goal_col = new_col

                goal_changed = True

                print(f"\nGOAL = ({goal_row},{goal_col})")



blue_boxes = sorted(list(set(blue_boxes)))
red_boxes = sorted(list(set(red_boxes)))
obstacles = sorted(list(set(obstacles)))


# ==========================
# Create 5x5 Occupancy Matrix
# ==========================

occupancy = [[0 for _ in range(5)] for _ in range(5)]

# Obstacles = 1
for row, col in obstacles:
    occupancy[row][col] = 1

# Blue bonus = 2
for row, col in blue_boxes:
    occupancy[row][col] = 2

# Red bonus = 3
for row, col in red_boxes:
    occupancy[row][col] = 3


# =====================================
# Mark START position
# =====================================

if robot_row is not None and robot_col is not None:

    # Robot cell should be empty
    occupancy[robot_row][robot_col] = 0

    print(f"START = ({robot_row},{robot_col})")




cv2.namedWindow("Grid Labels")
cv2.setMouseCallback("Grid Labels", mouse_click)

MISSION_TIME = 20

BONUS_VALUE = {
    2: 5,   # blue
    3: 10   # red
}

def estimate_path_time(path, start_direction):

    heading = start_direction
    total_time = 0

    for i in range(len(path)-1):

        desired = path_direction(
            path[i],
            path[i+1]
        )

        if desired != heading:

            turn = get_rotation_command(
                heading,
                desired
            )

            if turn in ["L", "R"]:
                total_time += 1

            elif turn == "B":
                total_time += 2

            heading = desired

        total_time += 1

    return total_time


def optimal_time_constrained_path(
    grid,
    start,
    goal,
    start_direction,
    max_time
):

    bonuses = []

    for r in range(5):
        for c in range(5):

            if grid[r][c] in [2,3]:
                bonuses.append((r,c))

    best_score = -1
    best_time = 999
    best_path = None

    # Check all subset sizes
    for k in range(len(bonuses)+1):

        for subset in combinations(
            bonuses,
            k
        ):

            current = start

            full_path = [start]

            valid = True
            score = 0

            for bonus in subset:

                segment = astar(
                    grid,
                    current,
                    bonus
                )

                if segment is None:
                    valid = False
                    break

                full_path.extend(
                    segment[1:]
                )

                score += BONUS_VALUE[
                    grid[bonus[0]][bonus[1]]
                ]

                current = bonus

            if not valid:
                continue

            segment = astar(
                grid,
                current,
                goal
            )

            if segment is None:
                continue

            full_path.extend(
                segment[1:]
            )

            total_time = estimate_path_time(
                full_path,
                start_direction
            )

            if total_time > max_time:
                continue

            if score > best_score:

                best_score = score
                best_time = total_time
                best_path = full_path

            elif (
                score == best_score and
                total_time < best_time
            ):

                best_time = total_time
                best_path = full_path

    return best_path, best_score, best_time


def get_rotation_command(current, target):

    dirs = ["NORTH", "EAST", "SOUTH", "WEST"]

    cur = dirs.index(current)
    tar = dirs.index(target)

    diff = (tar - cur) % 4

    if diff == 0:
        return "S"      # already facing target

    elif diff == 1:
        return "R"      # 90° right

    elif diff == 2:
        return "B"      # 180°

    elif diff == 3:
        return "L"      # 90° left
    

goal_changed = False
path = []
current_heading = robot_direction
# ---------------------------
# Display forever
# ---------------------------
while True:

    temp_display = display.copy()

    

    if goal_row is not None:

        goal_x = int(x + goal_col * cell_w)
        goal_y = int(y + goal_row * cell_h)

        cv2.rectangle(
            temp_display,
            (goal_x, goal_y),
            (int(goal_x + cell_w), int(goal_y + cell_h)),
            (0, 255, 255),
            3
        )

        cv2.putText(
            temp_display,
            "GOAL",
            (goal_x + 10, goal_y + int(cell_h/2)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0,255,255),
            2
        )

    if goal_changed:

        arena = {
            "blue_bonus": blue_boxes,
            "red_bonus": red_boxes,
            "obstacles": obstacles,
            "start": (robot_row, robot_col),
            "goal": (goal_row, goal_col),
        }

        print("\n" + "="*40)
        print("ARENA UPDATED")
        print("="*40)
        print(arena)
        print("="*40)
        

        occupancy_display = [row[:] for row in occupancy]

        # Mark Start
        if robot_row is not None and robot_col is not None:
            occupancy_display[robot_row][robot_col] = 4

        # Mark Goal
        if goal_row is not None and goal_col is not None:
            occupancy_display[goal_row][goal_col] = 5

        start = (robot_row, robot_col)
        goal = (goal_row, goal_col)

        path, score, total_time = (
            optimal_time_constrained_path(
                occupancy_display,
                (robot_row, robot_col),
                (goal_row, goal_col),
                robot_direction,
                MISSION_TIME
            )
        )

        print("\OPTIMAL PATH")
        print(path)

        print(
            f"Score={score}"
        )

        print(
            f"Estimated Time={total_time}s"
        )

        goal_changed = False

        print("\n" + "="*40)
        print("          OCCUPANCY MATRIX")
        print("="*40)

        print("      0  1  2  3  4")

        for i, row in enumerate(occupancy_display):
            print(f"Row {i}: {row}")

        print("="*40)
        print()

        commands = generate_commands(
            path,
            robot_direction
        )

       
        compressed = []

        i = 0

        while i < len(commands):

            cmd = commands[i]

            if cmd.startswith("MOVE"):

                count = 1

                while (
                    i + count < len(commands)
                    and commands[i + count] == cmd
                ):
                    count += 1

                compressed.append(f"{cmd} {count}")

                i += count

            else:
                compressed.append(cmd)
                i += 1

        print("\nCOMPRESSED COMMANDS")
        print("=" * 40)

        for c in compressed:
            print(c)

        
        current_heading = robot_direction

        for cmd in compressed:

            print(f"\nExecuting: {cmd}")

            if cmd.startswith("ROTATE"):

                desired_heading = cmd.split()[1]

                turn_cmd = get_rotation_command(
                    current_heading,
                    desired_heading
                )

                if turn_cmd != "S":

                    print(
                        f"{current_heading} -> "
                        f"{desired_heading} = "
                        f"{turn_cmd}"
                    )

                    send(turn_cmd)

                    if turn_cmd == "L":
                        wait_for("L_DONE")

                    elif turn_cmd == "R":
                        wait_for("R_DONE")

                    elif turn_cmd == "B":
                        wait_for("B_DONE")

                current_heading = desired_heading

            elif cmd.startswith("MOVE NORTH"):

                steps = int(cmd.split()[-1])

                for i in range(steps):
                  
                    print(
                        f"Sent: F ({i+1}/{steps})"
                    )

                    send("F")
                    wait_for("F_DONE")

        print("\nPath Complete")

        #Update start position
        robot_row = goal_row
        robot_col = goal_col

        robot_direction = current_heading

        print(
            f"NEW START = ({robot_row},{robot_col})"
            f"Facing={robot_direction}"
        )

        # Clear goal
        goal_row = None
        goal_col = None

        path = []

        print("\nWaiting for next goal click...")

    
    if path:

        for i in range(len(path)-1):

            r1, c1 = path[i]
            r2, c2 = path[i+1]

            p1 = (
                int(x + (c1 + 0.5) * cell_w),
                int(y + (r1 + 0.5) * cell_h)
            )

            p2 = (
                int(x + (c2 + 0.5) * cell_w),
                int(y + (r2 + 0.5) * cell_h)
            )

            cv2.line(
                temp_display,
                p1,
                p2,
                (0,255,0),
                4
            )


    cv2.imshow("Grid Labels", temp_display)


    key = cv2.waitKey(1)

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()