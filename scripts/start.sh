#!/bin/bash
set -e  # Exit on error

echo "=========================================="
echo "Azure DevOps Sprint MCP Server - Start"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "   Run ./scripts/setup.sh first"
    exit 1
fi

# Ask user which mode to start
echo "Select startup mode:"
echo "  1) Docker (recommended for production)"
echo "  2) Python (direct, for development)"
echo "  3) Auto-detect"
echo ""
read -p "Choice [1-3]: " -n 1 -r MODE
echo ""
echo ""

start_docker() {
    echo "Starting with Docker..."
    echo ""

    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        echo "❌ Error: Docker not found"
        echo "   Install Docker from: https://docker.com"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo "❌ Error: Docker is not running"
        echo "   Start Docker Desktop and try again"
        exit 1
    fi

    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        echo "❌ Error: docker-compose.yml not found"
        exit 1
    fi

    # Start containers
    echo "Starting Docker containers..."
    docker-compose up -d

    echo ""
    echo "✓ Docker containers started"
    echo ""

    # Wait a moment for container to start
    sleep 2

    # Check container status
    echo "Container status:"
    docker-compose ps

    echo ""
    echo "View logs:"
    echo "  docker-compose logs -f"
    echo ""
    echo "Stop server:"
    echo "  ./scripts/stop.sh"
    echo "  or: docker-compose down"
    echo ""
    echo "Server URL: http://localhost:8000/mcp"
    echo ""
}

start_python() {
    echo "Starting with Python..."
    echo ""

    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "❌ Error: Virtual environment not found"
        echo "   Run ./scripts/setup.sh first"
        exit 1
    fi

    # Activate virtual environment
    echo "Activating virtual environment..."
    source venv/bin/activate

    # Check if package is installed
    if ! python -c "import src.server" 2>/dev/null; then
        echo "❌ Error: Package not installed"
        echo "   Run ./scripts/setup.sh first"
        exit 1
    fi

    # Check Azure authentication
    echo "Checking Azure authentication..."
    if command -v az &> /dev/null && az account show &> /dev/null; then
        ACCOUNT=$(az account show --query name -o tsv)
        echo "✓ Using Azure account: $ACCOUNT"
    else
        echo "⚠️  Not logged into Azure (will try PAT or Service Principal)"
    fi
    echo ""

    # Start server
    echo "Starting MCP server..."
    echo "Press Ctrl+C to stop"
    echo ""
    echo "=========================================="
    echo ""

    python -m src.server
}

# Execute based on choice
case $MODE in
    1)
        start_docker
        ;;
    2)
        start_python
        ;;
    3)
        # Auto-detect: prefer Docker if available
        if command -v docker &> /dev/null && docker info &> /dev/null 2>&1 && [ -f "docker-compose.yml" ]; then
            echo "Auto-detected: Docker is available"
            start_docker
        elif [ -d "venv" ]; then
            echo "Auto-detected: Python virtual environment"
            start_python
        else
            echo "❌ Error: Could not auto-detect startup mode"
            echo "   Run ./scripts/setup.sh first"
            exit 1
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac
