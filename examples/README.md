# Example Scripts

This directory contains example scripts demonstrating how to use the Azure DevOps Sprint MCP Server programmatically.

## Available Examples

### create_workitem.py
Example of creating work items using the MCP server.

**Usage:**
```bash
python examples/create_workitem.py
```

**Features:**
- Creates a new work item (Task, Bug, or User Story)
- Sets title, description, and other fields
- Demonstrates field validation
- Shows error handling

### query_sprint.py
Example of querying sprint information.

**Usage:**
```bash
python examples/query_sprint.py
```

**Features:**
- Lists team iterations
- Gets current sprint details
- Retrieves sprint work items
- Calculates sprint progress

## Running Examples

### Prerequisites

1. **Install the package:**
   ```bash
   pip install -e .
   ```

2. **Configure environment:**
   ```bash
   # Copy .env.example to .env
   cp .env.example .env

   # Edit .env with your settings
   nano .env
   ```

3. **Authenticate with Azure:**
   ```bash
   az login
   ```

### Direct Execution

```bash
# Activate virtual environment
source venv/bin/activate

# Run example
python examples/create_workitem.py
```

### Import as Module

You can also import and use the server programmatically:

```python
import asyncio
import os
from dotenv import load_dotenv
from src.auth import AzureDevOpsAuth
from src.service_manager import ServiceManager

async def main():
    # Load environment
    load_dotenv()

    # Initialize auth
    auth = AzureDevOpsAuth(os.getenv("AZURE_DEVOPS_ORG_URL"))
    await auth.initialize()

    # Create service manager
    manager = ServiceManager(auth, default_project=os.getenv("AZURE_DEVOPS_PROJECT"))

    # Use services
    workitem_service = manager.get_workitem_service()
    items = await workitem_service.get_my_work_items()

    print(f"Found {len(items)} work items")
    for item in items[:5]:
        print(f"  [{item['id']}] {item['title']}")

    # Cleanup
    await auth.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Creating Your Own Scripts

### Template

```python
#!/usr/bin/env python3
"""
Example script description
"""
import asyncio
import os
from dotenv import load_dotenv
from src.auth import AzureDevOpsAuth
from src.service_manager import ServiceManager

async def main():
    # Load environment
    load_dotenv()

    # Initialize auth
    org_url = os.getenv("AZURE_DEVOPS_ORG_URL")
    project = os.getenv("AZURE_DEVOPS_PROJECT")

    auth = AzureDevOpsAuth(org_url)
    await auth.initialize()

    # Create service manager
    manager = ServiceManager(auth, default_project=project)

    # Get services
    workitem_service = manager.get_workitem_service()
    sprint_service = manager.get_sprint_service()

    # Your code here
    # ...

    # Cleanup
    await auth.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### Best Practices

1. **Error Handling:**
   ```python
   from src.errors import AuthenticationError, WorkItemNotFoundError

   try:
       item = await workitem_service.get_work_item(123)
   except WorkItemNotFoundError:
       print("Work item not found")
   except AuthenticationError:
       print("Authentication failed")
   ```

2. **Multi-Project:**
   ```python
   # Get service for different project
   project1_service = manager.get_workitem_service("Project1")
   project2_service = manager.get_workitem_service("Project2")

   items1 = await project1_service.get_my_work_items()
   items2 = await project2_service.get_my_work_items()
   ```

3. **Caching:**
   ```python
   # Check cache statistics
   stats = workitem_service.get_cache_stats()
   print(f"Cache hit rate: {stats['hit_rate_percent']}%")
   ```

4. **Field Validation:**
   ```python
   from src.validation import validate_state, validate_work_item_type

   # Validate before using
   state = validate_state("Active")  # Raises ValidationError if invalid
   work_item_type = validate_work_item_type("Task")
   ```

## Common Use Cases

### 1. Bulk Update Work Items

```python
# Get all active bugs
bugs = await workitem_service.get_my_work_items(
    work_item_type="Bug",
    state="Active"
)

# Update priority
for bug in bugs:
    await workitem_service.update_work_item(
        work_item_id=bug['id'],
        fields={"Microsoft.VSTS.Common.Priority": 1},
        comment="Increased priority for triage"
    )
```

### 2. Sprint Report

```python
# Get current sprint
sprint = await sprint_service.get_current_sprint()

print(f"Sprint: {sprint['name']}")
print(f"Progress: {sprint['completion_percentage']:.1f}%")
print(f"Days remaining: {sprint['days_remaining']}")

# Get work items
result = await sprint_service.get_sprint_work_items()
for item in result['work_items']:
    print(f"  [{item['id']}] {item['title']} - {item['state']}")
```

### 3. Create Epic with Features

```python
# Create Epic
epic = await workitem_service.create_work_item(
    title="Q1 2025 Initiative",
    work_item_type="Epic",
    description="Major initiative for Q1",
    iteration_path="Sprint 1"
)

# Create Features under Epic
features = [
    "Feature 1: User Authentication",
    "Feature 2: Data Migration",
    "Feature 3: API Integration"
]

for feature_title in features:
    await workitem_service.create_work_item(
        title=feature_title,
        work_item_type="Feature",
        description=f"Feature for {epic['title']}",
        # Link to Epic using relations (see API docs)
    )
```

## Troubleshooting

**Import errors:**
```bash
# Ensure package is installed
pip install -e .
```

**Authentication errors:**
```bash
# Verify Azure login
az account show

# Check .env configuration
cat .env
```

**Module not found:**
```bash
# Run from project root
cd /path/to/azure-devops-sprint-mcp
python examples/script.py
```

## More Information

- **API Reference:** See [docs/API-REFERENCE.md](../docs/API-REFERENCE.md)
- **Usage Guide:** See [docs/USAGE.md](../docs/USAGE.md)
- **Development:** See [docs/DEVELOPMENT.md](../docs/DEVELOPMENT.md)
