#!/bin/bash
set -e  # Exit on error

echo "=========================================="
echo "Azure DevOps Sprint MCP Server Setup"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 is not installed"
    echo "   Please install Python 3.10 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Error: Python $PYTHON_VERSION is installed, but $REQUIRED_VERSION or higher is required"
    exit 1
fi

echo "✓ Python $PYTHON_VERSION found"
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
    read -p "Recreate it? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing old virtual environment..."
        rm -rf venv
    fi
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null

# Install package
echo "Installing Azure DevOps Sprint MCP Server..."
pip install -e . > /dev/null
echo "✓ Package installed"
echo ""

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ .env file created"
        echo ""
        echo "⚠️  Please edit .env file and configure:"
        echo "   - AZURE_DEVOPS_ORG_URL (required)"
        echo "   - AZURE_DEVOPS_PROJECT (recommended)"
        echo ""
    else
        echo "⚠️  .env.example not found, creating basic .env..."
        cat > .env <<EOF
# Azure DevOps Configuration
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg
AZURE_DEVOPS_PROJECT=YourProject

# Authentication (choose one - Managed Identity recommended)
# AZURE_DEVOPS_PAT=your-pat-token
# AZURE_CLIENT_ID=your-client-id
# AZURE_CLIENT_SECRET=your-client-secret
# AZURE_TENANT_ID=your-tenant-id

# Server Configuration
MCP_TRANSPORT=http
PORT=8000
EOF
        echo "✓ Basic .env file created"
        echo ""
        echo "⚠️  Please edit .env file and configure your Azure DevOps settings"
        echo ""
    fi
else
    echo "✓ .env file already exists"
    echo ""
fi

# Check Azure CLI
echo "Checking Azure CLI..."
if command -v az &> /dev/null; then
    echo "✓ Azure CLI found"

    # Check if logged in
    if az account show &> /dev/null; then
        ACCOUNT=$(az account show --query name -o tsv)
        echo "✓ Logged into Azure: $ACCOUNT"
    else
        echo "⚠️  Not logged into Azure"
        echo "   Run: az login"
    fi
else
    echo "⚠️  Azure CLI not found (optional)"
    echo "   Install from: https://docs.microsoft.com/cli/azure/install-azure-cli"
    echo "   Or use PAT/Service Principal authentication"
fi
echo ""

# Run basic tests
echo "Running basic tests..."
if python -c "from src.server import mcp; print('✓ Server imports successfully')" 2>/dev/null; then
    echo "✓ Server package is working"
else
    echo "⚠️  Server import test failed"
fi
echo ""

# Check Docker
echo "Checking Docker (optional)..."
if command -v docker &> /dev/null; then
    echo "✓ Docker found"
    if docker info &> /dev/null; then
        echo "✓ Docker is running"
    else
        echo "⚠️  Docker is installed but not running"
    fi
else
    echo "⚠️  Docker not found (optional for Python mode)"
fi
echo ""

echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. Edit .env file with your Azure DevOps settings:"
echo "   nano .env"
echo ""
echo "2. Login to Azure (for Managed Identity auth):"
echo "   az login"
echo ""
echo "3. Start the server:"
echo "   ./scripts/start.sh"
echo ""
echo "Or use Docker:"
echo "   docker-compose up -d"
echo ""
echo "For Claude Desktop integration, see:"
echo "   docs/SETUP.md"
echo ""
