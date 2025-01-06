import serial

# Open the serial port at the desired baud rate
ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)

# Function to read data from UART
def read_uart():
    try:
        while True:
            # Read a line from the UART
            line = ser.readline().decode('utf-8').rstrip()
            if line:
                print(f"Received: {line}")
    except KeyboardInterrupt:
        print("Program stopped by user")
    finally:
        ser.close()

if __name__ == '__main__':
    read_uart()
