#!/usr/bin/env python
"""
Demo script showing tenant-safe operations in Django shell.

Run with: python manage.py shell < demo_tenant_operations.py

This script demonstrates:
1. How tenant filtering works automatically
2. How to create tenant-scoped data
3. How to perform cross-tenant queries safely
4. Common patterns and best practices
"""

from core.models import Tenant, User, Project, Task
from core.managers import set_current_tenant, clear_current_tenant, get_current_tenant

print("=" * 70)
print("Multi-Tenant Django Demo")
print("=" * 70)

# Get existing tenants (or create new ones)
tenant1 = Tenant.objects.filter(name="Acme Corp").first()
tenant2 = Tenant.objects.filter(name="TechStart Inc").first()

if not tenant1 or not tenant2:
    print("\n⚠️  Please run 'python manage.py create_sample_data' first!")
    exit(1)

print(f"\nTenants in system:")
print(f"  1. {tenant1.name} (ID: {tenant1.id})")
print(f"  2. {tenant2.name} (ID: {tenant2.id})")

# ============================================================================
# Demo 1: Automatic Tenant Filtering
# ============================================================================
print("\n" + "=" * 70)
print("DEMO 1: Automatic Tenant Filtering")
print("=" * 70)

print("\n📋 Without setting tenant context:")
print(f"   get_current_tenant() = {get_current_tenant()}")
print(f"   Project.objects.all().count() = {Project.objects.all().count()}")
print("   (Returns all projects when no tenant is set)")

print("\n🔒 Setting tenant context to Acme Corp...")
set_current_tenant(tenant1)
print(f"   get_current_tenant() = {get_current_tenant()}")
tenant1_projects = Project.objects.all()
print(f"   Project.objects.all().count() = {tenant1_projects.count()}")
print("\n   Projects visible:")
for proj in tenant1_projects:
    print(f"     - {proj.name} (Tenant: {proj.tenant.name})")

print("\n🔒 Switching tenant context to TechStart Inc...")
set_current_tenant(tenant2)
print(f"   get_current_tenant() = {get_current_tenant()}")
tenant2_projects = Project.objects.all()
print(f"   Project.objects.all().count() = {tenant2_projects.count()}")
print("\n   Projects visible:")
for proj in tenant2_projects:
    print(f"     - {proj.name} (Tenant: {proj.tenant.name})")

clear_current_tenant()

# ============================================================================
# Demo 2: Creating Tenant-Scoped Data
# ============================================================================
print("\n" + "=" * 70)
print("DEMO 2: Creating Tenant-Scoped Data")
print("=" * 70)

print("\n📝 Creating a new project for Acme Corp...")
set_current_tenant(tenant1)

# Create project - tenant is automatically set!
new_project = Project.objects.create(name="Demo Project - Acme")
print(f"   Created: {new_project.name}")
print(f"   Tenant automatically set to: {new_project.tenant.name}")

# Create some tasks for the project
task1 = Task.objects.create(
    title="Design mockups",
    project=new_project,
    is_done=False
)
print(f"\n   Created task: {task1.title}")
print(f"   Task tenant automatically set to: {task1.tenant.name}")

task2 = Task.objects.create(
    title="Review requirements",
    project=new_project,
    is_done=True
)
print(f"   Created task: {task2.title}")
print(f"   Task tenant automatically set to: {task2.tenant.name}")

clear_current_tenant()

# ============================================================================
# Demo 3: Safe Cross-Tenant Queries
# ============================================================================
print("\n" + "=" * 70)
print("DEMO 3: Safe Cross-Tenant Queries")
print("=" * 70)

set_current_tenant(tenant1)

print("\n🔍 Current tenant: Acme Corp")
print(f"   Filtered query: Project.objects.all().count() = {Project.objects.all().count()}")

print("\n🔓 Using without_tenant_filter() [USE WITH CAUTION!]:")
all_projects = Project.objects.without_tenant_filter().all()
print(f"   Project.objects.without_tenant_filter().all().count() = {all_projects.count()}")
print("\n   All projects across all tenants:")
for proj in all_projects:
    print(f"     - {proj.name} (Tenant: {proj.tenant.name})")

print("\n🎯 Using for_tenant() for specific cross-tenant query:")
tenant2_projects_explicit = Project.objects.for_tenant(tenant2)
print(f"   Project.objects.for_tenant(tenant2).count() = {tenant2_projects_explicit.count()}")
print("\n   TechStart Inc projects (queried from Acme Corp context):")
for proj in tenant2_projects_explicit:
    print(f"     - {proj.name} (Tenant: {proj.tenant.name})")

clear_current_tenant()

