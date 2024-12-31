# import serial
import paho.mqtt.client as mqtt
from datetime import datetime

# Setup serial connection
# ser = serial.Serial('/dev/ttyS0', 9600, timeout=1)

# MQTT setup
mqtt_client = mqtt.Client()
mqtt_client.connect("10.0.0.38", 1883, 60)  # Replace with your MQTT broker details

def read_uart():
    i = 0
    while True:
        # data = ser.readline().decode('utf-8').strip()
        data = i + 1  
        if data:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = f"{timestamp}: {data}"
            print(f"Read: {message}")
            mqtt_client.publish("sonda/uart", message)
        i = i + 1

if __name__ == "__main__":
    mqtt_client.loop_start()
    read_uart()
