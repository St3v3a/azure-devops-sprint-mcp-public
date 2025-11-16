# Azure DevOps Sprint MCP Server

> **Model Context Protocol (MCP) server for Azure DevOps sprint board and work item management**

[![Version](https://img.shields.io/badge/version-2.1-blue.svg)](https://github.com/yourusername/azure-devops-sprint-mcp)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

Enterprise-grade MCP server for managing Azure DevOps work items, sprints, and boards through natural language (Claude Desktop) or programmatic interfaces. Built with FastMCP and designed for production use with Azure Managed Identity authentication.

## ✨ Features

- **15 MCP Tools** - Complete work item and sprint management
- **Multi-Project Support** - Work with multiple Azure DevOps projects simultaneously (NEW in v2.1)
- **Health & Monitoring** - Built-in server health checks and performance metrics
- **Enterprise Authentication** - Azure Managed Identity, Service Principal, or PAT support
- **Production Ready** - Error handling, retry logic, caching, and security hardening
- **Docker Native** - Optimized containers with health checks and dual transport modes

## 🚀 Quick Start

### Prerequisites

- **Linux/macOS**: Python 3.10+ or Docker
- **Windows**: Docker Desktop with WSL 2 → **[See Windows/WSL Guide](docs/WSL-CLAUDE-DESKTOP.md)**
- Azure DevOps organization access
- Authentication: Azure CLI (`az login`), Service Principal, or PAT

---

### Step 1: Clone and Configure

```bash
# Clone repository
git clone https://github.com/yourusername/azure-devops-sprint-mcp.git
cd azure-devops-sprint-mcp

# Create .env file from template
cp .env.example .env

# Edit .env with your settings (required!)
nano .env  # or use your preferred editor
```

**Required in .env:**
```bash
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-organization
AZURE_DEVOPS_PROJECT=YourProject  # Recommended
```

---

### Step 2: Choose Your Deployment Mode

#### Option A: Docker (Recommended)

```bash
# Login to Azure for authentication
az login

# Start server with Docker
docker-compose up -d

# View logs
docker-compose logs -f
```

#### Option B: Python (Local Development)

```bash
# Run setup script (creates venv, installs dependencies)
./scripts/setup.sh

# Login to Azure for authentication
az login

# Start server
./scripts/start.sh
```

---

### Quick Verification

```bash
# Check server is running
curl http://localhost:8000/mcp

# Check Docker logs (if using Docker)
docker-compose logs

# Stop server
docker-compose down  # Docker mode
# OR
./scripts/stop.sh    # Python mode
```

## ⚙️ Configuration

The `.env` file supports these options:

```bash
# Required
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/your-organization

# Recommended (default project for multi-project support)
AZURE_DEVOPS_PROJECT=MyProject

# Authentication Methods (choose one)
# 1. Managed Identity (Recommended) - Just run 'az login', no config needed!
# 2. Service Principal (for automation)
# AZURE_CLIENT_ID=your-client-id
# AZURE_CLIENT_SECRET=your-client-secret
# AZURE_TENANT_ID=your-tenant-id
# 3. Personal Access Token (legacy)
# AZURE_DEVOPS_PAT=your-pat-token

# Server Settings (optional)
# MCP_TRANSPORT=http
# PORT=8000
```

**Recommended:** Use Azure Managed Identity (`az login`) - no tokens to manage, automatic refresh, and preserves your user identity in Azure DevOps audit logs.

## 📖 Documentation

- **[Setup & Installation](docs/SETUP.md)** - Complete setup guide for all deployment modes
- **[Usage Guide](docs/USAGE.md)** - Tool reference, examples, and best practices
- **[WSL + Claude Desktop](docs/WSL-CLAUDE-DESKTOP.md)** - Windows users guide for Claude Desktop integration
- **[Docker Deployment](docs/DOCKER.md)** - Docker and production deployment guide
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[API Reference](docs/API-REFERENCE.md)** - Fields, states, types, and WIQL queries
- **[Development Guide](docs/DEVELOPMENT.md)** - For contributors
- **[Changelog](CHANGELOG.md)** - Version history

## 🛠️ MCP Tools (15 Total)

### Core Work Item Tools

- **`get_my_work_items`** - Get your assigned work items
- **`get_work_item_details`** - Get complete work item details
- **`update_work_item`** - Update work item fields
- **`create_work_item`** - Create new work items
- **`add_comment`** - Add comments to work items

### Sprint Management Tools

- **`get_sprint_work_items`** - Get work items for a sprint
- **`get_current_sprint`** - Get current active sprint
- **`get_team_iterations`** - List all sprints/iterations
- **`move_to_sprint`** - Move work items between sprints

### Advanced Query Tools (NEW in v2.0)

- **`get_work_item_hierarchy`** - Get parent-child work item trees
- **`search_work_items`** - Full-text search across work items
- **`get_historical_work_items`** - Query historical state changes

### Monitoring Tools (NEW in v2.1)

- **`health_check`** - Server health and auth status
- **`get_service_statistics`** - Performance metrics and cache stats

### MCP Resources (3)

- **`sprint://current`** - Current sprint overview
- **`sprint://{iteration_path}`** - Specific sprint details
- **`workitem://{id}`** - Work item details with comments

## 💡 Common Use Cases

### Daily Standup with Claude Desktop

> "Show me my active work items for today"

> "What's the status of our current sprint?"

> "Move work item 12345 to the next sprint"

### Sprint Planning

```python
# Get current sprint capacity
sprint = await sprint_service.get_current_sprint()
print(f"Progress: {sprint['completion_percentage']}%")

# Get work items
items = await sprint_service.get_sprint_work_items()
```

### Multi-Project Management (NEW)

> "Show me work items from Project-A and Project-B"

```python
# Work with multiple projects
manager = ServiceManager(auth)
items_a = await manager.get_workitem_service("Project-A").get_my_work_items()
items_b = await manager.get_workitem_service("Project-B").get_my_work_items()
```

See [docs/USAGE.md](docs/USAGE.md) for more examples.

## 🔐 Authentication

The server supports three authentication methods (tried in order):

### 1. Azure Managed Identity (⭐ Recommended)

**Benefits:**
- ✅ Uses your personal Azure credentials
- ✅ No tokens to manage or rotate
- ✅ Automatic token refresh
- ✅ All operations tracked as YOUR user

**Setup:**
```bash
# Just login to Azure CLI
az login

# Server automatically uses your credentials
./scripts/start.sh
```

### 2. Service Principal (For Automation)

```bash
# Set in .env
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
```

### 3. Personal Access Token (Development Only)

```bash
# Set in .env
AZURE_DEVOPS_PAT=your-pat-token
```

See [docs/SETUP.md](docs/SETUP.md) for detailed authentication setup.

## 🐳 Docker Deployment

### Quick Start

```bash
# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Deployment

See [docs/DOCKER.md](docs/DOCKER.md) for:
- Azure Container Registry (ACR) deployment
- Azure Container Instances (ACI) deployment
- Health checks and monitoring
- Environment configuration

### Important Notes

**Cache Configuration**: The Azure DevOps SDK cache is stored in `/tmp/.azure-devops` (ephemeral, recreated on container restart). The application's performance cache (`src/cache.py`) is in-memory and provides 95%+ hit rates for work item queries. No persistent cache volume is needed, simplifying deployment and avoiding permission issues.

## 🖥️ Claude Desktop Integration

### Linux/macOS (Direct)

Edit `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "azure-devops": {
      "command": "python",
      "args": ["/path/to/azure-devops-sprint-mcp/scripts/run_stdio.py"],
      "env": {
        "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/yourorg",
        "AZURE_DEVOPS_PROJECT": "YourProject"
      }
    }
  }
}
```

### Windows + WSL (Docker Bridge)

See comprehensive guide: [docs/WSL-CLAUDE-DESKTOP.md](docs/WSL-CLAUDE-DESKTOP.md)

**Quick Summary:**

1. Start Docker container in WSL:
   ```bash
   docker-compose up -d
   ```

2. Configure Claude Desktop (Windows):
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

## 📁 Project Structure

```
azure-devops-sprint-mcp/
├── src/                    # Core MCP server implementation
│   ├── server.py          # FastMCP server (15 tools + 3 resources)
│   ├── auth.py            # Multi-method authentication
│   ├── service_manager.py # Multi-project management
│   ├── cache.py           # Performance caching
│   ├── validation.py      # Security validators
│   └── services/          # Sprint and work item services
├── tests/                  # Comprehensive test suite
├── docs/                   # Complete documentation
├── scripts/                # Maintenance and bridge scripts
│   ├── setup.sh           # First-time setup
│   ├── start.sh           # Start server
│   ├── stop.sh            # Stop server
│   ├── restart.sh         # Restart server
│   ├── run_stdio.py       # STDIO bridge (Linux/macOS)
│   ├── run_docker_stdio.py # Docker bridge (Windows/WSL)
│   └── run_docker_stdio.bat # Batch bridge (Windows)
├── examples/               # Example usage scripts
├── docker/                 # Docker development files
├── Dockerfile              # Production Docker image
├── docker-compose.yml      # Docker Compose config
├── pyproject.toml          # Package metadata
├── requirements.txt        # Dependencies
└── .env.example            # Configuration template
```

## 🧪 Development

### Setup Development Environment

```bash
# Clone and setup
git clone https://github.com/yourusername/azure-devops-sprint-mcp.git
cd azure-devops-sprint-mcp
./scripts/setup.sh

