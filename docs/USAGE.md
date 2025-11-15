# MCP Tools Usage Guide

Complete guide to using the Azure DevOps Sprint MCP Server's 15 tools and 3 resources.

---

## Table of Contents

- [Overview](#overview)
- [Tool Categories](#tool-categories)
- [Query Tools (9 Tools)](#query-tools-9-tools)
- [Monitoring Tools (2 Tools)](#monitoring-tools-2-tools)
- [Resources (3 Read-Only Contexts)](#resources-3-read-only-contexts)
- [Multi-Project Usage](#multi-project-usage)
- [Common Use Cases](#common-use-cases)
- [Best Practices](#best-practices)

---

## Overview

The Azure DevOps Sprint MCP server provides 15 tools organized into three categories:

- **9 Query Tools** - Read and write operations for work items and sprints
- **4 Advanced Query Tools** - Hierarchical queries, search, and historical analysis (included in the 9)
- **2 Monitoring Tools** - Server health and performance metrics

Plus **3 Resources** for context-aware information.

**New in v2.1:** All tools support multi-project usage via optional `project` parameter.

---

## Tool Categories

### Core Work Item Tools
- `get_my_work_items` - Your assigned work items
- `get_work_item_details` - Complete work item details
- `update_work_item` - Update work item fields
- `create_work_item` - Create new work items
- `add_comment` - Add comments to work items

### Sprint Management Tools
- `get_sprint_work_items` - Work items in a sprint
- `get_team_iterations` - List all sprints
- `get_current_sprint` - Current sprint with metrics
- `move_to_sprint` - Reassign work items to sprints

### Advanced Query Tools
- `search_work_items` - Full-text indexed search
- `get_work_item_hierarchy` - Parent-child relationships
- `get_historical_work_items` - Historical state queries

### Monitoring Tools
- `health_check` - Server health and authentication status
- `get_service_statistics` - Performance and cache metrics

---

## Query Tools (9 Tools)

### 1. get_my_work_items

Get work items assigned to you.

**Parameters:**
- `project` (optional): Project name (uses default if not specified)
- `state` (optional): Filter by state ("Active", "Resolved", etc.)
- `work_item_type` (optional): Filter by type ("Bug", "Task", etc.)
- `limit` (optional): Max results (default: 100, max: 20,000)

**Example:**
```python
# Get all your active work items (default project)
items = await get_my_work_items(state="Active")

# Get bugs from specific project
bugs = await get_my_work_items(
    project="AI-Proj",
    work_item_type="Bug",
    state="Active"
)

# Get recent 50 items
recent = await get_my_work_items(limit=50)
```

**Returns:**
```json
{
  "total_count": 12,
  "work_items": [
    {
      "id": 1234,
      "title": "Fix login bug",
      "state": "Active",
      "work_item_type": "Bug",
      "assigned_to": "user@company.com",
      "iteration_path": "MyProject\\Sprint 10",
      "priority": 1,
      "remaining_work": 4.0
    }
  ]
}
```

---

### 2. get_sprint_work_items

Get work items for a sprint with progress statistics.

**Parameters:**
- `project` (optional): Project name
- `iteration_path` (optional): Sprint path (default: current sprint)
- `team_name` (optional): Team name (default: default team)
- `limit` (optional): Max results (default: 500, max: 20,000)

**Example:**
```python
# Current sprint (default project)
sprint = await get_sprint_work_items()

# Specific sprint in specific project
sprint = await get_sprint_work_items(
    project="Marketing-Proj",
    iteration_path="Sprint 12"
)

# Limit results
top_items = await get_sprint_work_items(limit=100)
```

**Returns:**
```json
{
  "sprint_name": "Sprint 10",
  "iteration_path": "MyProject\\Sprint 10",
  "total_items": 42,
  "completed_items": 27,
  "in_progress_items": 10,
  "not_started_items": 5,
  "completion_percentage": 64.3,
  "work_items": [...]
}
```

---

### 3. get_work_item_details

Get complete details of a specific work item.

**Parameters:**
- `work_item_id` (required): Work item ID
- `project` (optional): Project name
- `include_comments` (optional): Include comments (default: true)
- `expand` (optional): Expansion level ("None", "Relations", "All")

**Example:**
```python
# Full details with comments
item = await get_work_item_details(work_item_id=1234)

# Without comments (faster)
item = await get_work_item_details(
    work_item_id=1234,
    include_comments=False
)

# Specific project with all relations
item = await get_work_item_details(
    work_item_id=1234,
    project="AI-Proj",
    expand="All"
)
```

**Returns:**
```json
{
  "id": 1234,
  "title": "Fix login bug",
  "state": "Active",
  "work_item_type": "Bug",
  "assigned_to": "user@company.com",
  "description": "<p>Bug description</p>",
  "created_date": "2025-01-15T10:00:00Z",
  "changed_date": "2025-01-16T14:30:00Z",
  "priority": 1,
  "comments": [...],
  "relations": [...],
  "url": "https://dev.azure.com/..."
}
```

---

### 4. get_team_iterations

List all sprints/iterations for a team.

**Parameters:**
- `project` (optional): Project name
- `team_name` (optional): Team name (default: default team)

**Example:**
```python
# Get iterations for default project
iterations = await get_team_iterations()

# Specific project and team
iterations = await get_team_iterations(
    project="DevOps-Proj",
    team_name="Platform Team"
)
```

**Returns:**
```json
[
  {
    "id": "abc-123",
    "name": "Sprint 10",
    "path": "MyProject\\Sprint 10",
    "start_date": "2025-01-15T00:00:00Z",
    "finish_date": "2025-01-29T00:00:00Z",
    "time_frame": "current"
  }
]
```

---

### 5. get_current_sprint

Get current active sprint with progress metrics.

**Parameters:**
- `project` (optional): Project name
- `team_name` (optional): Team name (default: default team)

**Example:**
```python
# Current sprint for default project
sprint = await get_current_sprint()

# Specific project
sprint = await get_current_sprint(project="Marketing-Proj")
```

**Returns:**
```json
{
  "id": "abc-123",
  "name": "Sprint 10",
  "path": "MyProject\\Sprint 10",
  "start_date": "2025-01-15T00:00:00Z",
  "end_date": "2025-01-29T00:00:00Z",
  "days_remaining": 3,
  "total_items": 42,
  "completed_items": 27,
  "in_progress_items": 10,
  "not_started_items": 5,
  "completion_percentage": 64.3
}
```

---

### 6. update_work_item

Update work item fields.

**Parameters:**
- `work_item_id` (required): Work item ID
- `fields` (required): Dictionary of field updates
- `project` (optional): Project name
- `comment` (optional): Comment to add with update

**Example:**
```python
# Update state
await update_work_item(
    work_item_id=1234,
    fields={"System.State": "Resolved"}
)

# Update multiple fields with comment
await update_work_item(
    work_item_id=1234,
    fields={
        "System.State": "Active",
        "System.AssignedTo": "dev@company.com",
        "Microsoft.VSTS.Common.Priority": 1,
        "Microsoft.VSTS.Scheduling.RemainingWork": 8.0
    },
    comment="Taking ownership and prioritizing"
)

# Update in specific project
await update_work_item(
    work_item_id=1234,
    project="AI-Proj",
    fields={"System.State": "Done"}
)
```

**Common Field Names:**
- `System.State` - Work item state
- `System.AssignedTo` - Assigned user email
- `System.Title` - Work item title
- `System.Description` - Description (HTML)
- `System.IterationPath` - Sprint path
- `Microsoft.VSTS.Common.Priority` - Priority (1-4)
- `Microsoft.VSTS.Scheduling.RemainingWork` - Remaining hours
- `Microsoft.VSTS.Scheduling.StoryPoints` - Story points

See [API-REFERENCE.md](./API-REFERENCE.md) for complete field list.

---

### 7. create_work_item

Create a new work item.

**Parameters:**
- `title` (required): Work item title
- `work_item_type` (required): Type ("Bug", "Task", "User Story", etc.)
- `project` (optional): Project name
- `description` (optional): HTML description
- `assigned_to` (optional): User email
- `iteration_path` (optional): Sprint path
- `priority` (optional): Priority 1-4 (1 is highest)

**Example:**
```python
# Create bug
bug = await create_work_item(
    title="Login fails with special characters",
    work_item_type="Bug",
    description="<p>Users cannot login with @ or # in password</p>",
    assigned_to="dev@company.com",
    iteration_path="Sprint 10",
    priority=1
)

# Create in specific project
task = await create_work_item(
    title="Implement PDF export",
    work_item_type="Task",
    project="Marketing-Proj",
    assigned_to="dev@company.com"
)
```

---

### 8. add_comment

Add a comment to a work item.

**Parameters:**
- `work_item_id` (required): Work item ID
- `comment` (required): Comment text
- `project` (optional): Project name

**Example:**
```python
# Add comment
await add_comment(
    work_item_id=1234,
    comment="Fix deployed to production. Monitoring for issues."
)

# Add to specific project
await add_comment(
    work_item_id=1234,
    project="AI-Proj",
    comment="Code review completed"
)
```

---

### 9. move_to_sprint

Move a work item to a different sprint.

**Parameters:**
- `work_item_id` (required): Work item ID
- `iteration_path` (required): Target sprint path
- `project` (optional): Project name

**Example:**
```python
# Move to next sprint
await move_to_sprint(
    work_item_id=1234,
    iteration_path="Sprint 11"
)

# Move to backlog (use project root)
await move_to_sprint(
    work_item_id=1234,
    iteration_path="MyProject"
)

# Move in specific project
await move_to_sprint(
    work_item_id=1234,
    iteration_path="Sprint 13",
    project="Marketing-Proj"
)
```

---

### Advanced Query Tools

### 10. search_work_items

Full-text indexed search across work items.

**Parameters:**
- `search_text` (required): Search text (indexed "Contains Words")
- `project` (optional): Project name
- `field` (optional): Field to search (default: "System.Title")
- `work_item_type` (optional): Filter by type
- `state` (optional): Filter by state
- `limit` (optional): Max results (default: 100)

**Example:**
```python
# Search titles
results = await search_work_items(search_text="authentication")

# Search descriptions
results = await search_work_items(
    search_text="database timeout",
    field="System.Description"
)

# Filter results
bugs = await search_work_items(
    search_text="crash",
    work_item_type="Bug",
    state="Active",
    project="AI-Proj"
)
```

---

### 11. get_work_item_hierarchy

Query parent-child relationships (Epic → Feature → Story → Task).

**Parameters:**
- `work_item_id` (required): Root work item ID
- `project` (optional): Project name
- `link_type` (optional): Link type (default: "System.LinkTypes.Hierarchy-Forward")
- `max_depth` (optional): Max depth (default: 5)

**Link Types:**
- `System.LinkTypes.Hierarchy-Forward` - Children (Epic → Features)
- `System.LinkTypes.Hierarchy-Reverse` - Parents (Task → Story)
- `System.LinkTypes.Related` - Related items
- `System.LinkTypes.Dependency-Forward` - What depends on this
- `System.LinkTypes.Dependency-Reverse` - What this depends on

**Example:**
```python
# Get Epic with all children
hierarchy = await get_work_item_hierarchy(work_item_id=100)

# Get task's parent story
parent = await get_work_item_hierarchy(
    work_item_id=1234,
    link_type="System.LinkTypes.Hierarchy-Reverse"
)

# Get dependencies
deps = await get_work_item_hierarchy(
    work_item_id=1234,
    link_type="System.LinkTypes.Dependency-Reverse",
    project="AI-Proj"
)
```

**Returns:**
```json
{
  "id": 100,
  "title": "Authentication Epic",
  "work_item_type": "Epic",
  "state": "Active",
  "children": [
    {
      "id": 101,
      "title": "SSO Feature",
      "work_item_type": "Feature",
      "children": [...]
    }
  ],
  "total_count": 15
}
```

---

### 12. get_historical_work_items

Find items that were ever in a specific state (regression tracking).

**Parameters:**
- `historical_state` (required): State to check (e.g., "Resolved")
- `project` (optional): Project name
- `work_item_type` (optional): Filter by type
- `limit` (optional): Max results (default: 100)

**Use Cases:**
- Find regressions (was Resolved, now Active)
- Track churned work
- Analyze state transitions

**Example:**
```python
# Find potential regressions
regressions = await get_historical_work_items(
    historical_state="Resolved",
    work_item_type="Bug"
)

# Filter for current regressions
current_regressions = [
    bug for bug in regressions['work_items']
    if bug['state'] == 'Active'
]

# Specific project
history = await get_historical_work_items(
    historical_state="Resolved",
    project="AI-Proj"
)
```

---

## Monitoring Tools (2 Tools)

### 1. health_check

Check server health and authentication status.

**Parameters:** None

**Example:**
```python
health = await health_check()
```

**Returns:**
```json
{
  "status": "healthy",
  "service": "Azure DevOps Sprint Manager",
  "version": "2.1",
  "authenticated": true,
  "auth_method": "Azure Managed Identity",
  "organization": "https://dev.azure.com/your-org"
}
```

---

### 2. get_service_statistics

Get performance metrics and cache statistics.

**Parameters:** None

**Example:**
```python
stats = await get_service_statistics()
```

**Returns:**
```json
{
  "service_manager": {
    "loaded_projects": 3,
    "sprint_services": 3,
    "workitem_services": 2,
    "total_services": 5,
    "service_creations": 6,
    "cache_hits": 120,
    "cache_hit_rate_percent": 95.24,
    "default_project": "AI-Proj"
  },
  "loaded_projects": ["AI-Proj", "Marketing-Proj", "DevOps-Proj"],
  "timestamp": "2025-11-15T08:00:00.000000"
}
```

---

## Resources (3 Read-Only Contexts)

Resources provide context-aware information in Markdown format.

### 1. sprint://current

Current sprint overview (uses default project).

**Example:**
```
# Sprint 10
**Status:** In Progress
**Duration:** 2025-01-15 to 2025-01-29
**Days Remaining:** 3

## Progress
- Total Items: 42
- Completed: 27 (64.3%)
- In Progress: 10
- Not Started: 5
```

---

### 2. sprint://{iteration_path}

Specific sprint details (uses default project).

**Example:**
```
sprint://Sprint%209
```

---

### 3. workitem://{work_item_id}

Full work item context (uses default project).

**Example:**
```
workitem://1234
```

---

## Multi-Project Usage

**New in v2.1:** Work with multiple projects in a single organization.

### Configuration

Set default project in `.env`:
```bash
AZURE_DEVOPS_PROJECT=AI-Proj
```

### Usage Patterns

**Use default project:**
```python
# No project parameter = uses AZURE_DEVOPS_PROJECT
items = await get_my_work_items(state="Active")
sprint = await get_current_sprint()
```

**Override with specific project:**
```python
# Specify project explicitly
ai_items = await get_my_work_items(project="AI-Proj", state="Active")
marketing_sprint = await get_current_sprint(project="Marketing-Proj")
```

**Work across multiple projects:**
```python
# Each call can use different project
ai_sprint = await get_current_sprint(project="AI-Proj")
marketing_sprint = await get_current_sprint(project="Marketing-Proj")
devops_sprint = await get_current_sprint(project="DevOps-Proj")
```

**Benefits:**
- Single authentication for all projects
- Services lazy-loaded per project
- Isolated cache per project
- No performance penalty

---

## Common Use Cases

### Daily Standup Report

```python
# Get your work for standup
items = await get_my_work_items(state="Active")

for item in items['work_items']:
    print(f"[{item['work_item_type']}] {item['title']}")
    print(f"  State: {item['state']}")
    print(f"  Remaining: {item.get('remaining_work', 'N/A')} hours")
```

---

### Sprint Planning

```python
# View current sprint progress
sprint = await get_current_sprint()

print(f"Sprint: {sprint['name']}")
print(f"Completion: {sprint['completion_percentage']:.1f}%")
print(f"Days remaining: {sprint['days_remaining']}")

# Move incomplete items to next sprint
if sprint['days_remaining'] < 2:
    incomplete = [
        item for item in sprint['work_items']
        if item['state'] not in ['Done', 'Closed']
    ]

    for item in incomplete:
        await move_to_sprint(
            work_item_id=item['id'],
            iteration_path="Sprint 11"
        )
```

---

### Bug Triage

```python
# Find high priority bugs
bugs = await search_work_items(
    search_text="",
    work_item_type="Bug",
    state="Active"
)

high_priority = [
    bug for bug in bugs['work_items']
    if bug.get('priority', 4) <= 2
]

for bug in high_priority:
    print(f"Bug {bug['id']}: {bug['title']}")
    print(f"  Priority: {bug['priority']}")
    print(f"  Assigned: {bug['assigned_to']}")
```

---

### Regression Tracking

```python
# Find bugs that were resolved but are now active again
regressions = await get_historical_work_items(
    historical_state="Resolved",
    work_item_type="Bug"
)

current_regressions = [
    bug for bug in regressions['work_items']
    if bug['state'] == 'Active'
]

print(f"Found {len(current_regressions)} regressions")
for bug in current_regressions:
    print(f"  Bug {bug['id']}: {bug['title']}")
```

---

### Epic Breakdown

```python
# View Epic with all child work
hierarchy = await get_work_item_hierarchy(
    work_item_id=100,  # Epic ID
    max_depth=3
)

def print_hierarchy(item, indent=0):
    print("  " * indent + f"{item['work_item_type']} {item['id']}: {item['title']}")
    for child in item.get('children', []):
        print_hierarchy(child, indent + 1)

print_hierarchy(hierarchy)
```

---

### Multi-Project Dashboard

```python
# Monitor multiple projects
projects = ["AI-Proj", "Marketing-Proj", "DevOps-Proj"]

for project in projects:
    sprint = await get_current_sprint(project=project)
    print(f"\n{project}:")
    print(f"  Sprint: {sprint['name']}")
    print(f"  Completion: {sprint['completion_percentage']:.1f}%")
    print(f"  Items: {sprint['total_items']}")
```

---

## Best Practices

### 1. Use Query Limits

```python
# Good: Fetch only what you need
recent = await get_my_work_items(limit=50)

# Avoid: Large result sets
all_items = await get_my_work_items(limit=5000)  # Slow!
```

---

### 2. Disable Comments When Not Needed

```python
# Good: Skip comments for list views
items = await get_work_item_details(
    work_item_id=1234,
    include_comments=False
)

# Use comments only for detail views
item = await get_work_item_details(work_item_id=1234)
```

---

### 3. Use Specific Filters

```python
# Good: Filter in query
bugs = await search_work_items(
    search_text="",
    work_item_type="Bug",
    state="Active"
)

# Avoid: Fetch all, filter in code
all_items = await get_sprint_work_items()
bugs = [i for i in all_items if i['work_item_type'] == 'Bug']
```

---

### 4. Leverage Caching

All read operations are cached for 5 minutes:

```python
# First call: Fetches from API
item = await get_work_item_details(work_item_id=1234)

# Second call within 5 min: Returns from cache (instant!)
item = await get_work_item_details(work_item_id=1234)

# Update invalidates cache
await update_work_item(work_item_id=1234, fields={...})

# Next call: Fresh data from API
item = await get_work_item_details(work_item_id=1234)
```

---

### 5. Use Indexed Search

```python
# Good: Indexed search (fast)
results = await search_work_items(search_text="authentication")

# The tool uses "Contains Words" internally (indexed)
```

---

### 6. Monitor Performance

```python
# Check cache effectiveness
stats = await get_service_statistics()

if stats['service_manager']['cache_hit_rate_percent'] < 90:
    print("Warning: Low cache hit rate")
```

---

### 7. Handle Errors Gracefully

All operations automatically retry transient errors (500, 502, 503, 504, 429) with exponential backoff. You don't need to implement retry logic!

```python
# This automatically retries on transient errors
try:
    item = await get_work_item_details(work_item_id=1234)
except Exception as e:
    print(f"Error: {e}")
    # Friendly error messages included
```

---

### 8. Project Organization

```python
# Set default project for common operations
# In .env:
AZURE_DEVOPS_PROJECT=AI-Proj

# Then use project parameter only when needed
my_items = await get_my_work_items()  # Uses AI-Proj
other_items = await get_my_work_items(project="Marketing-Proj")
```

---

## Performance Metrics

**Achieved Performance:**
- Cache hit rate: 95%+
- Cached response time: <100ms
- Uncached response time: <2s
- 70% reduction in response sizes
- Automatic retry on transient errors

**Query Limits:**
- Default limit: 100 items
- Sprint limit: 500 items
- Maximum limit: 20,000 items
- Batch size: 200 items per request

---

## Additional Resources

- [API-REFERENCE.md](./API-REFERENCE.md) - Field names, states, types
- [DOCKER.md](./DOCKER.md) - Docker deployment guide
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - Common issues and solutions
- [DEVELOPMENT.md](./DEVELOPMENT.md) - Contributing guide

---

**Version:** 2.1 (Multi-Project Support)
**Last Updated:** 2025-11-15
