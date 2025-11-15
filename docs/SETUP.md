# Setup & Installation Guide

Complete guide for installing and configuring the Azure DevOps Sprint MCP Server.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Authentication Setup](#authentication-setup)
- [Running the Server](#running-the-server)
- [Connecting to Claude Desktop](#connecting-to-claude-desktop)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Azure DevOps** organization access
- **Authentication Method** (choose one):
  - Azure CLI with `az login` (recommended)
  - Service Principal credentials
  - Personal Access Token (PAT)

### Optional (for Docker)
- **Docker** ([Get Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** (included with Docker Desktop)

### Windows Users
- **WSL 2** (Windows Subsystem for Linux)
- **Docker Desktop** with WSL integration enabled

---

## Installation

Choose your preferred installation method:

### Option 1: Using pip (Quick Start)

```bash
# Clone repository
git clone https://github.com/yourusername/azure-devops-sprint-mcp.git
cd azure-devops-sprint-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .
```

### Option 2: Using Docker (Recommended for Production)

```bash
# Clone repository
git clone https://github.com/yourusername/azure-devops-sprint-mcp.git
cd azure-devops-sprint-mcp

# Login to Azure (for Managed Identity)
az login

# Start container
docker-compose up -d

# Check health
docker-compose ps
docker-compose logs
```

### Option 3: Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/azure-devops-sprint-mcp.git
cd azure-devops-sprint-mcp

# Run setup script (creates venv, installs deps, configures .env)
./scripts/setup.sh

# Or manually:
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

---

## Authentication Setup

The server supports three authentication methods (tried in order):

### Method 1: Azure Managed Identity (⭐ Recommended)

**Benefits:**
- ✅ Uses your personal Azure credentials
- ✅ No tokens to manage or rotate
- ✅ Automatic token refresh
- ✅ Preserves your user identity in Azure DevOps
- ✅ All operations tracked as YOUR user

**Setup:**

```bash
# 1. Login to Azure CLI
az login

# 2. Verify login
az account show

# 3. Set correct subscription (if needed)
az account set --subscription "Your Subscription Name"

# 4. Configure environment (.env file)
cat > .env <<EOF
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg
AZURE_DEVOPS_PROJECT=YourProject
EOF
```

**That's it!** The server automatically uses your `az login` credentials.

**How it works:**
- Server uses `DefaultAzureCredential` from Azure SDK
- Reads credentials from `~/.azure` directory (created by `az login`)
- Obtains access tokens for Azure DevOps Resource ID
- Tokens refresh automatically 5 minutes before expiry

### Method 2: Service Principal (For Automation)

**Use when:**
- Running in CI/CD pipelines
- Automated scripts without user interaction
- Production deployments without user login

**Setup:**

```bash
# 1. Create Service Principal (one-time)
az ad sp create-for-rbac --name "azure-devops-mcp-sp" --role Contributor

# 2. Add to .env file
cat > .env <<EOF
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg
AZURE_DEVOPS_PROJECT=YourProject

# Service Principal authentication
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
EOF
```

**Required Azure DevOps permissions:**
- Member of Azure DevOps organization
- Read/Write access to work items
- Access to team iterations

### Method 3: Personal Access Token (PAT) (Development Only)

**Use when:**
- Azure CLI not available
- Quick development/testing
- Legacy systems

**Setup:**

```bash
# 1. Create PAT in Azure DevOps
#    Go to: https://dev.azure.com/yourorg/_usersSettings/tokens
#    Scopes needed: Work Items (Read & Write), Project and Team (Read)

# 2. Add to .env file
cat > .env <<EOF
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg
AZURE_DEVOPS_PROJECT=YourProject

# PAT authentication
AZURE_DEVOPS_PAT=your-personal-access-token
EOF
```

⚠️ **Security Note:** Never commit `.env` files with real credentials!

---

## Running the Server

### Using Python Directly

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run server
python -m src.server

# Or use convenience script
./scripts/start.sh
```

**Output:**
```
Starting MCP server with HTTP streaming on port 8000
Server URL: http://localhost:8000/mcp
Health check: Use 'health_check' tool
```

### Using Docker

```bash
# Start server
docker-compose up -d

# View logs
docker-compose logs -f

# Stop server
docker-compose down

# Restart server
docker-compose restart
```

### Using Makefile (Docker)

```bash
make run      # Start containers
make logs     # View logs
make stop     # Stop containers
make restart  # Restart containers
make test     # Run tests
make help     # Show all commands
```

---

## Connecting to Claude Desktop

The server supports two transport modes for Claude Desktop integration:

### Mode 1: STDIO Transport (Recommended for Desktop)

**Perfect for:** Direct Claude Desktop integration on Linux/macOS

**Configuration:**

Edit Claude Desktop config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "python",
      "args": [
        "/path/to/azure-devops-sprint-mcp/scripts/run_stdio.py"
      ],
      "env": {
        "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/yourorg",
        "AZURE_DEVOPS_PROJECT": "YourProject"
      }
    }
  }
}
```

**Important:** Replace `/path/to/` with your actual repository path!

### Mode 2: Docker with STDIO Bridge (Windows + WSL)

**Perfect for:** Windows users with Docker Desktop and WSL

See dedicated guide: [docs/WSL-CLAUDE-DESKTOP.md](WSL-CLAUDE-DESKTOP.md)

**Quick Summary:**

1. Start Docker container in WSL:
   ```bash
   docker-compose up -d
   ```

2. Configure Claude Desktop (Windows) to use bridge script:
   ```json
   {
     "mcpServers": {
       "azure-devops": {
         "command": "C:\\Users\\YourUsername\\azure-devops-mcp\\run_docker_stdio.bat"
       }
     }
   }
   ```

3. Restart Claude Desktop

### Mode 3: HTTP Transport (For API Access)

**Perfect for:** Web applications, multiple clients, API integration

The server automatically runs in HTTP mode when started with Docker:

```bash
docker-compose up -d
# Server available at: http://localhost:8000/mcp
```

**Connect from MCP clients:**
```json
{
  "mcpServers": {
    "azure-devops": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

---

## Verification

### 1. Check Server Health

**Python mode:**
```bash
# Server should be running and show:
# "Transport: STDIO" or "Transport: HTTP"
```

**Docker mode:**
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs | grep -E "(Authenticated|Transport)"

# Should show:
# ✓ Authenticated using: Azure Managed Identity
# ✓ Transport: HTTP
```

### 2. Test Authentication

```bash
# Quick auth test (Python)
python -c "
from src.auth import AzureDevOpsAuth
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
auth = AzureDevOpsAuth(os.getenv('AZURE_DEVOPS_ORG_URL'))
asyncio.run(auth.initialize())
print('✓ Success!')
print('  Method:', auth.get_auth_info()['method'])
print('  Organization:', auth.get_auth_info()['organization_url'])
"
```

**Docker test:**
```bash
docker-compose exec azure-devops-mcp python -c "
from src.auth import AzureDevOpsAuth
import asyncio
import os

auth = AzureDevOpsAuth(os.getenv('AZURE_DEVOPS_ORG_URL'))
asyncio.run(auth.initialize())
info = auth.get_auth_info()
print('✓ Authenticated!')
print(f'  Method: {info[\"method\"]}')
print(f'  Org: {info[\"organization_url\"]}')
"
```

### 3. Test MCP Tools (Claude Desktop)

After connecting to Claude Desktop, try:

> "List my Azure DevOps work items"

> "Show me the current sprint"

> "Get details for work item 12345"

Claude should successfully call the MCP tools and return results.

### 4. Test Health Check Tool

In Claude Desktop:

> "Check the Azure DevOps MCP server health"

Response should show:
```json
{
  "status": "healthy",
  "service": "Azure DevOps Sprint Manager",
  "version": "2.1",
  "authenticated": true,
  "auth_method": "Azure Managed Identity",
  "organization": "https://dev.azure.com/yourorg"
}
```

---

## Troubleshooting

### Authentication Issues

**Problem: "Authentication failed"**

```bash
# 1. Verify Azure login
az account show

# If not logged in:
az login

# 2. Verify .env file
cat .env  # Should have AZURE_DEVOPS_ORG_URL and PROJECT

# 3. Check organization access
az devops project list --org https://dev.azure.com/yourorg

# 4. Restart server to pick up new credentials
# Python: Ctrl+C and restart
# Docker: docker-compose restart
```

**Problem: "Permission denied" or 403 errors**

Your authentication method needs these Azure DevOps permissions:
- Work Items: Read & Write
- Project and Team: Read
- Analytics: Read (optional, for advanced queries)

**Fix:**
1. For PAT: Update token scopes in Azure DevOps settings
2. For Service Principal: Add to Azure DevOps organization with correct permissions
3. For Managed Identity: Verify your Azure account has access to the organization

### Connection Issues

**Problem: "Server not connecting" (STDIO mode)**

```bash
# Test the server manually
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python ./scripts/run_stdio.py

# Should return JSON-RPC initialize response
```

**Problem: "Module not found"**

```bash
# Ensure dependencies installed
pip install -r requirements.txt

# Or reinstall package
pip install -e .
```

### Docker Issues

**Problem: "Container won't start"**

```bash
# Check logs
docker-compose logs

# Validate configuration
docker-compose config

# Check environment
docker-compose exec azure-devops-mcp env

# Common fix: Rebuild container
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Problem: "Port already in use"**

```bash
# Check what's using port 8000
lsof -i :8000

# Change port in docker-compose.yml:
ports:
  - "8080:8000"  # Use 8080 instead of 8000
```

**Problem: "Azure credentials not found in container"**

```bash
# Verify .azure directory is mounted
docker-compose exec azure-devops-mcp ls -la /home/mcpuser/.azure

# Should show config files from az login

# If empty, ensure Docker has access to your home directory
# Windows: Check Docker Desktop Settings > Resources > File Sharing
# Linux/macOS: Should work automatically
```

### Windows-Specific Issues

See comprehensive Windows troubleshooting: [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md#windows-wsl-issues)

**Quick fixes:**
- Ensure Docker Desktop is running
- Enable WSL integration in Docker Desktop settings
- Run Docker commands in WSL, not Windows terminal
- Copy bridge scripts to Windows filesystem (`/mnt/c/Users/...`)

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_DEVOPS_ORG_URL` | ✅ Yes | None | Azure DevOps organization URL |
| `AZURE_DEVOPS_PROJECT` | Recommended | None | Default project name (can override per-tool call) |
| `AZURE_DEVOPS_PAT` | No | None | Personal Access Token (if not using Managed Identity) |
| `AZURE_CLIENT_ID` | No | None | Service Principal client ID |
| `AZURE_CLIENT_SECRET` | No | None | Service Principal secret |
| `AZURE_TENANT_ID` | No | None | Azure AD tenant ID |
| `MCP_TRANSPORT` | No | `http` | Transport mode: `stdio` or `http` |
| `PORT` | No | `8000` | HTTP server port (HTTP mode only) |

---

## Next Steps

- **Usage Guide:** See [docs/USAGE.md](USAGE.md) for tool reference and examples
- **Docker Guide:** See [docs/DOCKER.md](DOCKER.md) for advanced Docker deployment
- **Windows/WSL Guide:** See [docs/WSL-CLAUDE-DESKTOP.md](WSL-CLAUDE-DESKTOP.md) for Windows setup
- **Troubleshooting:** See [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues
- **Development:** See [docs/DEVELOPMENT.md](DEVELOPMENT.md) for contributing

---

**Authentication Priority:**
1. **Azure Managed Identity** (DefaultAzureCredential) ⭐ Recommended
2. Service Principal (if `AZURE_CLIENT_ID` set)
3. Personal Access Token (if `AZURE_DEVOPS_PAT` set)

**All operations are tracked in Azure DevOps as YOUR user!**
