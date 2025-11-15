# Docker Deployment Guide

Complete guide for deploying Azure DevOps Sprint MCP Server using Docker.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Docker Compose](#docker-compose)
- [Transport Modes](#transport-modes)
- [Environment Variables](#environment-variables)
- [Health Checks](#health-checks)
- [Production Deployment](#production-deployment)
- [Azure Container Registry (ACR)](#azure-container-registry-acr)
- [Azure Container Instances (ACI)](#azure-container-instances-aci)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

```bash
# Install Docker
# - macOS: Docker Desktop
# - Linux: Docker Engine
# - Windows: Docker Desktop or WSL2 + Docker

# Verify installation
docker --version
docker-compose --version
```

### 1-Minute Setup

```bash
# Clone repository
git clone https://github.com/yourusername/azure-devops-sprint-mcp.git
cd azure-devops-sprint-mcp

# Login to Azure (uses your personal credentials)
az login

# Create .env file (no credentials needed!)
cat > .env <<EOF
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg
AZURE_DEVOPS_PROJECT=YourProject
EOF

# Start with docker-compose
docker-compose up -d

# Check health
docker logs azure-devops-mcp

# Test connection
curl http://localhost:8000/mcp
```

---

## Docker Compose

### Standard Configuration

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  azure-devops-mcp:
    image: azure-devops-sprint-mcp:latest
    container_name: azure-devops-mcp
    ports:
      - "8000:8000"
    volumes:
      - ~/.azure:/root/.azure:ro  # Azure credentials (read-only)
      - ./logs:/app/logs          # Logs persistence
      - ./cache:/app/cache        # Cache persistence
    env_file:
      - .env
    environment:
      - PORT=8000
      - MCP_TRANSPORT=http        # Default: HTTP mode
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
```

### Build and Run

```bash
# Build image
docker-compose build

# Run in foreground (with logs)
docker-compose up

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop and remove
docker-compose down

# Restart
docker-compose restart
```

---

## Transport Modes

The server supports **two transport modes** configurable via the `MCP_TRANSPORT` environment variable.

### HTTP Transport (Default)

**Use for:**
- Web-based MCP clients
- API testing (curl, Postman)
- Integration with web services
- Multi-client access

**Configuration:**
```yaml
environment:
  - MCP_TRANSPORT=http  # Default
  - PORT=8000
```

**Access:**
```bash
# From host
curl http://localhost:8000/mcp

# From WSL to Windows (get WSL IP first)
hostname -I | awk '{print $1}'
curl http://<WSL_IP>:8000/mcp
```

**Test:**
```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

---

### STDIO Transport (Claude Desktop)

**Use for:**
- Claude Desktop (Windows) direct connection
- Command-line MCP clients
- Single-client stdio applications

#### Option A: Run Container in STDIO Mode

```yaml
environment:
  - MCP_TRANSPORT=stdio  # Switch to stdio
```

Restart container:
```bash
docker-compose restart
```

**Note:** In this mode, HTTP endpoint is **NOT** available.

#### Option B: Docker Exec Bridge (Recommended)

Keep container in HTTP mode, but connect via stdio using `docker exec`.

**Advantages:**
- HTTP endpoint remains available
- Multiple clients can connect
- No container restart needed

**Setup for Claude Desktop (Windows):**

1. **Create bridge script** (`run_docker_stdio.bat`):
```batch
@echo off
docker exec -i -e MCP_TRANSPORT=stdio azure-devops-mcp python -m src.server
```

2. **Configure Claude Desktop** (`%APPDATA%\Claude\claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "C:\\Users\\<YourUsername>\\azure-devops-mcp\\run_docker_stdio.bat"
    }
  }
}
```

3. **Restart Claude Desktop**

**How it works:**
- Container runs in HTTP mode (default)
- `docker exec` creates new process in stdio mode
- Claude Desktop connects via stdio
- Both transports work simultaneously!

---

## Environment Variables

### Required Variables

```bash
# Organization URL
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg

# Default project (recommended)
AZURE_DEVOPS_PROJECT=MyProject
```

### Authentication Variables

Choose **ONE** authentication method:

#### Method 1: Managed Identity (Recommended)

Uses your personal Azure credentials from `az login`.

**Advantages:**
- Preserves user identity (audit logs show your name)
- No credential storage needed
- Automatic token refresh
- Most secure

**Setup:**
```bash
# Login on host
az login

# Docker mounts ~/.azure directory (read-only)
# No environment variables needed!
```

**docker-compose.yml:**
```yaml
volumes:
  - ~/.azure:/root/.azure:ro  # Mounted automatically
```

#### Method 2: Service Principal (Automation)

For CI/CD pipelines and automation.

```bash
# Add to .env
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
```

#### Method 3: Personal Access Token (Development)

Quick testing and local development.

```bash
# Add to .env
AZURE_DEVOPS_PAT=your_personal_access_token
```

**Security Warning:** Never commit PATs to version control!

### Optional Variables

```bash
# Server configuration
PORT=8000                      # HTTP server port
MCP_TRANSPORT=http             # Transport mode (http or stdio)
LOG_LEVEL=INFO                 # Logging level
DEBUG=0                        # Debug mode (0 or 1)
PYTHONUNBUFFERED=1             # Unbuffered output
```

### Using .env File

**For personal use (with az login):**
```bash
cat > .env <<EOF
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg
AZURE_DEVOPS_PROJECT=YourProject
PORT=8000
LOG_LEVEL=INFO
EOF

# Login to Azure
az login

# Use with docker-compose (mounts ~/.azure automatically)
docker-compose up -d
```

**For automation (with service credentials):**
```bash
cat > .env <<EOF
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg
AZURE_DEVOPS_PROJECT=YourProject
AZURE_CLIENT_ID=your_client_id
AZURE_CLIENT_SECRET=your_client_secret
AZURE_TENANT_ID=your_tenant_id
PORT=8000
LOG_LEVEL=INFO
EOF
```

---

## Health Checks

### Docker Health Check

Built-in health check in `docker-compose.yml`:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

**Check health status:**
```bash
docker inspect azure-devops-mcp --format='{{.State.Health.Status}}'
```

### Application Health Check

Use the `health_check` MCP tool:

```bash
# Via HTTP
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"health_check","arguments":{}}}'
```

**Response:**
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

## Production Deployment

### Best Practices

1. **Use Managed Identity** (most secure)
2. **Set resource limits** (CPU, memory)
3. **Enable health checks**
4. **Use restart policies**
5. **Persist logs and cache**
6. **Monitor with Azure Monitor**

### Production docker-compose.yml

```yaml
version: '3.8'

services:
  azure-devops-mcp:
    image: yourregistry.azurecr.io/azure-devops-sprint-mcp:2.1
    container_name: azure-devops-mcp
    ports:
      - "8000:8000"
    volumes:
      - ~/.azure:/root/.azure:ro
      - /var/log/azure-devops-mcp:/app/logs
      - /var/cache/azure-devops-mcp:/app/cache
    env_file:
      - .env
    environment:
      - PORT=8000
      - MCP_TRANSPORT=http
      - LOG_LEVEL=INFO
    restart: always
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '2.0'
        reservations:
          memory: 512M
          cpus: '1.0'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Azure Container Registry (ACR)

### Setup ACR

```bash
# Variables
RESOURCE_GROUP="rg-azure-devops-mcp"
ACR_NAME="acrazuredevopsmcp"  # Must be globally unique
LOCATION="eastus"

# Create resource group
az group create \
  --name $RESOURCE_GROUP \
  --location $LOCATION

# Create ACR
az acr create \
  --resource-group $RESOURCE_GROUP \
  --name $ACR_NAME \
  --sku Basic \
  --location $LOCATION

# Login to ACR
az acr login --name $ACR_NAME
```

### Push Image to ACR

```bash
# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)

# Tag image
docker tag azure-devops-sprint-mcp:latest \
  $ACR_LOGIN_SERVER/azure-devops-sprint-mcp:latest

docker tag azure-devops-sprint-mcp:latest \
  $ACR_LOGIN_SERVER/azure-devops-sprint-mcp:2.1

# Push to ACR
docker push $ACR_LOGIN_SERVER/azure-devops-sprint-mcp:latest
docker push $ACR_LOGIN_SERVER/azure-devops-sprint-mcp:2.1

# List images
az acr repository list --name $ACR_NAME -o table
```

### Build in ACR (Cloud Build)

```bash
# Build image in Azure (no local Docker needed!)
az acr build \
  --registry $ACR_NAME \
  --image azure-devops-sprint-mcp:latest \
  --image azure-devops-sprint-mcp:2.1 \
  --file Dockerfile \
  .
```

---

## Azure Container Instances (ACI)

### Deploy to ACI

```bash
# Variables
ACI_NAME="aci-azure-devops-mcp"
ACR_LOGIN_SERVER=$(az acr show --name $ACR_NAME --query loginServer -o tsv)

# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query passwords[0].value -o tsv)

# Create container instance
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $ACI_NAME \
  --image $ACR_LOGIN_SERVER/azure-devops-sprint-mcp:latest \
  --cpu 1 \
  --memory 0.5 \
  --registry-login-server $ACR_LOGIN_SERVER \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --environment-variables \
    AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg \
    AZURE_DEVOPS_PROJECT=YourProject \
  --ports 8000 \
  --dns-name-label azure-devops-mcp-unique \
  --restart-policy Always

# View container details
az container show \
  --resource-group $RESOURCE_GROUP \
  --name $ACI_NAME

# View logs
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name $ACI_NAME \
  --follow
```

### Deploy with Managed Identity

```bash
# Create user-assigned managed identity
IDENTITY_NAME="id-azure-devops-mcp"

az identity create \
  --resource-group $RESOURCE_GROUP \
  --name $IDENTITY_NAME

# Get identity details
IDENTITY_ID=$(az identity show \
  --resource-group $RESOURCE_GROUP \
  --name $IDENTITY_NAME \
  --query id -o tsv)

# Create ACI with managed identity
az container create \
  --resource-group $RESOURCE_GROUP \
  --name $ACI_NAME \
  --image $ACR_LOGIN_SERVER/azure-devops-sprint-mcp:latest \
  --assign-identity $IDENTITY_ID \
  --acr-identity $IDENTITY_ID \
  --environment-variables \
    AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg \
    AZURE_DEVOPS_PROJECT=YourProject \
  --ports 8000 \
  --restart-policy Always
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs azure-devops-mcp

# Common issues:
# 1. Missing environment variables
docker-compose config  # Validate config

# 2. Port already in use
lsof -i :8000  # Check what's using port
docker-compose down  # Stop containers

# 3. Permission issues
ls -la logs/ cache/  # Check permissions
sudo chown -R $USER:$USER logs/ cache/
```

### Authentication Failures

```bash
# Test auth inside container
docker-compose exec azure-devops-mcp python -c "
from src.auth import AzureDevOpsAuth
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
auth = AzureDevOpsAuth(os.getenv('AZURE_DEVOPS_ORG_URL'))
asyncio.run(auth.initialize())
print('Auth successful:', auth.get_auth_info()['method'])
"

# Check Azure credentials mounted
docker exec azure-devops-mcp ls -la /root/.azure

# Re-login on host
az login
docker-compose restart
```

### Network Issues

```bash
# Test connectivity from container
docker-compose exec azure-devops-mcp ping dev.azure.com

# Check DNS
docker-compose exec azure-devops-mcp nslookup dev.azure.com

# Test Azure DevOps API
docker-compose exec azure-devops-mcp curl -v https://dev.azure.com/yourorg
```

### Memory/CPU Issues

```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 1G
```

### Windows/WSL Issues

**Problem:** Container runs in WSL, Claude Desktop runs on Windows

**Solution:** Use `docker exec` bridge (see [Transport Modes](#transport-modes))

**Problem:** Docker command not found (Windows)

**Solution:**
1. Verify Docker Desktop is installed and running
2. Check Docker is in PATH:
   ```powershell
   docker --version
   ```
3. Use full path if needed:
   ```
   C:\Program Files\Docker\Docker\resources\bin\docker.exe
   ```

**Problem:** Permission denied

**Solution:**
1. Open Docker Desktop
2. Settings → Resources → WSL Integration
3. Enable integration for your WSL distro

---

## Monitoring & Logging

### View Logs

```bash
# Docker Compose
docker-compose logs -f

# Docker
docker logs -f azure-devops-mcp

# ACI
az container logs \
  --resource-group $RESOURCE_GROUP \
  --name $ACI_NAME \
  --follow
```

### Log Rotation

Configure log rotation in `docker-compose.yml`:

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Performance Monitoring

Use the `get_service_statistics` MCP tool:

```python
stats = await get_service_statistics()
print(f"Cache hit rate: {stats['service_manager']['cache_hit_rate_percent']}%")
print(f"Loaded projects: {stats['loaded_projects']}")
```

---

## Quick Reference

### Common Commands

```bash
# Build and start
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop and remove
docker-compose down

# Check health
docker inspect azure-devops-mcp --format='{{.State.Health.Status}}'

# Shell access
docker-compose exec azure-devops-mcp /bin/bash

# Run tests
docker-compose exec azure-devops-mcp pytest
```

### Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AZURE_DEVOPS_ORG_URL` | ✅ Yes | - | Organization URL |
| `AZURE_DEVOPS_PROJECT` | Recommended | - | Default project name |
| `AZURE_DEVOPS_PAT` | Auth Option | - | Personal Access Token |
| `AZURE_CLIENT_ID` | Auth Option | - | Service Principal ID |
| `AZURE_CLIENT_SECRET` | Auth Option | - | Service Principal Secret |
| `AZURE_TENANT_ID` | Auth Option | - | Azure AD Tenant ID |
| `PORT` | No | 8000 | HTTP server port |
| `MCP_TRANSPORT` | No | http | Transport mode (http/stdio) |
| `LOG_LEVEL` | No | INFO | Logging level |

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        WINDOWS                               │
│  ┌──────────────────┐          ┌───────────────────────┐   │
│  │ Claude Desktop   │          │  Web Browser / curl   │   │
│  └────────┬─────────┘          └─────────────┬─────────┘   │
│           │ stdio                             │ HTTP        │
│  ┌────────▼─────────────────────────────────────────┐      │
│  │     run_docker_stdio.bat (Bridge)                │      │
│  │     docker exec -i azure-devops-mcp...           │      │
│  └────────┬─────────────────────────────────────────┘      │
└───────────┼──────────────────────────────────────────────────┘
            │                    WSL Network
┌───────────▼──────────────────────────────────────────────────┐
│                         WSL (Linux)                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Docker Container: azure-devops-mcp                     │ │
│  │                                                          │ │
│  │  • HTTP mode: Port 8000 exposed                        │ │
│  │  • STDIO mode: Via docker exec                         │ │
│  │  • Volumes: ~/.azure (user credentials)                │ │
│  │  • Auto-restart on failure                             │ │
│  └────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────┘
```

---

## Additional Resources

- [USAGE.md](./USAGE.md) - MCP tools usage guide
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Detailed troubleshooting
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Development guide
- [Docker Documentation](https://docs.docker.com/)
- [Azure Container Registry](https://docs.microsoft.com/azure/container-registry/)
- [Azure Container Instances](https://docs.microsoft.com/azure/container-instances/)

---

**Version:** 2.1
**Last Updated:** 2025-11-15
