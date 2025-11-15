#!/bin/bash
set -e  # Exit on error

echo "=========================================="
echo "Azure DevOps Sprint MCP Server - Restart"
echo "=========================================="
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Stop the server
echo "Step 1: Stopping server..."
echo ""
./scripts/stop.sh

echo ""
echo "Waiting 2 seconds..."
sleep 2
echo ""

# Start the server
echo "Step 2: Starting server..."
echo ""
./scripts/start.sh