# ============================================================================
# Demo 4: QuerySet Chaining
# ============================================================================
print("\n" + "=" * 70)
print("DEMO 4: QuerySet Chaining with Tenant Filtering")
print("=" * 70)

set_current_tenant(tenant1)

print("\n🔗 Tenant filtering works with all QuerySet operations:")

# Filter
print(f"   Project.objects.filter(name__contains='Demo').count() = ", end="")
print(Project.objects.filter(name__contains='Demo').count())

# Get (safe - returns 404 if wrong tenant)
try:
    demo_proj = Project.objects.get(name__contains='Demo')
    print(f"   Project.objects.get(name__contains='Demo') = {demo_proj.name}")
except Project.MultipleObjectsReturned:
    print("   Multiple projects found (this is expected)")
except Project.DoesNotExist:
    print("   No matching project found")

# Count tasks
all_tasks = Task.objects.all()
print(f"\n   All tasks for current tenant: {all_tasks.count()}")
completed_tasks = Task.objects.filter(is_done=True)
print(f"   Completed tasks: {completed_tasks.count()}")
pending_tasks = Task.objects.filter(is_done=False)
print(f"   Pending tasks: {pending_tasks.count()}")

clear_current_tenant()

# ============================================================================
# Demo 5: Model Save() Method
# ============================================================================
print("\n" + "=" * 70)
print("DEMO 5: Model save() Method with Tenant Auto-Assignment")
print("=" * 70)

set_current_tenant(tenant2)

print("\n💾 Creating project instance without explicit tenant...")
project_obj = Project(name="Demo Project - TechStart")
print(f"   Before save - tenant: {project_obj.tenant}")

print("\n   Calling save()...")
project_obj.save()
print(f"   After save - tenant: {project_obj.tenant.name}")
print("   ✅ Tenant was automatically assigned!")

clear_current_tenant()

# ============================================================================
# Demo 6: Bulk Operations
# ============================================================================
print("\n" + "=" * 70)
print("DEMO 6: Bulk Operations")
print("=" * 70)

set_current_tenant(tenant1)

print("\n📦 Creating multiple tasks using bulk_create...")
project_for_bulk = Project.objects.first()
print(f"   Project: {project_for_bulk.name}")

tasks_to_create = [
    Task(title=f"Bulk Task {i}", project=project_for_bulk, is_done=False)
    for i in range(1, 4)
]

created_tasks = Task.objects.bulk_create(tasks_to_create)
print(f"   Created {len(created_tasks)} tasks")

# Verify tenant was set automatically
for task in created_tasks:
    task.refresh_from_db()
    print(f"     - {task.title} (Tenant: {task.tenant.name})")

clear_current_tenant()

# ============================================================================
# Demo 7: Security - Attempting Cross-Tenant Access
# ============================================================================
print("\n" + "=" * 70)
print("DEMO 7: Security - Cross-Tenant Access Protection")
print("=" * 70)

# Get a project from tenant2
set_current_tenant(tenant2)
tenant2_project = Project.objects.first()
tenant2_project_id = tenant2_project.id
print(f"\n📌 Found project in TechStart Inc: {tenant2_project.name} (ID: {tenant2_project_id})")

# Try to access it from tenant1 context
print("\n🔒 Switching to Acme Corp context...")
set_current_tenant(tenant1)

print(f"   Attempting: Project.objects.get(id={tenant2_project_id})")
try:
    Project.objects.get(id=tenant2_project_id)
    print("   ❌ ERROR: Should not be able to access this!")
except Project.DoesNotExist:
    print("   ✅ SUCCESS: Correctly blocked cross-tenant access!")
    print("   (Raises DoesNotExist as if the project doesn't exist)")

clear_current_tenant()

# ============================================================================
# Cleanup and Summary
# ============================================================================
print("\n" + "=" * 70)
print("Summary")
print("=" * 70)

print("\n✅ Key Takeaways:")
print("   1. Tenant filtering happens automatically on all queries")
print("   2. set_current_tenant() sets the context for the current thread")
print("   3. Objects created automatically get the current tenant")
print("   4. Cross-tenant access is blocked by default (DoesNotExist)")
print("   5. Use without_tenant_filter() only when absolutely necessary")
print("   6. Use for_tenant() for safe cross-tenant queries")
print("   7. Always clear_current_tenant() when done")

print("\n🔒 Security Features:")
print("   ✓ Automatic query filtering at ORM level")
print("   ✓ Thread-local storage for tenant context")
print("   ✓ Tenant auto-assignment on create")
print("   ✓ Protection against accidental cross-tenant access")
print("   ✓ Clean separation of tenant data")

print("\n" + "=" * 70)
print("Demo Complete!")
print("=" * 70)

# Clean up
clear_current_tenant()

