# Development Guide

Guide for contributing to the Azure DevOps Sprint MCP Server project.

---

## Table of Contents

- [Development Setup](#development-setup)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Code Quality](#code-quality)
- [Architecture Overview](#architecture-overview)
- [Contributing Guidelines](#contributing-guidelines)
- [Release Process](#release-process)

---

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Azure DevOps organization access
- One of: Azure CLI, Service Principal, or PAT

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/azure-devops-sprint-mcp.git
cd azure-devops-sprint-mcp

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# OR
venv\Scripts\activate     # Windows

# Install in development mode
pip install -e ".[dev]"

# Verify installation
python -c "import fastmcp; print('OK')"
```

### Configuration

Create `.env` file:

```bash
# Required
AZURE_DEVOPS_ORG_URL=https://dev.azure.com/yourorg
AZURE_DEVOPS_PROJECT=YourProject

# Authentication (choose one)
# Option 1: Use Azure CLI (recommended)
# Just run: az login

# Option 2: Personal Access Token (development)
AZURE_DEVOPS_PAT=your_pat_here

# Option 3: Service Principal (automation)
# AZURE_CLIENT_ID=...
# AZURE_CLIENT_SECRET=...
# AZURE_TENANT_ID=...

# Optional
LOG_LEVEL=DEBUG
PORT=8000
```

### Quick Test

```bash
# Test authentication
python -c "from src.auth import AzureDevOpsAuth; import asyncio; import os; from dotenv import load_dotenv; load_dotenv(); auth = AzureDevOpsAuth(os.getenv('AZURE_DEVOPS_ORG_URL')); asyncio.run(auth.initialize()); print('Success:', auth.get_auth_info()['method'])"

# Run server
python -m src.server

# In another terminal, test with MCP Inspector
mcp-inspector python -m src.server
```

---

## Project Structure

```
azure-devops-sprint-mcp/
├── src/
│   ├── server.py                 # FastMCP server (15 tools, 3 resources)
│   ├── auth.py                   # Multi-method authentication
│   ├── service_manager.py        # Multi-project service factory
│   ├── models.py                 # Data models
│   ├── validation.py             # Input validators
│   ├── errors.py                 # Custom exceptions
│   ├── decorators.py             # Retry logic
│   ├── constants.py              # Field definitions
│   ├── cache.py                  # TTL-based caching
│   └── services/
│       ├── sprint_service.py     # Sprint operations
│       └── workitem_service.py   # Work item operations
├── tests/
│   ├── test_service_manager.py   # Multi-project tests (30 tests)
│   ├── test_multi_project_integration.py  # Integration tests (14 tests)
│   ├── test_validation.py        # Security validation tests
│   ├── test_cache.py             # Caching tests
│   ├── test_decorators.py        # Retry logic tests
│   └── test_errors.py            # Error handling tests
├── docs/                          # Documentation
│   ├── USAGE.md                  # Tool usage guide
│   ├── DOCKER.md                 # Docker deployment
│   ├── TROUBLESHOOTING.md        # Common issues
│   ├── DEVELOPMENT.md            # This file
│   └── API-REFERENCE.md          # Field reference
├── pyproject.toml                 # Package configuration
├── requirements.txt               # Dependencies
├── Dockerfile                     # Production image
├── docker-compose.yml             # Docker Compose config
└── .env.example                   # Example environment file
```

### Key Modules

**server.py** (600 lines)
- FastMCP server initialization
- 15 MCP tools implementation
- 3 MCP resources
- Multi-project parameter handling

**service_manager.py** (200 lines) - NEW in v2.1
- Multi-project service factory
- Service instance caching
- Cache statistics aggregation
- Per-project namespace management

**auth.py** (400 lines)
- Multi-method authentication (Managed Identity, Service Principal, PAT)
- Automatic token refresh
- Azure DevOps client creation

**services/sprint_service.py** (500 lines)
- Sprint queries and operations
- Iteration management
- Progress statistics
- Caching integration

**services/workitem_service.py** (800 lines)
- Work item CRUD operations
- WIQL query execution
- Hierarchical queries
- Batch operations

**validation.py** (300 lines)
- Whitelist-based validators
- WIQL sanitization
- SQL injection prevention

**cache.py** (200 lines)
- TTL-based caching (5-minute default)
- Thread-safe operations
- Hit rate statistics

**decorators.py** (150 lines)
- Retry with exponential backoff
- Timeout handling
- Error mapping

---

## Running Tests

### All Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=src

# Generate HTML coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Test Categories

```bash
# Unit tests only (skip integration tests)
pytest -m "not integration"

# Integration tests only (requires Azure DevOps credentials)
pytest -m integration

# Specific test file
pytest tests/test_validation.py -v

# Specific test
pytest tests/test_cache.py::test_cache_hit_rate -v
```

### Test Structure

**Unit Tests (30+ tests):**
- `test_service_manager.py` - Multi-project functionality
- `test_validation.py` - Input validation
- `test_cache.py` - Caching behavior
- `test_decorators.py` - Retry logic
- `test_errors.py` - Error handling

**Integration Tests (14+ tests):**
- `test_multi_project_integration.py` - Real Azure DevOps API tests
- Requires valid credentials
- Uses `@pytest.mark.integration` marker

### Writing Tests

**Example Unit Test:**
```python
import pytest
from src.validation import validate_state, ValidationError

def test_state_validator_accepts_valid_state():
    # Should not raise exception
    assert validate_state("Active") == "Active"

def test_state_validator_rejects_invalid_state():
    with pytest.raises(ValidationError) as exc:
        validate_state("InvalidState")
    assert "Invalid state" in str(exc.value)
```

**Example Integration Test:**
```python
import pytest
from src.service_manager import ServiceManager

@pytest.mark.integration
async def test_multi_project_work_items(auth, project1, project2):
    manager = ServiceManager(auth, default_project=project1)

    # Get work items from both projects
    items1 = await manager.get_workitem_service(project1).get_my_work_items()
    items2 = await manager.get_workitem_service(project2).get_my_work_items()

    assert items1['total_count'] >= 0
    assert items2['total_count'] >= 0
```

---

## Code Quality

### Formatting

```bash
# Format code with Black
black src tests

# Check formatting without changes
black --check src tests
```

**Black Configuration** (in `pyproject.toml`):
```toml
[tool.black]
line-length = 100
target-version = ['py310']
```

### Linting

```bash
# Lint with Ruff
ruff check src tests

# Auto-fix issues
ruff check --fix src tests

# Show all violations
ruff check --show-violations src tests
```

**Ruff Configuration** (in `pyproject.toml`):
```toml
[tool.ruff]
line-length = 100
target-version = "py310"
```

### Type Checking

```bash
# Type check with mypy
mypy src

# Strict mode
mypy --strict src
```

**Mypy Configuration** (in `pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
```

### Pre-commit Checks

Run all quality checks before committing:

```bash
# All checks
black src tests && ruff check src tests && mypy src && pytest

# Create alias in ~/.bashrc or ~/.zshrc
alias precommit='black src tests && ruff check src tests && mypy src && pytest'
```

---

## Architecture Overview

### Multi-Project Pattern (v2.1)

**ServiceManager** manages services for multiple projects:

```python
# Single authentication for organization
auth = AzureDevOpsAuth(org_url)
await auth.initialize()

# Service manager with optional default
manager = ServiceManager(auth, default_project="AI-Proj")

# Get/create services per project
service1 = manager.get_sprint_service("AI-Proj")     # Creates new
service2 = manager.get_workitem_service("AI-Proj")   # Creates new
service3 = manager.get_sprint_service("AI-Proj")     # Returns cached

# Each project has isolated cache namespace
# "sprints:AI-Proj", "workitems:Marketing-Proj", etc.
```

**Key Features:**
- Single `AzureDevOpsAuth` instance per organization
- Service instances cached per project
- Lazy-loading (services created on first use)
- Per-project cache namespaces
- Statistics aggregation

### Authentication Flow

```
Try Method 1: DefaultAzureCredential
 ├─ Managed Identity (Azure VMs)
 ├─ Azure CLI (az login)
 └─ Environment variables
     ↓ Success? → [AUTHENTICATED]
     ↓ No
Try Method 2: Service Principal
 └─ Requires: CLIENT_ID/SECRET/TENANT
     ↓ Success? → [AUTHENTICATED]
     ↓ No
Try Method 3: Personal Access Token
 └─ AZURE_DEVOPS_PAT
     ↓ Success? → [AUTHENTICATED]
     ↓ No
[AUTH FAILED]
```

### Caching Strategy

**5-Minute TTL Cache:**
```python
# Read operations cached
item = await service.get_work_item(123)  # API call
item = await service.get_work_item(123)  # From cache (instant!)

# Cache invalidated on updates
await service.update_work_item(123, fields={...})
item = await service.get_work_item(123)  # Fresh API call
```

**Cache Namespaces:**
- `sprints:{project}` - Sprint data per project
- `workitems:{project}` - Work item data per project
- Separate TTL tracking per namespace
- Thread-safe operations

### Error Handling Pattern

**Automatic Retry with Exponential Backoff:**
```python
@azure_devops_operation(timeout_seconds=30, max_retries=3)
async def api_call():
    # Automatically retries on transient errors
    # Schedule: Immediate → 1s → 2s → 4s
    pass
```

**Error Mapping:**
- 404 → `WorkItemNotFoundError` (friendly message)
- 401 → `AuthenticationError`
- 403 → `PermissionDeniedError`
- 429 → `RateLimitError` (respects Retry-After header)
- 500-504 → `TransientError` (auto-retry)

### Validation Pattern

**Whitelist-Based Validation:**
```python
# All inputs validated against whitelists
from src.validation import (
    validate_state,          # 20+ allowed states
    validate_work_item_type, # 20+ allowed types
    validate_field_name,     # 60+ allowed fields
    validate_wiql,           # SQL injection prevention
)

# Example
state = validate_state("Active")  # OK
state = validate_state("Invalid") # Raises ValidationError
```

---

## Contributing Guidelines

### Code Style

1. **Follow PEP 8** with 100-character line length
2. **Use type hints** for function signatures
3. **Write docstrings** for all public functions
4. **Add comments** for complex logic

**Example:**
```python
async def get_work_item(
    self,
    work_item_id: int,
    include_comments: bool = True
) -> Dict[str, Any]:
    """
    Get work item details by ID.

    Args:
        work_item_id: Work item ID
        include_comments: Include comments (default: True)

    Returns:
        Work item details dictionary

    Raises:
        WorkItemNotFoundError: If work item doesn't exist
        ValidationError: If work_item_id is invalid
    """
    # Implementation...
```

### Commit Messages

Follow conventional commits:

```
feat: Add multi-project support
fix: Handle rate limiting correctly
docs: Update usage guide
test: Add cache hit rate tests
refactor: Simplify service manager logic
```

### Pull Request Process

1. **Create feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test:**
   ```bash
   # Run all quality checks
   black src tests
   ruff check src tests
   mypy src
   pytest
   ```

3. **Commit with meaningful messages:**
   ```bash
   git add .
   git commit -m "feat: Add support for custom fields"
   ```

4. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **PR should include:**
   - Clear description of changes
   - Tests for new functionality
   - Documentation updates
   - No breaking changes (or clearly documented)

### Adding New Features

**1. Add validation (if needed):**
```python
# src/validation.py
class NewValidator:
    VALID_VALUES = {"value1", "value2"}

    @classmethod
    def validate(cls, value: str) -> str:
        if value not in cls.VALID_VALUES:
            raise ValidationError(f"Invalid value: {value}")
        return value
```

**2. Add service method:**
```python
# src/services/workitem_service.py
@azure_devops_operation(timeout_seconds=30, max_retries=3)
async def new_operation(self, param: str) -> Dict[str, Any]:
    """Operation description."""
    # Validate input
    param = validate_param(param)

    # Check cache
    cached = self._get_cached('operation', param)
    if cached:
        return cached

    # API call
    result = await self._fetch_data(param)

    # Cache result
    self._set_cached(result, 'operation', param)
    return result
```

**3. Add MCP tool:**
```python
# src/server.py
@mcp.tool()
async def new_tool(param: str, project: Optional[str] = None) -> Dict[str, Any]:
    """
    Tool description.

    Args:
        param: Parameter description
        project: Project name (optional)

    Returns:
        Result description
    """
    service = service_manager.get_workitem_service(project)
    return await service.new_operation(param)
```

**4. Add tests:**
```python
# tests/test_new_feature.py
def test_new_operation():
    result = await service.new_operation("value1")
    assert result['status'] == 'success'

@pytest.mark.integration
async def test_new_operation_integration(auth, project):
    service = WorkItemService(auth, project)
    result = await service.new_operation("value1")
    assert result is not None
```

**5. Update documentation:**
- Add to `docs/USAGE.md` (tool description)
- Add to `docs/API-REFERENCE.md` (if new fields)
- Update `README.md` (if major feature)

---

## Release Process

### Version Numbering

Follow Semantic Versioning (SemVer):
- **Major** (2.0.0): Breaking changes
- **Minor** (2.1.0): New features, backward compatible
- **Patch** (2.1.1): Bug fixes, backward compatible

### Release Checklist

1. **Update version:**
   ```python
   # src/server.py
   VERSION = "2.1.0"
   ```

2. **Update CHANGELOG.md:**
   ```markdown
   ## [2.1.0] - 2025-11-15

   ### Added
   - Multi-project support
   - Health check tool
   - Service statistics tool

   ### Changed
   - Improved caching performance

   ### Fixed
   - Token refresh edge case
   ```

3. **Run all tests:**
   ```bash
   pytest --cov=src
   # Target: 80%+ coverage
   ```

4. **Run quality checks:**
   ```bash
   black --check src tests
   ruff check src tests
   mypy src
   ```

5. **Build Docker image:**
   ```bash
   docker build -t azure-devops-sprint-mcp:2.1.0 .
   docker tag azure-devops-sprint-mcp:2.1.0 azure-devops-sprint-mcp:latest
   ```

6. **Test Docker image:**
   ```bash
   docker-compose up -d
   docker logs azure-devops-mcp
   # Verify health
   ```

7. **Create Git tag:**
   ```bash
   git tag -a v2.1.0 -m "Release v2.1.0: Multi-project support"
   git push origin v2.1.0
   ```

8. **Create GitHub release:**
   - Go to GitHub → Releases → New Release
   - Tag: v2.1.0
   - Title: v2.1.0 - Multi-Project Support
   - Description: Copy from CHANGELOG.md
   - Attach build artifacts (if any)

9. **Update documentation:**
   - README.md version badge
   - Documentation version footer
   - Docker image tags

---

## Development Tips

### Debugging

**Enable debug logging:**
```bash
# In .env
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Use MCP Inspector:**
```bash
# Interactive testing
mcp-inspector python -m src.server

# Test specific tool
# Use MCP Inspector UI to call tools
```

**Test authentication:**
```bash
python -c "from src.auth import AzureDevOpsAuth; import asyncio; import os; from dotenv import load_dotenv; load_dotenv(); auth = AzureDevOpsAuth(os.getenv('AZURE_DEVOPS_ORG_URL')); asyncio.run(auth.initialize()); print(auth.get_auth_info())"
```

### Performance Profiling

**Cache statistics:**
```python
from src.service_manager import ServiceManager

manager = ServiceManager(auth)
stats = manager.get_statistics()
print(f"Cache hit rate: {stats['cache_hit_rate_percent']}%")
```

**Time operations:**
```python
import time

start = time.time()
result = await service.get_work_item(1234)
print(f"Took {time.time() - start:.2f}s")
```

---

## Resources

- **FastMCP Documentation:** https://github.com/jlowin/fastmcp
- **Azure DevOps REST API:** https://learn.microsoft.com/rest/api/azure/devops/
- **WIQL Syntax:** https://learn.microsoft.com/azure/devops/boards/queries/wiql-syntax
- **MCP Protocol:** https://modelcontextprotocol.io/

---

## Getting Help

- **Issues:** https://github.com/yourusername/azure-devops-sprint-mcp/issues
- **Discussions:** https://github.com/yourusername/azure-devops-sprint-mcp/discussions
- **Contributing:** See this guide

---

**Version:** 2.1
**Last Updated:** 2025-11-15
