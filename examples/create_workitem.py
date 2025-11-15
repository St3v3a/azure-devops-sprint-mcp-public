#!/usr/bin/env python
"""Create a new work item"""
import asyncio
import os
from dotenv import load_dotenv
from src.auth import AzureDevOpsAuth
from src.services.workitem_service import WorkItemService
from src.services.sprint_service import SprintService

async def main():
    # Load environment
    load_dotenv()
    org_url = os.getenv('AZURE_DEVOPS_ORG_URL')
    project = os.getenv('AZURE_DEVOPS_PROJECT')

    print(f"🔗 Organization: {org_url}")
    print(f"📁 Project: {project}\n")

    # Initialize auth
    auth = AzureDevOpsAuth(org_url)
    await auth.initialize()

    # Initialize services
    workitem_service = WorkItemService(auth, project)
    sprint_service = SprintService(auth, project)

    # Get current sprint path
    current_sprint = await sprint_service.get_current_sprint()
    iteration_path = current_sprint['path']

    print(f"📋 Creating work item in sprint: {current_sprint['name']}\n")

    # Create the work item
    result = await workitem_service.create_work_item(
        title="test-mcp",
        work_item_type="Task",
        description="Test work item created via MCP server",
        iteration_path=iteration_path,
        priority=3
    )

    print("✓ Work item created successfully!\n")
    print(f"  ID: {result['id']}")
    print(f"  Title: {result['title']}")
    print(f"  Type: {result['work_item_type']}")
    print(f"  State: {result['state']}")
    print(f"  Sprint: {result['iteration_path'].split('\\')[-1] if result['iteration_path'] else 'None'}")
    print(f"  Priority: {result['priority']}")
    print(f"  URL: {result['url']}")

    # Cleanup
    await auth.close()

if __name__ == '__main__':
    asyncio.run(main())
