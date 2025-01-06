import os
import serial
import paho.mqtt.client as mqtt
from datetime import datetime

# Setup serial connection
# the ser variable holds an instance of type Serial (from the serial package)
# the data passed to the constrctor are the following:

# SERIAL PORT ('/dev/ttyS0'):
# the serial port conection this can vary depending on the number of serial devices you
# have conected to the computer running this program, but must of the time the first
# conected serial device gets the /dev/ttyS0 port

# BAUD RATE (9600):
# The 9600 is the baud rate and it is a measure of the number of bits per second
# that can be transmitted or received by the UART device in our case is 9600 becaus this
# is the speed my e32 LoRa module can handle as specified in it's datasheet.

# TIMEOUT (1s):
# the timeout parameter is set to 1 second and this means that if the serial port
# doesn't receive any data within 1 second of attempting to read, the read operation
# will be considered unsuccessful and will return whatever data has been received up to that point
ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)

# MQTT setup
mqtt_client = mqtt.Client() # get and instance of the mqtt client

# Get the MQTT broker address from the environment variable
# In our case these variables are created by docker compose
# as specified in the docker compose file
mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
mqtt_port = int(os.getenv('MQTT_PORT', 1833))

# set the conection details of the mqtt instance
# In this case the 10.0.0.38 represents the hsot IP
# the  1883 represents the port on which the mqtt broker is listening (we are using mosquitto)
# the 60 is the "keep-alive" interval this means that the client have to send a ping to keep the
# conection with the broker alive if the client fails to do this (whithin a minute in this case)
# the broker will drop the conection with the client
mqtt_client.connect(mqtt_broker, mqtt_port, 60)

def read_uart():
    while True: # an infinite loop
        data = ser.readline().decode('utf-8').strip() # will read the serial data send to the UART port
        if data:
			# and will add the timestap when it reads it
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = f"{timestamp}: {data}" # and then create the message that will be send to the broker
            print(f"Read: {message}")
            # finally the message will be published to the "sonda/uart queue"
            mqtt_client.publish("sonda/uart", message)

if __name__ == "__main__":
	# starts a new thread to send/listen to broker messages, this ensures that broker operations
	# susch as publishing or reading does not block the appliation
    mqtt_client.loop_start()
    read_uart() # start reading from UART
