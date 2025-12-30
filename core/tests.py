from django.test import TestCase, Client
from django.urls import reverse
from core.models import Tenant, User, Project, Task
from core.managers import set_current_tenant, clear_current_tenant


class TenantIsolationTests(TestCase):
    """Test cases to verify tenant data isolation."""
    
    def setUp(self):
        """Set up test tenants and users."""
        # Create tenants
        self.tenant1 = Tenant.objects.create(name="Test Tenant 1")
        self.tenant2 = Tenant.objects.create(name="Test Tenant 2")
        
        # Create users
        self.user1 = User.objects.create_user(
            username='testuser1',
            password='testpass123',
            email='user1@test.com',
            tenant=self.tenant1
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            password='testpass123',
            email='user2@test.com',
            tenant=self.tenant2
        )
        
        # Create projects for each tenant
        set_current_tenant(self.tenant1)
        self.project1 = Project.objects.create(name="Project 1", tenant=self.tenant1)
        
        set_current_tenant(self.tenant2)
        self.project2 = Project.objects.create(name="Project 2", tenant=self.tenant2)
        
        clear_current_tenant()
        
    def tearDown(self):
        """Clean up after tests."""
        clear_current_tenant()
    
    def test_user_can_only_see_own_tenant_projects(self):
        """Test that users can only see projects from their own tenant."""
        # Login as user1
        self.client.login(username='testuser1', password='testpass123')
        
        # Access dashboard
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Check that only tenant1's project is visible
        self.assertContains(response, "Project 1")
        self.assertNotContains(response, "Project 2")
    
    def test_user_cannot_access_other_tenant_project(self):
        """Test that users get 404 when trying to access another tenant's project."""
        # Login as user1
        self.client.login(username='testuser1', password='testpass123')
        
        # Try to access project2 (belongs to tenant2)
        response = self.client.get(
            reverse('core:project_detail', kwargs={'project_id': self.project2.id})
        )
        
        # Should get 404 because project belongs to different tenant
        self.assertEqual(response.status_code, 404)
    
    def test_project_create_automatically_sets_tenant(self):
        """Test that creating a project automatically sets the correct tenant."""
        # Login as user1
        self.client.login(username='testuser1', password='testpass123')
        
        # Create a project via HTMX
        response = self.client.post(
            reverse('core:project_create'),
            {'name': 'New Project'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify project was created with correct tenant
        new_project = Project.objects.get(name='New Project')
        self.assertEqual(new_project.tenant, self.tenant1)
    
    def test_task_isolation(self):
        """Test that tasks are also isolated by tenant."""
        # Create tasks for each project
        set_current_tenant(self.tenant1)
        task1 = Task.objects.create(
            title="Task 1",
            project=self.project1,
            tenant=self.tenant1
        )
        
        set_current_tenant(self.tenant2)
        task2 = Task.objects.create(
            title="Task 2",
            project=self.project2,
            tenant=self.tenant2
        )
        
        clear_current_tenant()
        
        # Login as user1
        self.client.login(username='testuser1', password='testpass123')
        
        # Access project1's detail page
        response = self.client.get(
            reverse('core:project_detail', kwargs={'project_id': self.project1.id})
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Task 1")
        self.assertNotContains(response, "Task 2")
    
    def test_search_respects_tenant_boundaries(self):
        """Test that search only returns results from current tenant."""
        # Login as user1
        self.client.login(username='testuser1', password='testpass123')
        
        # Search for "Project" (both projects have this in the name)
        response = self.client.get(
            reverse('core:search') + '?q=Project',
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project 1")
        self.assertNotContains(response, "Project 2")
    
    def test_unauthenticated_user_redirected_to_login(self):
        """Test that unauthenticated users are redirected to login."""
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_user_without_tenant_gets_403(self):
        """Test that users without a tenant cannot access tenant views."""
        # Create user without tenant
        user_no_tenant = User.objects.create_user(
            username='notenant',
            password='testpass123',
            email='notenant@test.com'
        )
        
        # Login
        self.client.login(username='notenant', password='testpass123')
        
        # Try to access dashboard
        response = self.client.get(reverse('core:dashboard'))
        self.assertEqual(response.status_code, 403)


class TenantManagerTests(TestCase):
    """Test cases for the custom TenantManager and TenantQuerySet."""
    
    def setUp(self):
        """Set up test tenants and projects."""
        self.tenant1 = Tenant.objects.create(name="Tenant 1")
        self.tenant2 = Tenant.objects.create(name="Tenant 2")
        
        set_current_tenant(self.tenant1)
        self.project1 = Project.objects.create(name="Project 1", tenant=self.tenant1)
        
        set_current_tenant(self.tenant2)
        self.project2 = Project.objects.create(name="Project 2", tenant=self.tenant2)
        
        clear_current_tenant()
    
    def tearDown(self):
        """Clean up after tests."""
        clear_current_tenant()
    
    def test_queryset_automatically_filters_by_tenant(self):
        """Test that querysets automatically filter by current tenant."""
        set_current_tenant(self.tenant1)
        
        # Query should only return tenant1's projects
        projects = list(Project.objects.all())
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0], self.project1)
        
        clear_current_tenant()
    
    def test_create_automatically_sets_tenant(self):
        """Test that creating objects automatically sets the tenant."""
        set_current_tenant(self.tenant1)
        
        project = Project.objects.create(name="New Project")
        
        self.assertEqual(project.tenant, self.tenant1)
        
        clear_current_tenant()
    
    def test_without_tenant_filter(self):
        """Test that without_tenant_filter returns all objects."""
        set_current_tenant(self.tenant1)
        
        # Normal query returns only tenant1's projects
        filtered = list(Project.objects.all())
        self.assertEqual(len(filtered), 1)
        
        # Unfiltered query returns all projects
        unfiltered = list(Project.objects.without_tenant_filter().all())
        self.assertEqual(len(unfiltered), 2)
        
        clear_current_tenant()
    
    def test_for_tenant_method(self):
        """Test the for_tenant method for cross-tenant queries."""
        set_current_tenant(self.tenant1)
        
        # Query for tenant2's projects while tenant1 is current
        projects = list(Project.objects.for_tenant(self.tenant2))
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0], self.project2)
        
        clear_current_tenant()


