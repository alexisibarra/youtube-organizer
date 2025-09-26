#!/bin/bash
# Script to generate both backend and frontend SSL certificates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR/.."

bash "$SCRIPT_DIR/generate-backend-cert.sh"
bash "$SCRIPT_DIR/generate-frontend-cert.sh"

echo "All certificates generated."