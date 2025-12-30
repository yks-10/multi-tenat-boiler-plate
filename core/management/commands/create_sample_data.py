"""
Django management command to create sample tenants, users, projects, and tasks for testing.
Run with: python manage.py create_sample_data
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Tenant, User, Project, Task


class Command(BaseCommand):
    help = 'Creates sample tenants, users, projects, and tasks for testing the multi-tenant application'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating sample data...'))
        
        with transaction.atomic():
            # Create Tenants
            tenant1, _ = Tenant.objects.get_or_create(name="Acme Corp")
            tenant2, _ = Tenant.objects.get_or_create(name="TechStart Inc")
            self.stdout.write(f"✓ Created tenants: {tenant1.name}, {tenant2.name}")
            
            # Create Users
            user1, created = User.objects.get_or_create(
                username="tenant1user",
                defaults={
                    'email': 'user1@acme.com',
                    'tenant': tenant1,
                    'is_staff': False,
                    'is_superuser': False
                }
            )
            if created:
                user1.set_password('password123')
                user1.save()
            else:
                user1.tenant = tenant1
                user1.save()
            
            user2, created = User.objects.get_or_create(
                username="tenant2user",
                defaults={
                    'email': 'user2@techstart.com',
                    'tenant': tenant2,
                    'is_staff': False,
                    'is_superuser': False
                }
            )
            if created:
                user2.set_password('password123')
                user2.save()
            else:
                user2.tenant = tenant2
                user2.save()
            
            self.stdout.write(f"✓ Created user: {user1.username} (Tenant: {user1.tenant.name})")
            self.stdout.write(f"✓ Created user: {user2.username} (Tenant: {user2.tenant.name})")
            
            # Create admin user without tenant (for admin panel)
            admin, created = User.objects.get_or_create(
                username="admin",
                defaults={
                    'email': 'admin@example.com',
                    'is_staff': True,
                    'is_superuser': True
                }
            )
            if created:
                admin.set_password('admin123')
                admin.save()
            self.stdout.write(f"✓ Created admin: {admin.username}")
            
            # Create Projects for Tenant 1
            project1_1, _ = Project.objects.get_or_create(
                name="Website Redesign",
                tenant=tenant1
            )
            project1_2, _ = Project.objects.get_or_create(
                name="Mobile App Development",
                tenant=tenant1
            )
            
            # Create Projects for Tenant 2
            project2_1, _ = Project.objects.get_or_create(
                name="API Integration",
                tenant=tenant2
            )
            project2_2, _ = Project.objects.get_or_create(
                name="Database Migration",
                tenant=tenant2
            )
            
            self.stdout.write(f"\n✓ Created projects for {tenant1.name}:")
            self.stdout.write(f"  - {project1_1.name}")
            self.stdout.write(f"  - {project1_2.name}")
            self.stdout.write(f"\n✓ Created projects for {tenant2.name}:")
            self.stdout.write(f"  - {project2_1.name}")
            self.stdout.write(f"  - {project2_2.name}")
            
            # Create Tasks for Tenant 1 Projects
            Task.objects.get_or_create(
                title="Create wireframes",
                project=project1_1,
                tenant=tenant1,
                defaults={'is_done': True}
            )
            Task.objects.get_or_create(
                title="Design homepage",
                project=project1_1,
                tenant=tenant1,
                defaults={'is_done': False}
            )
            Task.objects.get_or_create(
                title="Setup development environment",
                project=project1_2,
                tenant=tenant1,
                defaults={'is_done': True}
            )
            Task.objects.get_or_create(
                title="Implement authentication",
                project=project1_2,
                tenant=tenant1,
                defaults={'is_done': False}
            )
            
            # Create Tasks for Tenant 2 Projects
            Task.objects.get_or_create(
                title="Review API documentation",
                project=project2_1,
                tenant=tenant2,
                defaults={'is_done': True}
            )
            Task.objects.get_or_create(
                title="Implement webhooks",
                project=project2_1,
                tenant=tenant2,
                defaults={'is_done': False}
            )
            Task.objects.get_or_create(
                title="Backup current database",
                project=project2_2,
                tenant=tenant2,
                defaults={'is_done': True}
            )
            Task.objects.get_or_create(
                title="Test migration scripts",
                project=project2_2,
                tenant=tenant2,
                defaults={'is_done': False}
            )
            
            self.stdout.write(self.style.SUCCESS('\n✅ Sample data created successfully!'))
            self.stdout.write('\nLogin credentials:')
            self.stdout.write('  Tenant 1: tenant1user / password123')
            self.stdout.write('  Tenant 2: tenant2user / password123')
            self.stdout.write('  Admin:    admin / admin123')
            self.stdout.write(self.style.WARNING('\nEach user can only see their own tenant\'s data!'))

