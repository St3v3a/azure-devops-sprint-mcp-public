#!/usr/bin/env python
"""Query current sprint and work items in detail"""
import asyncio
import os
from dotenv import load_dotenv
from src.auth import AzureDevOpsAuth
from src.services.sprint_service import SprintService
from src.services.workitem_service import WorkItemService

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
    sprint_service = SprintService(auth, project)
    workitem_service = WorkItemService(auth, project)

    # Get current sprint with work items
    print("=" * 70)
    print("📊 CURRENT SPRINT")
    print("=" * 70)

    current_sprint = await sprint_service.get_current_sprint()

    print(f"\n🏃 Sprint: {current_sprint['name']}")
    print(f"📅 Start: {current_sprint['start_date'] or 'Not set'}")
    print(f"📅 End: {current_sprint['end_date'] or 'Not set'}")
    if current_sprint['days_remaining']:
        print(f"⏰ Days Remaining: {current_sprint['days_remaining']}")

    print(f"\n📈 Progress:")
    print(f"  Total Items: {current_sprint['total_items']}")
    print(f"  ✅ Completed: {current_sprint['completed_items']}")
    print(f"  🔄 In Progress: {current_sprint['in_progress_items']}")
    print(f"  ⭕ Not Started: {current_sprint['not_started_items']}")
    print(f"  📊 Completion: {current_sprint['completion_percentage']:.1f}%")

    # Get detailed work items
    print(f"\n{'=' * 70}")
    print("📋 WORK ITEMS")
    print("=" * 70)

    sprint_details = await sprint_service.get_sprint_work_items()

    if sprint_details['work_items']:
        for idx, item in enumerate(sprint_details['work_items'], 1):
            print(f"\n{idx}. [{item['work_item_type']}] {item['title']}")
            print(f"   ID: {item['id']}")
            print(f"   State: {item['state']}")
            print(f"   Assigned To: {item['assigned_to'] or 'Unassigned'}")
            if item['priority']:
                print(f"   Priority: {item['priority']}")
            if item['remaining_work']:
                print(f"   Remaining Work: {item['remaining_work']} hours")
            print(f"   URL: {item['url']}")
    else:
        print("\n  No work items found in current sprint")

    # Get my work items
    print(f"\n{'=' * 70}")
    print("👤 MY WORK ITEMS")
    print("=" * 70)

    my_items = await workitem_service.get_my_work_items()

    if my_items:
        print(f"\n  You have {len(my_items)} work items assigned to you:\n")
        for idx, item in enumerate(my_items, 1):
            print(f"{idx}. [{item['work_item_type']}] {item['title']}")
            print(f"   ID: {item['id']}")
            print(f"   State: {item['state']}")
            if item['iteration_path']:
                print(f"   Sprint: {item['iteration_path'].split('\\')[-1]}")
    else:
        print("\n  No work items assigned to you")

    # Cleanup
    await auth.close()

    print(f"\n{'=' * 70}")
    print("✓ Query completed successfully!")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(main())
