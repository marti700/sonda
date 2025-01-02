from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import threading

# Set the name of the application from the __name__ variable
# so that flask knows where to find the app resources, like templates and
# static files
app = Flask(__name__)

# This line creates an instance of the SocketIO class.
# The `app` argument is passed to the SocketIO constructor to integrate SocketIO to the Flask application.
# This allows SocketIO to provide real-time, bidirectional communication between the web server
# (Flask application) and the web browser also by doing this we will be able to access socketio from
# the application context
socketio = SocketIO(app)

# Configure database
# The “sqlite:///” prefix tells SQLAlchemy to use SQLite.
# The “sonda.db” part specifies the name of our database file.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///sonda.db'
# This line disables SQLAlchemy's built-in tracking of object modifications.
# By default, SQLAlchemy tracks changes to objects that are associated with the database.
# This tracking can be useful for some applications, but it can also lead to performance issues.
# Setting SQLALCHEMY_TRACK_MODIFICATIONS to False can improve performance in many cases.
# Since this database won't change that often this property is set to False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# This line creates an instance of the SQLAlchemy class.
# The `app` argument is passed to the SQLAlchemy constructor to bind the database to the Flask application.
# This allows the database to be used throughout the application.
db = SQLAlchemy(app)

# Create a database model
# Database models are basically classes that represent database tables in the db
# In this case SQLAlchemy is being told that there is a table in the database
# called measurements that has an numeric primary key column called id,
# a datetime column called timestap and a floating point value column called value
# notice how the Measurements inherit from the db.Model class from SQLAlchemy
class Measurements(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    value = db.Column(db.Float)

    # this method gieves a string representation of a Measurement so each time
    # the print method is called like this: print(measurement) python will print the measurement value using this format:
    # "Measurement <db id of the measurement> - <timestap of the measurement>: <value of the measurement>"
    def __repr__(self):
        return f'<Measurement {self.id} - {self.timestamp}: {self.value}>'

# MQTT setup
mqtt_client = mqtt.Client()

# Define the on_connect callback function for MQTT
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    # Subscribe to the MQTT topic 'sonda/uart'
    client.subscribe("sonda/uart")

# Define the on_message callback function for MQTT
def on_message(client, userdata, msg):
    try:
        message = msg.payload.decode()  # Decode the message payload
        # Split message into timestamp and value
        timestamp_str, value_str = message.split(": ")
        # Convert timestamp string to datetime object
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        value = float(value_str)  # Convert value string to float
        with app.app_context(): # execute the following code block within the applicatio context tha was so gracefully called 'app' at line 11
            # Create a new measurement record
            measurement = Measurements(timestamp=timestamp, value=value)
            db.session.add(measurement)  # Add the measurement to the database session
            db.session.commit()  # Commit the transaction to the database
            # Emit new data to connected clients using Socket.IO
            # the 'new_data' is a custom event being sent, in the index.html there is a javascript function
            # that will look for this event name
            # the other argument is a dctionary with the actual data being sent through the socket
            socketio.emit('new_data', {'timestamp': timestamp_str, 'value': value_str})
    except ValueError as e:
        print(f"Invalid message received: {message}, error: {e}")

# Assign the MQTT callbacks
# no parentheses are used because the onconect property of the mqtt_client
# expects a function as a value if parentheses are used the function will be called
# this will lead to an error because mqtt expects a function reference
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
# Connect to the MQTT broker
mqtt_client.connect("10.0.0.38", 1883, 60)

# Function to run the MQTT loop in a separate thread
# so that borker operations not interfere with the normal
# application flow
def mqtt_loop():
    mqtt_client.loop_forever()

# this method will be executed when a request is made to the root endpoint ('/')
@app.route('/')
def index():
    # Get the filter type from the query parameters, default to 'today'
    filter_type = request.args.get('filter', 'today')
    # Get the start and end date strings from the query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Check if the custom filter is used and the start and end dates are provided
    if filter_type == 'custom' and start_date_str and end_date_str:
        # Convert start and end date strings to datetime objects
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1)
    # Filter by year, month, or week based on the filter type
    elif filter_type == 'year':
        start_date = datetime.now() - timedelta(days=365)
        end_date = datetime.now()
    elif filter_type == 'month':
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
    elif filter_type == 'week':
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
    # Default to showing data collected today
    else:
        start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = datetime.now() + timedelta(days=1)
    # Query the database for measurements within the date range
    measurements = Measurements.query.filter(Measurements.timestamp >= start_date, Measurements.timestamp < end_date).order_by(Measurements.timestamp.desc()).all()

    # Render the HTML template with the measurements and filter variables
    # rendering the filter variables will ensure that the dropdown takes the value of the filter
    # applied by the user on page reload. Whithout this the filter dropdown will always take the
    # value of the first dropdown option.
    return render_template('index.html', measurements=measurements, filter_type=filter_type, start_date=start_date_str, end_date=end_date_str)

if __name__ == '__main__':
    # This line establishes an application context.
    # In Flask, an application context provides access to application-wide objects and configurations.
    # This is essential because database operations (like creating tables)
    # rely on the application context to function correctly.
    with app.app_context():
        # db is the SQLAlchemy instance, which was configured to interact with the database.
        # create_all() instructs SQLAlchemy to examine all the defined database models
        # in this case the Measurements class.
        # It then dynamically creates the corresponding tables in the database
        # based on the model definitions (columns, data types, relationships, etc.).
        db.create_all() # this creates a sonda.db file in the /instance directory

    # Start the MQTT loop in a separate thread
    mqtt_thread = threading.Thread(target=mqtt_loop)
    mqtt_thread.daemon = True
    mqtt_thread.start()

    # Run the Flask application with Socket.IO
    # Why socketio.run instead of app.run?
    # The `socketio.run` function is specifically designed to run Flask applications
    # that are integrated with Socket.IO. It internally handles the initialization
    # and management of the Socket.IO server, which is crucial for enabling real-time communication.

    # app.run is for Standard Flask Apps. The standard app.run function is used
    # for regular Flask applications that don't involve real-time communication. It
    # focuses on starting the Flask development server to serve the web application.

    # Using socketio.run ensures that both the Flask development server and the
    # Socket.IO server are started correctly, providing the necessary environment for
    # real-time updates in your web application.

    # also remember the version of SocketIO being used comes from flask-socketIO package
    # make sense that is has a function to initialize flask and socketIo at the same time
    socketio.run(app, debug=True, host='0.0.0.0')

