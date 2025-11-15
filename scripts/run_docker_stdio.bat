@echo off
REM Docker STDIO Bridge for Claude Desktop (Windows)
REM Connects Claude Desktop to Azure DevOps MCP server running in Docker

REM Redirect errors to stderr so they appear in Claude Desktop logs
echo [Bridge] Starting Azure DevOps MCP Docker bridge... >&2

REM Check if Docker is running
docker ps >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [Bridge] ERROR: Docker is not running or not accessible >&2
    echo [Bridge] Please start Docker Desktop and try again >&2
    exit /b 1
)

REM Check if container is running using simpler approach
docker ps -q -f "name=azure-devops-mcp" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [Bridge] ERROR: Container 'azure-devops-mcp' is not running >&2
    echo [Bridge] Please start the container in WSL with: docker-compose up -d >&2
    exit /b 1
)

echo [Bridge] Connecting to Docker container... >&2

REM Run the server in stdio mode
docker exec -i -e MCP_TRANSPORT=stdio azure-devops-mcp python -m src.server