# Install dev dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# All tests
pytest

# Unit tests only (skip integration)
pytest -m "not integration"

# With coverage
pytest --cov=src
```

### Code Quality

```bash
# Format code
black src tests

# Lint
ruff check src tests

# Type checking
mypy src
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development guide.

## 🎯 What's New in v2.1

- **Multi-Project Support** - Work with multiple Azure DevOps projects simultaneously
  - ServiceManager for lazy-loaded, cached service instances
  - Per-project cache isolation
  - All tools accept optional `project` parameter
  - Backward compatible with default project

- **Health & Monitoring Tools**
  - `health_check()` - Server health and authentication status
  - `get_service_statistics()` - Performance metrics and cache statistics

- **Improved Documentation**
  - Reorganized docs into docs/ folder
  - Dedicated Windows/WSL setup guide
  - Consolidated troubleshooting guide
  - Complete API reference

- **Maintenance Scripts**
  - `./scripts/setup.sh` - Automated setup
  - `./scripts/start.sh` - Start server (Docker or Python)
  - `./scripts/stop.sh` - Stop server
  - `./scripts/restart.sh` - Restart server

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

## 🐛 Troubleshooting

### Common Issues

**Authentication Failed:**
```bash
# Verify Azure login
az account show

# If not logged in:
az login
```