class HTMXViewTests(TestCase):
    """Test cases for HTMX-specific view functionality."""
    
    def setUp(self):
        """Set up test tenant and user."""
        self.tenant = Tenant.objects.create(name="Test Tenant")
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            tenant=self.tenant
        )
        self.client.login(username='testuser', password='testpass123')
        
        set_current_tenant(self.tenant)
        self.project = Project.objects.create(name="Test Project", tenant=self.tenant)
        clear_current_tenant()
    
    def test_htmx_required_decorator(self):
        """Test that @htmx_required views reject non-HTMX requests."""
        # Try to access HTMX-only view without HX-Request header
        response = self.client.get(reverse('core:project_create'))
        self.assertEqual(response.status_code, 400)
        
        # With HX-Request header should work
        response = self.client.get(
            reverse('core:project_create'),
            HTTP_HX_REQUEST='true'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_htmx_partial_templates(self):
        """Test that HTMX requests return partial templates."""
        response = self.client.get(
            reverse('core:project_create'),
            HTTP_HX_REQUEST='true'
        )
        
        # Should return the form partial
        self.assertContains(response, '<form')
        # Should not contain full HTML structure
        self.assertNotContains(response, '<!DOCTYPE html>')
    
    def test_project_create_returns_hx_trigger(self):
        """Test that successful creates return HX-Trigger header."""
        response = self.client.post(
            reverse('core:project_create'),
            {'name': 'New Project'},
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        self.assertEqual(response.headers['HX-Trigger'], 'projectCreated')
    
    def test_task_toggle(self):
        """Test toggling task completion status via HTMX."""
        set_current_tenant(self.tenant)
        task = Task.objects.create(
            title="Test Task",
            project=self.project,
            tenant=self.tenant,
            is_done=False
        )
        clear_current_tenant()
        
        # Toggle task
        response = self.client.post(
            reverse('core:task_toggle', kwargs={'task_id': task.id}),
            HTTP_HX_REQUEST='true'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Check task was toggled
        task.refresh_from_db()
        self.assertTrue(task.is_done)

