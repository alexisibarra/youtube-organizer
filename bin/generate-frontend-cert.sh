#!/bin/bash
# Script to generate frontend SSL certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout frontend/certs/localhost.key \
  -out frontend/certs/localhost.crt \
  -subj "/CN=localhost"
echo "Frontend certificate generated at frontend/certs/localhost.crt and .key"