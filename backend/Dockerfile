# Dockerfile for YouTube Organizer Backend
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


# Copy the rest of the backend code
COPY . .

# Copy SSL certificates for local HTTPS
COPY certs/ /app/certs/

# Use runserver_plus from django-extensions for SSL support
CMD ["python", "manage.py", "runserver_plus", "0.0.0.0:8000", "--cert-file", "/app/certs/localhost.crt", "--key-file", "/app/certs/localhost.key"]
