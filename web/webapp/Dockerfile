# Start with a base image containing Python 3.9
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install the dependencies
RUN pip install --no-cache-dir flask flask-sqlalchemy flask-socketio paho-mqtt gunicorn eventlet

# Copy the application code into the container
COPY . .

# Create a new user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

#Change ownership of the application files
RUN chown -R appuser:appgroup /app

# Ensure the app directory has the correct permissions
RUN chmod -R 755 /app

# Switch to the non-root user
USER appuser

# Expose the port on which the app runs
EXPOSE 5000

# Run the application
CMD ["gunicorn", "-w", "4", "-k", "eventlet", "-b", "0.0.0.0:5000", "app:app"]
