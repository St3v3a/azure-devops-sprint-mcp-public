# API Reference

Complete reference for Azure DevOps work item fields, states, types, and WIQL query examples.

---

## Table of Contents

- [Work Item Field Names](#work-item-field-names)
- [Work Item States](#work-item-states)
- [Work Item Types](#work-item-types)
- [Link Types](#link-types)
- [Priority and Severity](#priority-and-severity)
- [WIQL Query Examples](#wiql-query-examples)
- [Common Field Values](#common-field-values)

---

## Work Item Field Names

### System Fields (60+ validated fields)

#### Core System Fields

| Reference Name | Type | Description |
|----------------|------|-------------|
| `System.Id` | Integer | Unique work item ID (read-only) |
| `System.Title` | String | Work item title |
| `System.Description` | HTML | Detailed description |
| `System.WorkItemType` | String | Type (Bug, Task, User Story, etc.) |
| `System.State` | String | Current state (Active, Closed, etc.) |
| `System.Reason` | String | Reason for current state |
| `System.AssignedTo` | Identity | Person assigned to work item |
| `System.CreatedBy` | Identity | Person who created work item |
| `System.CreatedDate` | DateTime | Creation timestamp (read-only) |
| `System.ChangedBy` | Identity | Last person to modify (read-only) |
| `System.ChangedDate` | DateTime | Last modification timestamp (read-only) |
| `System.History` | History | Comment/history text |

#### Organization Fields

| Reference Name | Type | Description |
|----------------|------|-------------|
| `System.TeamProject` | String | Project name (read-only) |
| `System.AreaPath` | TreePath | Area path classification |
| `System.IterationPath` | TreePath | Iteration/sprint path |
| `System.Tags` | String | Semicolon-separated tags |

#### Board Fields

| Reference Name | Type | Description |
|----------------|------|-------------|
| `System.BoardColumn` | String | Kanban board column |
| `System.BoardColumnDone` | Boolean | Board column done status |
| `System.BoardLane` | String | Swimlane on board |

#### Workflow Fields

| Reference Name | Type | Description |
|----------------|------|-------------|
| `System.Rev` | Integer | Revision number (read-only) |
| `System.AuthorizedAs` | Identity | Authorized user (read-only) |
| `System.RevisedDate` | DateTime | Date revised (read-only) |
| `System.Watermark` | Integer | Internal watermark (read-only) |

---

### VSTS Common Fields

#### Priority and Ranking

| Reference Name | Type | Description | Values |
|----------------|------|-------------|--------|
| `Microsoft.VSTS.Common.Priority` | Integer | Priority level | 1-4 (1=highest) |
| `Microsoft.VSTS.Common.Severity` | String | Bug severity | 1-4 (1=critical) |
| `Microsoft.VSTS.Common.StackRank` | Double | Stack ranking for ordering | Any double |
| `Microsoft.VSTS.Common.BacklogPriority` | Double | Backlog priority | Any double |

#### Classification

| Reference Name | Type | Description | Values |
|----------------|------|-------------|--------|
| `Microsoft.VSTS.Common.ValueArea` | String | Value classification | Business, Architectural |
| `Microsoft.VSTS.Common.Risk` | String | Risk level | 1-High, 2-Medium, 3-Low |

#### State Management

| Reference Name | Type | Description |
|----------------|------|-------------|
| `Microsoft.VSTS.Common.StateChangeDate` | DateTime | Date state last changed |
| `Microsoft.VSTS.Common.ActivatedBy` | Identity | Person who activated |
| `Microsoft.VSTS.Common.ActivatedDate` | DateTime | Date activated |
| `Microsoft.VSTS.Common.ResolvedBy` | Identity | Person who resolved |
| `Microsoft.VSTS.Common.ResolvedDate` | DateTime | Date resolved |
| `Microsoft.VSTS.Common.ClosedBy` | Identity | Person who closed |
| `Microsoft.VSTS.Common.ClosedDate` | DateTime | Date closed |

---

### VSTS Scheduling Fields

#### Effort Tracking

| Reference Name | Type | Description |
|----------------|------|-------------|
| `Microsoft.VSTS.Scheduling.Effort` | Double | Effort estimate (generic) |
| `Microsoft.VSTS.Scheduling.StoryPoints` | Double | Story points (Scrum) |
| `Microsoft.VSTS.Scheduling.Size` | Double | Size estimate |

#### Time Tracking

| Reference Name | Type | Description |
|----------------|------|-------------|
| `Microsoft.VSTS.Scheduling.RemainingWork` | Double | Remaining work hours |
| `Microsoft.VSTS.Scheduling.CompletedWork` | Double | Completed work hours |
| `Microsoft.VSTS.Scheduling.OriginalEstimate` | Double | Original estimate hours |

#### Dates

| Reference Name | Type | Description |
|----------------|------|-------------|
| `Microsoft.VSTS.Scheduling.StartDate` | DateTime | Planned start date |
| `Microsoft.VSTS.Scheduling.FinishDate` | DateTime | Planned finish date |
| `Microsoft.VSTS.Scheduling.TargetDate` | DateTime | Target completion date |

---

### VSTS Bug-Specific Fields

| Reference Name | Type | Description |
|----------------|------|-------------|
| `Microsoft.VSTS.TCM.ReproSteps` | HTML | Steps to reproduce |
| `Microsoft.VSTS.TCM.SystemInfo` | HTML | System information |
| `Microsoft.VSTS.Build.FoundIn` | String | Build where bug was found |
| `Microsoft.VSTS.Build.IntegrationBuild` | String | Associated build |

---

### VSTS CMMI Fields

| Reference Name | Type | Description |
|----------------|------|-------------|
| `Microsoft.VSTS.CMMI.RequirementType` | String | Requirement type |
| `Microsoft.VSTS.CMMI.Analysis` | HTML | Analysis details |
| `Microsoft.VSTS.CMMI.UserAcceptanceTest` | String | User acceptance test |

---

## Work Item States

States vary by process template. Here are the most common states across templates:

### Universal States (All Templates)

| State | Description | Category |
|-------|-------------|----------|
| `New` | Just created, not started | Not Started |
| `Active` | Currently being worked on | In Progress |
| `Resolved` | Work complete, pending verification | In Progress |
| `Closed` | Verified and complete | Completed |
| `Removed` | Removed from backlog | Removed |

### Agile Process States

**User Story / Bug:**
- New
- Active
- Resolved
- Closed
- Removed

**Task:**
- New
- Active
- Closed
- Removed

**Epic / Feature:**
- New
- Active
- Resolved
- Closed

### Scrum Process States

**Product Backlog Item:**
- New
- Approved
- Committed
- Done
- Removed

**Task:**
- To Do
- In Progress
- Done
- Removed

**Bug:**
- New
- Approved
- Committed
- Done
- Removed

**Epic / Feature:**
- New
- In Progress
- Done
- Removed

### CMMI Process States

**Requirement:**
- Proposed
- Active
- Resolved
- Closed

**Task:**
- Proposed
- Active
- Resolved
- Closed

**Bug:**
- Proposed
- Active
- Resolved
- Closed

### Additional Common States

| State | Description |
|-------|-------------|
| `In Progress` | Actively being worked |
| `In Review` | Under review |
| `Committed` | Committed to sprint |
| `Done` | Completed |
| `Approved` | Approved by stakeholders |
| `Ready` | Ready to start |
| `To Do` | Planned but not started |
| `Complete` | Finished |
| `Open` | Open/active |

### State Categories

States are grouped into categories for completion tracking:

**Completed States:**
- Done
- Closed
- Resolved
- Completed

**In Progress States:**
- Active
- In Progress
- Committed
- In Review

**Not Started States:**
- New
- Proposed
- To Do
- Ready
- Approved

---

## Work Item Types

Types vary by process template.

### Agile Process

| Type | Level | Description |
|------|-------|-------------|
| `Epic` | 1 | Large feature spanning multiple sprints |
| `Feature` | 2 | Feature delivered over multiple sprints |
| `User Story` | 3 | User-facing functionality |
| `Task` | 4 | Unit of work |
| `Bug` | Any | Defect to fix |
| `Issue` | Any | Problem or impediment |
| `Test Case` | Any | Test scenario |

**Hierarchy:** Epic → Feature → User Story → Task

### Scrum Process

| Type | Level | Description |
|------|-------|-------------|
| `Epic` | 1 | Large initiative |
| `Feature` | 2 | Feature set |
| `Product Backlog Item` | 3 | User story equivalent |
| `Task` | 4 | Work item |
| `Bug` | Any | Defect |
| `Impediment` | Any | Blocker |
| `Test Case` | Any | Test |

**Hierarchy:** Epic → Feature → Product Backlog Item → Task

### CMMI Process

| Type | Level | Description |
|------|-------|-------------|
| `Epic` | 1 | Strategic initiative |
| `Feature` | 2 | Feature set |
| `Requirement` | 3 | Formal requirement |
| `Task` | 4 | Work item |
| `Bug` | Any | Defect |
| `Issue` | Any | Problem |
| `Risk` | Any | Risk item |
| `Review` | Any | Review item |
| `Test Case` | Any | Test |
| `Change Request` | Any | Change request |

**Hierarchy:** Epic → Feature → Requirement → Task

### Basic Process (Simplified)

| Type | Description |
|------|-------------|
| `Epic` | Large work item |
| `Issue` | Generic work item |
| `Task` | Task |

**Hierarchy:** Epic → Issue → Task

---

## Link Types

### Hierarchy Links

| Link Type | Direction | Description |
|-----------|-----------|-------------|
| `System.LinkTypes.Hierarchy-Forward` | Parent → Child | Epic to Features, Feature to Stories, etc. |
| `System.LinkTypes.Hierarchy-Reverse` | Child → Parent | Task to Story, Story to Feature, etc. |

**Usage:**
```python
# Get Epic's children (Features)
hierarchy = await get_work_item_hierarchy(
    work_item_id=100,
    link_type="System.LinkTypes.Hierarchy-Forward"
)

# Get Task's parent (Story)
parent = await get_work_item_hierarchy(
    work_item_id=1234,
    link_type="System.LinkTypes.Hierarchy-Reverse"
)
```

### Dependency Links

| Link Type | Direction | Description |
|-----------|-----------|-------------|
| `System.LinkTypes.Dependency-Forward` | This → Depends | What depends on this (Successor) |
| `System.LinkTypes.Dependency-Reverse` | Depends → This | What this depends on (Predecessor) |

**Usage:**
```python
# Get dependencies (what this item depends on)
deps = await get_work_item_hierarchy(
    work_item_id=1234,
    link_type="System.LinkTypes.Dependency-Reverse"
)

# Get dependents (what depends on this item)
dependents = await get_work_item_hierarchy(
    work_item_id=1234,
    link_type="System.LinkTypes.Dependency-Forward"
)
```

### Other Links

| Link Type | Description |
|-----------|-------------|
| `System.LinkTypes.Related` | Related work items |
| `System.LinkTypes.Duplicate` | Duplicate relationship |
| `System.LinkTypes.Successor` | Successor in sequence |
| `System.LinkTypes.Predecessor` | Predecessor in sequence |

---

## Priority and Severity

### Priority (1-4)

Higher priority = more urgent.

| Value | Label | Description |
|-------|-------|-------------|
| `1` | Critical | Immediate attention required |
| `2` | High | Important, schedule soon |
| `3` | Medium | Normal priority |
| `4` | Low | Can wait |

**Usage:**
```python
await update_work_item(
    work_item_id=1234,
    fields={"Microsoft.VSTS.Common.Priority": 1}
)
```

### Severity (1-4)

For bugs - higher severity = more severe impact.

| Value | Label | Description |
|-------|-------|-------------|
| `1` | Critical | System down, data loss |
| `2` | High | Major feature broken |
| `3` | Medium | Minor feature issue |
| `4` | Low | Cosmetic, minor annoyance |

**Usage:**
```python
await create_work_item(
    title="Database connection failure",
    work_item_type="Bug",
    fields={
        "Microsoft.VSTS.Common.Severity": 1,
        "Microsoft.VSTS.Common.Priority": 1
    }
)
```

---

## WIQL Query Examples

### Basic Queries

#### My Active Work Items

```sql
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.AssignedTo] = @Me
  AND [System.State] = 'Active'
ORDER BY [Microsoft.VSTS.Common.Priority] ASC
```

#### Work Created This Week

```sql
SELECT [System.Id], [System.Title], [System.CreatedBy]
FROM WorkItems
WHERE [System.TeamProject] = @project
  AND [System.CreatedDate] >= @Today-7
ORDER BY [System.CreatedDate] DESC
```

#### High Priority Bugs

```sql
SELECT [System.Id], [System.Title], [Microsoft.VSTS.Common.Priority]
FROM WorkItems
WHERE [System.WorkItemType] = 'Bug'
  AND [Microsoft.VSTS.Common.Priority] <= 2
  AND [System.State] <> 'Closed'
ORDER BY [Microsoft.VSTS.Common.Priority] ASC
```

### Sprint Queries

#### Current Sprint Work Items

```sql
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.IterationPath] = @CurrentIteration
  AND [System.TeamProject] = @project
ORDER BY [System.State] ASC, [Microsoft.VSTS.Common.StackRank] ASC
```

#### Sprint Burndown (Remaining Work)

```sql
SELECT [System.Id], [System.Title], [Microsoft.VSTS.Scheduling.RemainingWork]
FROM WorkItems
WHERE [System.IterationPath] = @CurrentIteration
  AND [System.WorkItemType] = 'Task'
  AND [System.State] <> 'Closed'
```

### Advanced Queries

#### Unassigned Work Items

```sql
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.AssignedTo] IS EMPTY
  AND [System.State] IN ('New', 'Active')
  AND [System.TeamProject] = @project
ORDER BY [System.CreatedDate] ASC
```

#### Overdue Work Items

```sql
SELECT [System.Id], [System.Title], [Microsoft.VSTS.Scheduling.TargetDate]
FROM WorkItems
WHERE [Microsoft.VSTS.Scheduling.TargetDate] < @Today
  AND [System.State] NOT IN ('Done', 'Closed')
ORDER BY [Microsoft.VSTS.Scheduling.TargetDate] ASC
```

#### Work Items Changed Recently

```sql
SELECT [System.Id], [System.Title], [System.ChangedDate], [System.ChangedBy]
FROM WorkItems
WHERE [System.ChangedDate] >= @Today-3
  AND [System.TeamProject] = @project
ORDER BY [System.ChangedDate] DESC
```

### Hierarchical Queries

#### Epic with Features

```sql
SELECT [System.Id], [System.Title], [System.WorkItemType]
FROM WorkItemLinks
WHERE ([Source].[System.WorkItemType] = 'Epic')
  AND ([System.Links.LinkType] = 'System.LinkTypes.Hierarchy-Forward')
  AND ([Target].[System.WorkItemType] = 'Feature')
MODE (Recursive)
```

#### Feature with Stories and Tasks

```sql
SELECT [System.Id], [System.Title], [System.WorkItemType], [System.State]
FROM WorkItemLinks
WHERE ([Source].[System.Id] = 100)
  AND ([System.Links.LinkType] = 'System.LinkTypes.Hierarchy-Forward')
MODE (Recursive, ReturnMatchingChildren)
```

#### Work Item Dependencies

```sql
SELECT [System.Id], [System.Title]
FROM WorkItemLinks
WHERE ([Source].[System.Id] = 1234)
  AND ([System.Links.LinkType] = 'System.LinkTypes.Dependency-Reverse')
MODE (MustContain)
```

### Search Queries

#### Full-Text Search (Indexed)

```sql
SELECT [System.Id], [System.Title]
FROM WorkItems
WHERE [System.Title] CONTAINS WORDS 'authentication login'
  AND [System.TeamProject] = @project
```

#### Tag Search

```sql
SELECT [System.Id], [System.Title], [System.Tags]
FROM WorkItems
WHERE [System.Tags] CONTAINS 'urgent'
  AND [System.State] <> 'Closed'
```

#### Historical State Query

```sql
SELECT [System.Id], [System.Title], [System.State]
FROM WorkItems
WHERE [System.State] WAS EVER 'Resolved'
  AND [System.WorkItemType] = 'Bug'
  AND [System.TeamProject] = @project
```

---

## Common Field Values

### System.State Values by Template

**Agile:**
- New, Active, Resolved, Closed, Removed

**Scrum:**
- New, Approved, Committed, Done, Removed
- To Do, In Progress (for Tasks)

**CMMI:**
- Proposed, Active, Resolved, Closed

**Common (across templates):**
- Active, In Progress, In Review, Ready, Done, Complete, Open

### System.WorkItemType Values

**All Templates:**
- Epic, Feature, Bug, Task, Test Case

**Agile:**
- User Story, Issue

**Scrum:**
- Product Backlog Item, Impediment

**CMMI:**
- Requirement, Risk, Review, Change Request

**Basic:**
- Issue (generic)

### Microsoft.VSTS.Common.ValueArea

- Business
- Architectural

### Microsoft.VSTS.Common.Risk

- 1 - High
- 2 - Medium
- 3 - Low

### System.Reason (varies by State and Type)

**For State "Active":**
- Approved
- Investigation Complete
- New
- Reopened

**For State "Resolved":**
- Fixed
- Fixed and verified
- Copy of work item made
- Deferred
- Duplicate
- Obsolete

**For State "Closed":**
- Fixed and verified
- Obsolete
- Copy of work item made
- Deferred
- Duplicate
- Fixed

---

## WIQL Macros Reference

| Macro | Description | Example |
|-------|-------------|---------|
| `@Me` | Current authenticated user | `[System.AssignedTo] = @Me` |
| `@Today` | Current date (midnight) | `[System.CreatedDate] >= @Today` |
| `@Today-{n}` | n days ago | `[System.CreatedDate] >= @Today-7` |
| `@Today+{n}` | n days from now | `[System.DueDate] <= @Today+3` |
| `@project` | Current project | `[System.TeamProject] = @project` |
| `@CurrentIteration` | Current team iteration | `[System.IterationPath] = @CurrentIteration` |
| `@CurrentIteration +/- n` | Relative iteration | `[System.IterationPath] = @CurrentIteration + 1` |

---

## Query Operators Reference

### Comparison Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `[System.State] = 'Active'` |
| `<>` | Not equals | `[System.State] <> 'Closed'` |
| `>` | Greater than | `[System.CreatedDate] > @Today-7` |
| `<` | Less than | `[Microsoft.VSTS.Common.Priority] < 3` |
| `>=` | Greater than or equal | `[System.ChangedDate] >= @Today` |
| `<=` | Less than or equal | `[Microsoft.VSTS.Scheduling.RemainingWork] <= 0` |

### String Operators

| Operator | Description | Performance | Example |
|----------|-------------|-------------|---------|
| `CONTAINS` | Substring match | Slow (table scan) | `[System.Title] CONTAINS 'login'` |
| `CONTAINS WORDS` | Full-text search | **Fast** (indexed) | `[System.Description] CONTAINS WORDS 'auth sso'` |
| `DOES NOT CONTAIN` | No substring | Slow | `[System.Title] DOES NOT CONTAIN 'test'` |
| `DOES NOT CONTAIN WORDS` | Exclude words | Fast | `[System.Title] DOES NOT CONTAIN WORDS 'draft'` |

### Set Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `IN` | Value in set | `[System.State] IN ('Active', 'Resolved', 'New')` |
| `NOT IN` | Value not in set | `[System.WorkItemType] NOT IN ('Epic', 'Feature')` |
| `IN GROUP` | User in group | `[System.AssignedTo] IN GROUP 'Developers'` |
| `NOT IN GROUP` | User not in group | `[System.CreatedBy] NOT IN GROUP 'External'` |

### Existence Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `IS EMPTY` | Field is empty/null | `[System.AssignedTo] IS EMPTY` |
| `IS NOT EMPTY` | Field has value | `[System.Description] IS NOT EMPTY` |
| `WAS EVER` | Historical value match | `[System.State] WAS EVER 'Active'` |

### Tree Path Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `UNDER` | Under path (including itself) | `[System.AreaPath] UNDER 'Project\\Team A'` |
| `NOT UNDER` | Not under path | `[System.IterationPath] NOT UNDER 'Project\\Archive'` |

---

## Field Data Types

| Data Type | Description | Example Values |
|-----------|-------------|----------------|
| `String` | Text string | "Fix login bug" |
| `Integer` | Whole number | 123, 1, 42 |
| `Double` | Decimal number | 3.5, 8.25 |
| `DateTime` | Date and time | "2025-01-20T14:30:00Z" |
| `Boolean` | True/False | true, false |
| `Identity` | User identity | "user@company.com" |
| `TreePath` | Hierarchical path | "Project\\Area\\SubArea" |
| `HTML` | Rich text HTML | "<p>Description</p>" |
| `History` | Historical comments | System-managed |

---

## Additional Resources

- **Azure DevOps REST API:** https://learn.microsoft.com/rest/api/azure/devops/
- **WIQL Syntax:** https://learn.microsoft.com/azure/devops/boards/queries/wiql-syntax
- **Work Item Customization:** https://learn.microsoft.com/azure/devops/organizations/settings/work/customize-process

---

**Version:** 2.1
**Last Updated:** 2025-11-15
