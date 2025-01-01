from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
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
    # Get the filter type from the query parameters, default to 'today'
    filter_type = request.args.get('filter', 'today')
    # Get the start and end date strings from the query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Check if the custom filter is used and the start and end dates are provided
    if filter_type == 'custom' and start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
    # Filter by year, month, or week based on the filter type
    elif filter_type == 'year':
        start_date = datetime.now() - timedelta(days=365)
    elif filter_type == 'month':
        start_date = datetime.now() - timedelta(days=30)
    elif filter_type == 'week':
        start_date = datetime.now() - timedelta(days=7)
    # Default to showing data collected today
    else:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.now() + timedelta(days=1)
    
    # Query the database for measurements within the date range
    measurements = Measurements.query.filter(Measurements.timestamp >= start_date, Measurements.timestamp < end_date).order_by(Measurements.timestamp.desc()).all()
    
    # Render the HTML template with the measurements
    return render_template('index.html', measurements=measurements)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    mqtt_thread = threading.Thread(target=mqtt_loop)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    socketio.run(app, debug=True, host='0.0.0.0')

