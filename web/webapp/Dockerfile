# Start with a base image containing Python 3.9
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

# Install slqlite
RUN apt-get update && apt-get install -y sqlite3

# Install the dependencies
RUN pip install --no-cache-dir flask flask-sqlalchemy flask-socketio paho-mqtt

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

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1

# Run the application
CMD ["python", "app.py"]
