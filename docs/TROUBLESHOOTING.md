# Troubleshooting Guide

Solutions to common issues when running Azure DevOps Sprint MCP Server.

---

## Table of Contents

- [Authentication Issues](#authentication-issues)
- [Connection Problems](#connection-problems)
- [Docker Issues](#docker-issues)
- [Windows/WSL Specific Issues](#windowswsl-specific-issues)
- [Performance Problems](#performance-problems)
- [Common Error Messages](#common-error-messages)
- [Claude Desktop Issues](#claude-desktop-issues)
- [Debug Mode](#debug-mode)

---

## Authentication Issues

### Issue: "Authentication failed"

**Error Message:**
```
AuthenticationError: Authentication failed. Your token may have expired.
```

**Solutions:**

#### For Managed Identity (az login):
```bash
# Re-login to Azure
az login

# Verify you're logged in
az account show

# Check which account is active
az account show --query user.name -o tsv

# Restart the MCP server
docker-compose restart  # If using Docker
# OR
python -m src.server    # If running locally
```

#### For Personal Access Token (PAT):
```bash
# Check PAT hasn't expired
# Go to: https://dev.azure.com/{org}/_usersSettings/tokens

# Verify PAT has correct scopes
# Required: vso.work (Read & Write)

# Update .env file with new PAT
AZURE_DEVOPS_PAT=your_new_token_here

# Restart server
```

#### For Service Principal:
```bash
# Verify environment variables are set
echo $AZURE_CLIENT_ID
echo $AZURE_TENANT_ID
# Don't echo the secret!

# Check secret hasn't expired
# Azure Portal → App Registrations → Certificates & secrets

# Test service principal login
az login --service-principal \
  -u $AZURE_CLIENT_ID \
  -p $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID
```

---

### Issue: "Permission denied" / "403 Forbidden"

**Error Message:**
```
PermissionDeniedError: Permission denied. Your credentials need 'vso.work_write' scope.
```

**Solutions:**

1. **Check PAT Scopes:**
   - Go to Azure DevOps → User Settings → Personal Access Tokens
   - Verify your PAT has:
     - `vso.work` (Read)
     - `vso.work_write` (Read & Write)

2. **Check Project Permissions:**
   - Azure DevOps → Project Settings → Permissions
   - Verify your user has:
     - **Contributor** role or higher
     - **Edit work items** permission

3. **For Managed Identity:**
   - Verify your Azure account has access to the Azure DevOps organization
   - Visit your organization in a browser
   - If you can access it there, the MCP server should work too

---

### Issue: "Unauthorized" / "401 Error"

**Error Message:**
```
401 Unauthorized
```

**Solutions:**

1. **Check organization URL:**
   ```bash
   # Verify URL is correct (case-sensitive!)
   echo $AZURE_DEVOPS_ORG_URL
   # Should be: https://dev.azure.com/yourorg
   ```

2. **Test authentication manually:**
   ```bash
   # Quick auth test
   python -c "from src.auth import AzureDevOpsAuth; import asyncio; import os; from dotenv import load_dotenv; load_dotenv(); auth = AzureDevOpsAuth(os.getenv('AZURE_DEVOPS_ORG_URL')); asyncio.run(auth.initialize()); print('Success:', auth.get_auth_info()['method'])"
   ```

3. **For PAT authentication:**
   - Ensure PAT is not expired
   - Check PAT has correct organization access

---

## Connection Problems

### Issue: "Project 'X' not found"

**Error Message:**
```
Project 'MyProject' not found or you do not have access.
```

**Solutions:**

1. **Verify project name (case-sensitive!):**
   ```bash
   # Project name must match exactly as shown in Azure DevOps
   # Check: https://dev.azure.com/{org}/_projects

   # Update .env file
   AZURE_DEVOPS_PROJECT=YourExactProjectName
   ```

2. **Check project access:**
   - Azure DevOps → Project Settings → Permissions
   - Ensure you're a member of the project

3. **For multi-project usage:**
   - All projects must be in the same organization
   - Organization URL must be correct

---

### Issue: "Cannot connect to Azure DevOps"

**Error Message:**
```
Failed to connect to dev.azure.com
```

**Solutions:**

1. **Check internet connection:**
   ```bash
   # Test connectivity
   ping dev.azure.com

   # Test DNS resolution
   nslookup dev.azure.com
   ```

2. **Check firewall/proxy:**
   - Ensure outbound HTTPS (443) is allowed
   - Check corporate proxy settings
   - Add Azure DevOps to allowlist if needed

3. **Verify organization URL:**
   ```bash
   # Test in browser
   # Visit: https://dev.azure.com/yourorg
   # Should load Azure DevOps homepage
   ```

---

## Docker Issues

### Issue: Container won't start

**Error Message:**
```
Error: Container 'azure-devops-mcp' failed to start
```

**Solutions:**

1. **Check logs:**
   ```bash
   docker logs azure-devops-mcp
   docker-compose logs
   ```

2. **Verify environment variables:**
   ```bash
   # Validate docker-compose config
   docker-compose config

   # Check .env file exists
   cat .env
   ```

3. **Check port availability:**
   ```bash
   # Check if port 8000 is already in use
   lsof -i :8000
   # OR on Windows
   netstat -ano | findstr :8000

   # Stop conflicting service or change port
   PORT=9000 docker-compose up -d
   ```

4. **Check permissions:**
   ```bash
   # Fix log/cache directory permissions
   sudo chown -R $USER:$USER logs/ cache/
   ```

---

### Issue: "Azure credentials not found in container"

**Error Message:**
```
DefaultAzureCredential failed to retrieve a token
```

**Solutions:**

1. **Verify Azure credentials are mounted:**
   ```bash
   # Check mount exists
   docker-compose exec azure-devops-mcp ls -la /root/.azure

   # Should show files like:
   # - azureProfile.json
   # - msal_token_cache.json
   # - clouds.config
   ```

2. **Re-login on host:**
   ```bash
   # Login on host machine
   az login

   # Verify credentials exist
   ls -la ~/.azure/

   # Restart container
   docker-compose restart
   ```

3. **Check docker-compose.yml volume:**
   ```yaml
   volumes:
     - ~/.azure:/root/.azure:ro  # Ensure this line exists
   ```

---

### Issue: "Permission denied" (Docker on Linux)

**Error Message:**
```
Got permission denied while trying to connect to the Docker daemon
```

**Solutions:**

1. **Add user to docker group:**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker

   # Test
   docker ps
   ```

2. **Or use sudo:**
   ```bash
   sudo docker-compose up -d
   ```

---

## Windows/WSL Specific Issues

### Issue: Python not found (Windows)

**Error in Claude Desktop logs:**
```
'python' is not recognized as an internal or external command
```

**Solutions:**

1. **Find Python path:**
   ```powershell
   # In PowerShell
   (Get-Command python).Path
   # Example: C:\Python311\python.exe
   ```

2. **Update Claude Desktop config with full path:**
   ```json
   {
     "mcpServers": {
       "azure-devops": {
         "command": "C:\\Python311\\python.exe",
         "args": [
           "C:\\path\\to\\azure-devops-sprint-mcp\\run_stdio.py"
         ]
       }
     }
   }
   ```

---

### Issue: Module not found (Windows)

**Error:**
```
ModuleNotFoundError: No module named 'fastmcp'
```

**Solutions:**

1. **Install dependencies:**
   ```powershell
   # Navigate to project directory
   cd C:\path\to\azure-devops-sprint-mcp

   # Install dependencies
   pip install -r requirements.txt

   # Or install globally
   pip install fastmcp azure-devops azure-identity python-dotenv
   ```

2. **Verify Python environment:**
   ```powershell
   python --version
   python -c "import fastmcp; print('FastMCP OK')"
   python -c "import azure.devops; print('Azure DevOps OK')"
   ```

---

### Issue: Azure CLI not found (Windows)

**Error:**
```
'az' is not recognized as an internal or external command
```

**Solutions:**

1. **Install Azure CLI:**
   - Download from: https://aka.ms/installazurecliwindows
   - Run installer
   - Restart PowerShell/Command Prompt

2. **Verify installation:**
   ```powershell
   az --version
   az login
   ```

3. **Restart Claude Desktop** after installing Azure CLI

---

### Issue: Path with spaces (Windows)

**Problem:** Windows paths with spaces need proper escaping.

**Wrong:**
```json
"args": ["C:\\Users\\My Name\\projects\\run_stdio.py"]
```

**Correct:**
```json
"args": ["C:\\Users\\My Name\\projects\\run_stdio.py"]
```

**Or use short path:**
```powershell
# Get short path in PowerShell
(New-Object -ComObject Scripting.FileSystemObject).GetFile("C:\Users\My Name\projects\run_stdio.py").ShortPath
```

---

### Issue: Docker command not found (Windows)

**Error:**
```
'docker' is not recognized as an internal or external command
```

**Solutions:**

1. **Verify Docker Desktop is installed and running:**
   - Check system tray for Docker icon
   - Open Docker Desktop

2. **Check Docker is in PATH:**
   ```powershell
   docker --version
   ```

3. **Use full path if needed:**
   ```
   C:\Program Files\Docker\Docker\resources\bin\docker.exe
   ```

4. **Enable WSL integration:**
   - Docker Desktop → Settings → Resources → WSL Integration
   - Enable for your WSL distro

---

## Performance Problems

### Issue: Slow responses

**Solutions:**

1. **Check cache statistics:**
   ```python
   stats = await get_service_statistics()
   print(f"Cache hit rate: {stats['service_manager']['cache_hit_rate_percent']}%")

   # Target: 90%+
   # If lower, may need to adjust cache TTL or query patterns
   ```

2. **Use query limits:**
   ```python
   # Instead of:
   items = await get_my_work_items()  # Returns up to 100

   # Use:
   items = await get_my_work_items(limit=50)  # Faster
   ```

3. **Disable comments when not needed:**
   ```python
   # Faster (no comments):
   item = await get_work_item_details(
       work_item_id=1234,
       include_comments=False
   )
   ```

4. **Check network latency:**
   ```bash
   # Test latency to Azure DevOps
   ping dev.azure.com

   # Test from container
   docker-compose exec azure-devops-mcp ping dev.azure.com
   ```

---

### Issue: High memory usage

**Solutions:**

1. **Check Docker stats:**
   ```bash
   docker stats azure-devops-mcp
   ```

2. **Increase memory limits:**
   ```yaml
   # In docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 1G  # Increase from 512M
   ```

3. **Clear cache:**
   ```bash
   # Remove cache directory
   rm -rf cache/*

   # Restart container
   docker-compose restart
   ```

---

### Issue: Rate limit exceeded

**Error Message:**
```
RateLimitError: Rate limit exceeded. Retry after 60 seconds.
```

**Solutions:**

1. **Wait and retry** (automatically handled):
   - The server automatically retries with exponential backoff
   - Respects `Retry-After` header

2. **Reduce request frequency:**
   ```python
   # Use batch operations
   sprint = await get_sprint_work_items()  # 1 request

   # Instead of:
   for id in [1, 2, 3, 4, 5]:  # 5 requests
       item = await get_work_item_details(work_item_id=id)
   ```

3. **Leverage caching:**
   - Read operations cached for 5 minutes
   - Reuse cached results when possible

---

## Common Error Messages

### ValidationError: "Invalid state 'XYZ'"

**Cause:** State value not in whitelist

**Solution:**
```python
# Check allowed states
from src.validation import StateValidator
print(StateValidator.VALID_STATES)

# Use valid state
await update_work_item(
    work_item_id=1234,
    fields={"System.State": "Active"}  # Valid
)
```

**Valid States:**
- New, Active, Resolved, Closed, Removed
- In Progress, Done, Committed, In Review
- Ready, Approved, To Do, Complete

See [API-REFERENCE.md](./API-REFERENCE.md) for complete list.

---

### ValidationError: "Invalid work item type 'XYZ'"

**Cause:** Work item type not in whitelist

**Solution:**
```python
# Check allowed types for your process template
# Common types:
# - Agile: Epic, Feature, User Story, Task, Bug
# - Scrum: Epic, Feature, Product Backlog Item, Task, Bug
# - CMMI: Epic, Feature, Requirement, Task, Bug

# Use valid type
await create_work_item(
    title="Test",
    work_item_type="Bug"  # Valid
)
```

---

### ValidationError: "Invalid field name 'XYZ'"

**Cause:** Field name not in whitelist

**Solution:**
```python
# Use correct field reference names
await update_work_item(
    work_item_id=1234,
    fields={
        "System.State": "Active",  # Correct
        # NOT "State": "Active"    # Wrong
    }
)
```

See [API-REFERENCE.md](./API-REFERENCE.md) for field names.

---

### QueryTooLargeError: "Query result exceeds maximum"

**Cause:** Query returns more than 20,000 items

**Solution:**
```python
# Add filters to reduce results
items = await get_my_work_items(
    state="Active",
    work_item_type="Bug",
    limit=100
)

# Or use pagination (if supported by your use case)
```

---

### TimeoutError: "Request timeout after 30 seconds"

**Cause:** Request took too long

**Solutions:**

1. **Check network connectivity:**
   ```bash
   ping dev.azure.com
   ```

2. **Reduce query size:**
   ```python
   # Use smaller limits
   items = await get_my_work_items(limit=50)
   ```

3. **Check Azure DevOps status:**
   - Visit: https://status.dev.azure.com/
   - Check for service outages

---

## Claude Desktop Issues

### Issue: MCP server not appearing in Claude Desktop

**Solutions:**

1. **Check configuration file location:**
   ```
   Windows: %APPDATA%\Claude\claude_desktop_config.json
   macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
   ```

2. **Validate JSON syntax:**
   ```powershell
   # Use online JSON validator
   # Or check with Python
   python -m json.tool "%APPDATA%\Claude\claude_desktop_config.json"
   ```

3. **Restart Claude Desktop completely:**
   - Quit Claude Desktop (not just close window)
   - Restart

4. **Check logs:**
   ```
   Windows: %APPDATA%\Claude\logs\
   macOS: ~/Library/Logs/Claude/
   ```

---

### Issue: MCP server crashes on startup

**Solutions:**

1. **Check Claude Desktop logs:**
   ```powershell
   # Windows
   cd $env:APPDATA\Claude\logs

   # View latest log
   Get-Content -Tail 50 mcp-server-azure-devops.log
   ```

2. **Test server manually:**
   ```powershell
   cd C:\path\to\azure-devops-sprint-mcp

   # Set environment variables
   $env:AZURE_DEVOPS_ORG_URL="https://dev.azure.com/yourorg"
   $env:AZURE_DEVOPS_PROJECT="YourProject"

   # Test server
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python run_stdio.py
   ```

3. **Check Python dependencies:**
   ```powershell
   pip list | findstr fastmcp
   pip list | findstr azure
   ```

---

## Debug Mode

### Enable Debug Logging

**In .env file:**
```bash
LOG_LEVEL=DEBUG
DEBUG=1
```

**For Docker:**
```bash
docker-compose down
docker-compose up  # Run in foreground to see logs
```

**For local Python:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run server
python -m src.server
```

**What you'll see:**
- Cache hits/misses
- API requests
- Retry attempts
- Token refresh events
- Query execution

---

### Collect Diagnostic Information

When reporting issues, collect:

1. **Version information:**
   ```bash
   python --version
   pip show fastmcp
   pip show azure-devops
   docker --version  # If using Docker
   ```

2. **Authentication method:**
   ```python
   from src.auth import AzureDevOpsAuth
   # ... initialize ...
   print(auth.get_auth_info())
   ```

3. **Server logs:**
   ```bash
   docker logs azure-devops-mcp > server.log
   # OR
   cat logs/server.log
   ```

4. **Cache statistics:**
   ```python
   stats = await get_service_statistics()
   print(stats)
   ```

5. **Configuration:**
   ```bash
   # Sanitize sensitive data first!
   cat .env | grep -v PAT | grep -v SECRET
   ```

---

## Getting Help

If issues persist after troubleshooting:

1. **Check existing issues:**
   - GitHub Issues: https://github.com/yourusername/azure-devops-sprint-mcp/issues

2. **Create new issue with:**
   - Error message
   - Steps to reproduce
   - Debug logs (sanitize credentials!)
   - Environment (OS, Python version, Docker version)
   - Configuration (sanitized)

3. **Resources:**
   - [USAGE.md](./USAGE.md) - Tool usage guide
   - [DOCKER.md](./DOCKER.md) - Docker deployment
   - [DEVELOPMENT.md](./DEVELOPMENT.md) - Development guide
   - [API-REFERENCE.md](./API-REFERENCE.md) - Field reference
   - Azure DevOps Status: https://status.dev.azure.com/

---

**Version:** 2.1
**Last Updated:** 2025-11-15
