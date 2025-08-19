#!/bin/sh
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout backend/certs/localhost.key \
  -out backend/certs/localhost.crt \
  -subj "/CN=localhost"
