from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime
import paho.mqtt.client as mqtt
import threading

app = Flask(__name__)
socketio = SocketIO(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sonda.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create a database model
class Measurements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    value = db.Column(db.Float)

    def __repr__(self):
        return f'<Measurement {self.id} - {self.timestamp}: {self.value}>'

# MQTT setup
mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("sonda/uart")

def on_message(client, userdata, msg):
    try:
        message = msg.payload.decode()
        timestamp_str, value_str = message.split(": ")
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        value = float(value_str)
        with app.app_context():
            measurement = Measurements(timestamp=timestamp, value=value)
            db.session.add(measurement)
            db.session.commit()
            # print(f"Stored: {measurement}")
            socketio.emit('new_data', {'timestamp': timestamp_str, 'value': value_str})
    except ValueError as e:
        print(f"Invalid message received: {message}, error: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect("10.0.0.38", 1883, 60)

def mqtt_loop():
    mqtt_client.loop_forever()

@app.route('/')
def index():
    measurements = Measurements.query.order_by(Measurements.timestamp.desc()).limit(10).all()
    return render_template('index.html', measurements=measurements)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    mqtt_thread = threading.Thread(target=mqtt_loop)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    socketio.run(app, debug=True, host='0.0.0.0')
