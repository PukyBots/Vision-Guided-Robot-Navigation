#static ip is set on rpi afeez- password is robot@123
#on reboot, the mqtt subscriber runs automatically on rpi as system service file is created
#give commands directly from laptop terminal to rpi to check motion- mosquitto_pub -h 192.168.254.180 -t robot/cmd -m "F"

import serial
import paho.mqtt.client as mqtt

ARDUINO_PORT = "/dev/ttyUSB0"
BAUD = 9600

ser = serial.Serial(
    ARDUINO_PORT,
    BAUD,
    timeout=1
)

BROKER = "localhost"
TOPIC = "robot/cmd"

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT Broker")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):

    cmd = msg.payload.decode().strip()

    print("Received:", cmd)

    if cmd in ["F", "L", "R", "B", "S"]:
        ser.write(cmd.encode())
        print("Sent to Arduino:", cmd)

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, 1883, 60)

client.loop_forever()