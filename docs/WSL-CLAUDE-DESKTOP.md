# Windows + WSL + Claude Desktop Setup Guide

> **Complete guide for Windows users to connect Claude Desktop to the MCP server running in Docker (WSL)**

## Quick Summary

If you're on Windows and want to use this MCP server with Claude Desktop:

1. **In WSL (Ubuntu)**: Clone repo → Create `.env` → Run `az login` → Start Docker container
2. **Copy bridge script** from WSL to Windows user directory
3. **Configure Claude Desktop** on Windows to use the bridge script
4. **Restart Claude Desktop** - Done!

Total setup time: ~10 minutes

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Understanding the Bridge](#understanding-the-bridge)
- [Setup Instructions](#setup-instructions)
- [Configuration Options](#configuration-options)
- [How It Works](#how-it-works)
- [Troubleshooting](#troubleshooting)

---

## Overview

**The Challenge:** Claude Desktop runs on Windows, but the Docker container runs in WSL. They can't directly communicate via STDIO.

**The Solution:** Use a bridge script that forwards STDIO messages between Claude Desktop (Windows) and the Docker container (WSL).

```
Windows (Claude Desktop)
    ↓ STDIO
Bridge Script (run_docker_stdio.py or .bat)
    ↓ docker exec
Docker Container (WSL)
    ↓ MCP Protocol
Azure DevOps Sprint MCP Server
    ↓ Azure API
Azure DevOps
```

---

## Prerequisites

### 1. Windows Components

- **Windows 10/11** with WSL 2 installed
- **Docker Desktop for Windows** with WSL integration enabled
- **Python 3.8+** installed on Windows (for Python bridge option)
- **Claude Desktop** installed on Windows

### 2. WSL Components

- **WSL 2** distribution (Ubuntu recommended)
- **Azure CLI** installed in WSL
- **Docker** accessible from WSL (via Docker Desktop integration)

### 3. Verify Prerequisites

```powershell
# In PowerShell (Windows)
wsl --status          # Should show WSL 2
docker --version      # Should show Docker version
python --version      # Should show Python 3.8+

# In WSL (Ubuntu)
az --version          # Should show Azure CLI
docker ps             # Should connect to Docker Desktop
```

---

## Understanding the Bridge

There are **two bridge implementations** - both do the same thing:

### Option A: Python Bridge (run_docker_stdio.py)

**Features:**
- Cross-platform (works on Windows and Linux)
- Better error handling and logging
- Forwards stderr for debugging
- Uses threading for non-blocking I/O
- 150 lines of well-tested code

**How it works:**
1. Accepts STDIO input from Claude Desktop
2. Spawns `docker exec -i azure-devops-mcp python -m src.server`
3. Creates 3 threads: stdin forward, stdout forward, stderr forward
4. Pipes messages between Claude Desktop ↔ Docker container

### Option B: Batch Bridge (run_docker_stdio.bat)

**Features:**
- Simple Windows batch file
- No Python dependency
- Direct docker exec call
- Minimal overhead
- 28 lines of batch commands

**How it works:**
1. Checks if Docker is running
2. Verifies container exists
3. Directly executes `docker exec -i azure-devops-mcp python -m src.server`
4. Forwards STDIO using Windows pipes

**Which to use?**
- **Python bridge** - More reliable, better error messages, recommended
- **Batch bridge** - Simpler, no Python needed on Windows

---

## Setup Instructions

### Step 1: Clone and Configure (WSL)

```bash
# Open WSL terminal (Ubuntu)
cd ~  # or your preferred directory

# Clone repository
git clone https://github.com/yourusername/azure-devops-sprint-mcp.git
cd azure-devops-sprint-mcp

# Create .env file from template
cp .env.example .env

# Edit .env with your settings (REQUIRED!)
nano .env  # Use nano, vim, or any editor

# The .env file must have:
# AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-organization
# AZURE_DEVOPS_PROJECT=YourProject
```

### Step 2: Authenticate and Start Docker (WSL)

```bash
# Login to Azure (required for Managed Identity auth)
az login
az account show  # Verify you're logged in

# Start Docker container
docker-compose up -d

# Verify container is running and healthy
docker ps | grep azure-devops-mcp
# Should show: azure-devops-mcp (Up X minutes) (healthy)

# Check logs for successful authentication
docker-compose logs
# Should see: "✓ Authenticated using: Azure Managed Identity / DefaultAzureCredential"
```

### Step 3: Copy Bridge Scripts to Windows

The bridge scripts need to be accessible from Windows (not WSL filesystem).

**Option 1: Manual Copy**

1. In WSL, run:
   ```bash
   # Copy both bridge scripts to Windows user directory
   cp scripts/run_docker_stdio.py /mnt/c/Users/<YourUsername>/azure-devops-mcp/
   cp scripts/run_docker_stdio.bat /mnt/c/Users/<YourUsername>/azure-devops-mcp/
   ```

2. Verify in Windows Explorer:
   - Navigate to `C:\Users\<YourUsername>\azure-devops-mcp\`
   - Should see: `run_docker_stdio.py` and `run_docker_stdio.bat`

**Option 2: Using Windows Path**

```bash
# In WSL
mkdir -p /mnt/c/Users/$USER/azure-devops-mcp
cp scripts/run_docker_stdio.* /mnt/c/Users/$USER/azure-devops-mcp/
```

### Step 4: Configure Claude Desktop (Windows)

**Using Batch Bridge (Simplest):**

1. Open: `%APPDATA%\Claude\claude_desktop_config.json`
   - Press `Win+R`, type: `%APPDATA%\Claude`
   - Open `claude_desktop_config.json` in Notepad

2. Add this configuration:
   ```json
   {
     "mcpServers": {
       "azure-devops": {
         "command": "C:\\Users\\<YourUsername>\\azure-devops-mcp\\run_docker_stdio.bat"
       }
     }
   }
   ```

3. Replace `<YourUsername>` with your actual Windows username

**Using Python Bridge (Recommended):**

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "python",
      "args": [
        "C:\\Users\\<YourUsername>\\azure-devops-mcp\\run_docker_stdio.py"
      ]
    }
  }
}
```

**Important:**
- Use double backslashes (`\\`) in Windows paths
- Replace `<YourUsername>` with your actual username
- Ensure the path exists and is accessible

### Step 4: Restart Claude Desktop

1. **Completely quit** Claude Desktop (right-click system tray → Quit)
2. Wait 5 seconds
3. **Restart** Claude Desktop
4. The Azure DevOps MCP server should now appear in the tools list

### Step 5: Verify Connection

In Claude Desktop, try:

> "Check the Azure DevOps MCP server health"

Expected response:
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

Then try:

> "List my Azure DevOps work items"

Should return your assigned work items from Azure DevOps.

---

## Configuration Options

### Environment Variables

Bridge scripts can pass environment variables to the container:

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "python",
      "args": ["C:\\Users\\<YourUsername>\\azure-devops-mcp\\run_docker_stdio.py"],
      "env": {
        "AZURE_DEVOPS_PROJECT": "MyProject",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

**Note:** These override the .env file in the container.

### Multiple Projects

To work with multiple projects, create multiple server configurations:

```json
{
  "mcpServers": {
    "azure-devops-project1": {
      "command": "python",
      "args": ["C:\\Users\\<YourUsername>\\azure-devops-mcp\\run_docker_stdio.py"],
      "env": {
        "AZURE_DEVOPS_PROJECT": "Project1"
      }
    },
    "azure-devops-project2": {
      "command": "python",
      "args": ["C:\\Users\\<YourUsername>\\azure-devops-mcp\\run_docker_stdio.py"],
      "env": {
        "AZURE_DEVOPS_PROJECT": "Project2"
      }
    }
  }
}
```

Or use the multi-project feature (v2.1+) with a single server:

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "python",
      "args": ["C:\\Users\\<YourUsername>\\azure-devops-mcp\\run_docker_stdio.py"]
    }
  }
}
```

Then specify project in Claude requests:

> "List my work items in Project1"

> "Show current sprint for Project2"

---

## How It Works

### Communication Flow

1. **User Query in Claude Desktop (Windows)**
   - User: "List my work items"
   - Claude Desktop sends MCP request via STDIO

2. **Bridge Script Receives Request**
   - Python script: `stdin.read()` receives JSON-RPC message
   - Batch script: Windows pipes receive message

3. **Forward to Docker Container (WSL)**
   - Executes: `docker exec -i azure-devops-mcp python -m src.server`
   - Pipes message to container's stdin

4. **MCP Server Processes Request**
   - Server receives JSON-RPC in container
   - Calls `get_my_work_items` tool
   - Authenticates with Azure using mounted credentials
   - Queries Azure DevOps API

5. **Response Back to Claude**
   - Server sends JSON-RPC response to stdout
   - Bridge forwards to Claude Desktop via stdout
   - Claude Desktop receives and displays result

### Technical Details

**Docker exec command:**
```bash
docker exec -i \
  -e MCP_TRANSPORT=stdio \
  azure-devops-mcp \
  python -m src.server
```

**Flags:**
- `-i` - Keep stdin open for interactive communication
- `-e MCP_TRANSPORT=stdio` - Override transport mode to STDIO
- `azure-devops-mcp` - Container name
- `python -m src.server` - MCP server entry point

**Why this works:**
- Docker Desktop shares the Docker daemon between Windows and WSL
- `docker exec` from Windows can access WSL containers
- STDIO pipes work across the Windows/WSL boundary

---

## Troubleshooting

### Common Issues

#### 1. "Server not connecting"

**Symptoms:** Claude Desktop shows Azure DevOps server as unavailable

**Fixes:**

```bash
# In WSL - Check container is running
docker ps | grep azure-devops-mcp

# If not running:
cd /path/to/azure-devops-sprint-mcp
docker-compose up -d

# Check container logs
docker logs azure-devops-mcp

# Test docker exec works
docker exec azure-devops-mcp echo "test"
# Should print: test
```

#### 2. "Docker command not found"

**Symptoms:** Bridge script can't find docker command

**Fixes:**

```powershell
# In PowerShell (Windows) - Verify Docker Desktop is running
docker --version

# If not installed:
# Download Docker Desktop from https://docker.com

# If installed but not running:
# Start Docker Desktop from Start menu
```

#### 3. "Container 'azure-devops-mcp' not found"

**Symptoms:** Bridge script reports container doesn't exist

**Fixes:**

```bash
# In WSL - Check container name
docker ps -a

# Should show container named: azure-devops-mcp

# If different name, edit bridge script or restart with correct name
docker-compose down
docker-compose up -d
```

#### 4. "Authentication failed"

**Symptoms:** Server connects but can't authenticate with Azure DevOps

**Fixes:**

```bash
# In WSL - Verify Azure login
az account show

# If not logged in:
az login

# Restart container to pick up new credentials
docker-compose restart

# Verify .azure directory is mounted
docker exec azure-devops-mcp ls -la /home/mcpuser/.azure
# Should show config files
```

#### 5. "Permission denied" errors

**Symptoms:** Docker commands fail with permission errors

**Fixes:**

1. **Check Docker Desktop WSL Integration:**
   - Open Docker Desktop
   - Settings → Resources → WSL Integration
   - Enable integration for your WSL distribution (Ubuntu)
   - Click "Apply & Restart"

2. **Verify Docker group membership (WSL):**
   ```bash
   # Add user to docker group
   sudo usermod -aG docker $USER

   # Logout and login to WSL
   exit
   # Then reopen WSL terminal
   ```

#### 6. "Python not found" (Python bridge)

**Symptoms:** Command 'python' is not recognized

**Fixes:**

```powershell
# In PowerShell - Check Python installation
python --version

# If not installed:
# Download from https://python.org

# If installed but not in PATH, use full path:
```

Update Claude config:
```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "C:\\Python311\\python.exe",
      "args": ["C:\\Users\\...\\run_docker_stdio.py"]
    }
  }
}
```

#### 7. "WSL IP address changed"

**Note:** This approach does NOT depend on WSL IP addresses!

The bridge uses `docker exec` which works regardless of WSL networking.
If you see IP-related errors, you're likely using an old HTTP-based approach.

**Fix:** Use the STDIO bridge (this guide), not HTTP tunnel.

### Testing the Bridge

**Test bridge script manually (Windows PowerShell):**

```powershell
# Navigate to bridge script directory
cd C:\Users\<YourUsername>\azure-devops-mcp

