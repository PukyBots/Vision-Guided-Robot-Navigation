import serial
import time

PORT = "/dev/ttyUSB0"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)

time.sleep(2)

print("Commands:")
print("F = Forward 25 cm")
print("L = Left 90°")
print("R = Right 90°")
print("B = U-turn 180°")
print("S = Stop")
print("Q = Quit")

while True:

    cmd = input("\nEnter command: ").strip().upper()

    if cmd == "Q":
        break

    if cmd in ["F", "L", "R", "B", "S"]:

        ser.write(cmd.encode())

        print(f"Sent: {cmd}")

    else:
        print("Invalid command")

ser.close()