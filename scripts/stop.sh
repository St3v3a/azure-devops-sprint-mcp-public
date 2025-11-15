#!/bin/bash

echo "=========================================="
echo "Azure DevOps Sprint MCP Server - Stop"
echo "=========================================="
echo ""

STOPPED_SOMETHING=false

# Try to stop Docker containers
if command -v docker &> /dev/null && [ -f "docker-compose.yml" ]; then
    echo "Checking for Docker containers..."

    if docker-compose ps | grep -q "Up"; then
        echo "Stopping Docker containers..."
        docker-compose down
        echo "✓ Docker containers stopped"
        STOPPED_SOMETHING=true
    else
        echo "No running Docker containers found"
    fi
    echo ""
fi

# Try to stop Python processes
echo "Checking for Python processes..."
if pgrep -f "python -m src.server" > /dev/null 2>&1; then
    echo "Found running Python MCP server processes"
    echo "Stopping Python processes..."

    pkill -f "python -m src.server"

    # Wait a moment
    sleep 1

    # Check if stopped
    if pgrep -f "python -m src.server" > /dev/null 2>&1; then
        echo "⚠️  Some processes still running, forcing stop..."
        pkill -9 -f "python -m src.server"
    fi

    echo "✓ Python processes stopped"
    STOPPED_SOMETHING=true
elif pgrep -f "python.*run_stdio.py" > /dev/null 2>&1; then
    echo "Found running STDIO bridge processes"
    echo "Stopping bridge processes..."
    pkill -f "python.*run_stdio.py"
    echo "✓ Bridge processes stopped"
    STOPPED_SOMETHING=true
else
    echo "No running Python processes found"
fi
echo ""

if [ "$STOPPED_SOMETHING" = true ]; then
    echo "✓ Server stopped successfully"
else
    echo "ℹ️  No running server instances found"
fi

echo ""
echo "To start server again:"
echo "  ./scripts/start.sh"
echo "  or: docker-compose up -d"
echo ""
