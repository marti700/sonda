# Start with a lightweight base image
FROM python:3.9-slim

# Set a working directory
WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir paho-mqtt pyserial

# Copy the rest of the application code
COPY . .

# Create a new user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

#Change ownership of the application files
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "LoRa_service.py"]