**Server Won't Start:**
```bash
# Check logs
docker-compose logs

# Restart
./scripts/restart.sh
```

**Windows/WSL Issues:**
- Ensure Docker Desktop is running
- Enable WSL integration in Docker Desktop settings
- See [docs/WSL-CLAUDE-DESKTOP.md](docs/WSL-CLAUDE-DESKTOP.md)

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for comprehensive troubleshooting guide.

## 📊 Performance

- ✅ **70% smaller responses** - Specific field selection vs expand='All'
- ✅ **95%+ cache hit rate** - TTL-based in-memory caching with auto-invalidation
- ✅ **Sub-second cached queries** - In-memory LRU cache (no persistent storage needed)
- ✅ **Automatic retry** - Exponential backoff for transient errors
- ✅ **Query limits enforced** - No unbounded result sets
- ✅ **Simplified deployment** - SDK cache in `/tmp` (no volume permission management)

## 🤝 Contributing

Contributions welcome! Please see [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for:

- Development setup
- Code style guidelines
- Testing requirements
- Pull request process

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🔗 Links

- **Documentation:** [docs/](docs/)
- **Issues:** https://github.com/yourusername/azure-devops-sprint-mcp/issues
- **Azure DevOps API:** https://learn.microsoft.com/rest/api/azure/devops/
- **MCP Protocol:** https://modelcontextprotocol.io/
- **FastMCP:** https://github.com/jlowin/fastmcp

---

**Built with ❤️ using FastMCP and Azure DevOps REST API**

*Version 2.1 - Multi-Project Support - Production Ready*
