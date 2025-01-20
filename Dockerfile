# Use official Python runtime as a base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt into the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code into the container
COPY . .

# Expose the default port for Koyeb (not strictly necessary for a Telegram bot)
EXPOSE 8080

# Run the bot
CMD ["python", "main.py"]