# Test Python bridge
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python run_docker_stdio.py

# Test batch bridge
echo {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}} | run_docker_stdio.bat
```

**Expected output:** JSON-RPC response with server capabilities

### Debug Logging

**Enable debug logging in Python bridge:**

Edit `run_docker_stdio.py` and add:

```python
import logging
logging.basicConfig(level=logging.DEBUG, filename='C:\\Users\\<YourUsername>\\bridge-debug.log')
```

Then check `C:\Users\<YourUsername>\bridge-debug.log` for detailed logs.

---

## Advanced Configuration

### Using Different Container Names

If your container has a different name:

1. Edit `run_docker_stdio.py`, change:
   ```python
   container_name = "azure-devops-mcp"  # Change this
   ```

2. Or edit `run_docker_stdio.bat`, change:
   ```batch
   set CONTAINER_NAME=azure-devops-mcp  REM Change this
   ```

### Custom Docker Socket

If using a non-standard Docker socket:

```powershell
# Set environment variable in Claude config
{
  "mcpServers": {
    "azure-devops": {
      "command": "python",
      "args": ["C:\\Users\\...\\run_docker_stdio.py"],
      "env": {
        "DOCKER_HOST": "tcp://localhost:2375"
      }
    }
  }
}
```

### Running Multiple MCP Servers

You can run multiple MCP servers simultaneously:

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "C:\\Users\\...\\run_docker_stdio.bat"
    },
    "other-mcp-server": {
      "command": "other-server-command"
    }
  }
}
```

Claude Desktop will load all configured servers.

---

## Benefits of This Approach

✅ **No Port Binding** - Uses STDIO, not HTTP ports
✅ **No IP Address Issues** - Works regardless of WSL IP changes
✅ **Container Isolation** - Full Docker environment
✅ **User Credentials** - Uses your Azure login from WSL
✅ **Automatic Restarts** - Docker handles container lifecycle
✅ **Dual Transport** - Same container can serve HTTP and STDIO
✅ **No Proxy Required** - Direct docker exec communication

---

## Next Steps

- **Usage Guide:** See [docs/USAGE.md](USAGE.md) for tool reference
- **Troubleshooting:** See [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more issues
- **Docker Guide:** See [docs/DOCKER.md](DOCKER.md) for advanced Docker configuration

---

**Questions or Issues?**
- Check troubleshooting section above
- Review Docker Desktop logs: Settings → Troubleshoot → Show logs
- Check WSL: `wsl --status` and `wsl --list --verbose`
- Verify container: `docker logs azure-devops-mcp`
