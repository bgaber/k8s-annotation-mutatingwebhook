# Use the official Python image.
FROM python:3.9-slim

# Set the working directory.
WORKDIR /app

# Copy the requirements file.
COPY requirements.txt requirements.txt

# Install dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the webhook server code.
COPY app/webhook.py webhook.py

# Expose port 443 for the webhook.
EXPOSE 443

# Run the webhook server.
CMD ["python", "webhook.py"]

