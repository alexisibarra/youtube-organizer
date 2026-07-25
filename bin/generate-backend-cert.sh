#!/bin/bash
# Script to generate backend SSL certificates
# subjectAltName is mandatory: browsers have ignored CN for hostname matching since Chrome 58.
# Without a SAN the cert is rejected outright, and on a fetch() subresource there is no
# click-through interstitial — it surfaces only as an opaque "TypeError: Failed to fetch".
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout backend/certs/localhost.key \
  -out backend/certs/localhost.crt \
  -subj "/CN=localhost" \
  -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
echo "Backend certificate generated at backend/certs/localhost.crt and .key"