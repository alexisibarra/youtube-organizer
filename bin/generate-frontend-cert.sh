#!/bin/bash
# Script to generate frontend SSL certificates
# subjectAltName is mandatory: browsers have ignored CN for hostname matching since Chrome 58.
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout frontend/certs/localhost.key \
  -out frontend/certs/localhost.crt \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
echo "Frontend certificate generated at frontend/certs/localhost.crt and .key"