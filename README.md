# Multi-Tenant SaaS Application

A production-ready Django-based multi-tenant SaaS application demonstrating secure tenant isolation, automatic data filtering, and modern web development practices with HTMX.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Multi-Tenant Implementation](#multi-tenant-implementation)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Security Features](#security-features)
- [API Routes](#api-routes)
- [Development](#development)
- [Demo Scripts](#demo-scripts)
- [Technology Stack](#technology-stack)

## 🎯 Overview

This is a fully functional multi-tenant SaaS application built with Django 6.0 that demonstrates enterprise-grade tenant isolation patterns. The application provides a project and task management system where each tenant's data is completely isolated from other tenants at the database query level.

**Key Highlights:**
- **Automatic Tenant Filtering**: All database queries are automatically filtered by the current tenant
- **Thread-Safe**: Uses thread-local storage for tenant context management
- **Modern UI**: Built with HTMX for dynamic interactions without page reloads
- **Security First**: Multiple layers of protection against cross-tenant data leakage
- **Production Ready**: Includes proper middleware, managers, and error handling

## ✨ Features

### Multi-Tenancy
- **Automatic tenant filtering** on all database queries
- **Thread-local tenant context** for request isolation
- **Custom QuerySet and Manager** for transparent tenant filtering
- **Safe cross-tenant queries** with explicit methods
- **Tenant auto-assignment** on object creation

### Project Management
- Create, read, update, and delete projects
- Projects automatically scoped to current tenant
- Search functionality across projects
- Real-time updates with HTMX

### Task Management
- Create and manage tasks within projects
- Toggle task completion status
- Edit and delete tasks
- All operations are tenant-aware

### User Authentication
- Custom user model with tenant association
- Secure login/logout functionality
- Per-tenant user isolation
- Admin panel access for superusers

### Modern UI/UX
- Tailwind CSS for beautiful, responsive design
- HTMX for seamless dynamic interactions
- No page reloads for CRUD operations
- Smooth animations and transitions

## 🏗️ Architecture

### Multi-Tenant Architecture Pattern

This application implements a **Shared Database with Tenant Column** pattern:

```
┌─────────────────────────────────────────────┐
│           Application Layer                  │
│  (Django Views, HTMX Frontend)              │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│        TenantMiddleware                      │
│  • Sets tenant from authenticated user      │
│  • Stores in thread-local storage           │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│     Custom Manager & QuerySet               │
│  • TenantManager: Overrides create()        │
│  • TenantQuerySet: Filters all queries      │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│          Database Layer                      │
│  ┌──────────────────────────────────────┐  │
│  │  Tenant A Data  │  Tenant B Data      │  │
│  │  Projects/Tasks │  Projects/Tasks     │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### Request Flow

1. **User Authentication**: User logs in with credentials
2. **Middleware Processing**: `TenantMiddleware` extracts tenant from user and stores in thread-local
3. **View Execution**: View processes request with automatic tenant context
4. **Query Filtering**: All database queries automatically filtered by tenant
5. **Response**: Only tenant-specific data returned
6. **Cleanup**: Middleware clears tenant context after response

## 🔐 Multi-Tenant Implementation

### Core Components

#### 1. Thread-Local Storage (`managers.py`)

```python
_thread_locals = local()

def get_current_tenant():
    """Get the current tenant from thread-local storage."""
    return getattr(_thread_locals, 'tenant', None)

def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage."""
    _thread_locals.tenant = tenant
```

#### 2. Custom QuerySet

The `TenantQuerySet` automatically filters all queries:

- **`all()`**: Applies tenant filtering
- **`filter()`**: Adds tenant to existing filters
- **`get()`**: Ensures tenant is included in lookup
- **`create()`**: Auto-assigns current tenant
- **`update()`**: Prevents tenant changes
- **`delete()`**: Only deletes tenant-scoped records

**Special Methods:**
- `without_tenant_filter()`: Bypass filtering (use with caution!)
- `for_tenant(tenant)`: Query specific tenant explicitly

#### 3. Custom Manager

The `TenantManager` provides high-level operations:

```python
class TenantManager(models.Manager):
    def get_queryset(self):
        return TenantQuerySet(self.model, using=self._db)
    
    def create(self, **kwargs):
        # Auto-assigns tenant if not specified
        tenant = get_current_tenant()
        if tenant and 'tenant' not in kwargs:
            kwargs['tenant'] = tenant
        return super().create(**kwargs)
```

#### 4. Model Mixin

The `TenantModelMixin` adds tenant awareness to models:

```python
class TenantModelMixin:
    objects = TenantManager()
    
    def save(self, *args, **kwargs):
        # Auto-assign tenant on creation
        if self.pk is None and self.tenant is None:
            self.tenant = get_current_tenant()
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Verify tenant before deletion
        current = get_current_tenant()
        if current and self.tenant != current:
            raise ValueError("Cross-tenant deletion prevented")
        return super().delete(*args, **kwargs)
```

#### 5. Middleware

The `TenantMiddleware` manages tenant context per request:

```python
class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if request.user.is_authenticated:
            request.tenant = request.user.tenant
            set_current_tenant(request.user.tenant)
        else:
            request.tenant = None
            clear_current_tenant()
    
    def process_response(self, request, response):
        clear_current_tenant()
        return response
```

### Data Models

```python
# Tenant Model
class Tenant(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

# User Model (extends AbstractUser)
class User(AbstractUser):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

# Project Model (tenant-scoped)
class Project(TenantModelMixin, models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)

# Task Model (tenant-scoped)
class Task(TenantModelMixin, models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    is_done = models.BooleanField(default=False)
```

## 📁 Project Structure

```
saas_app/
├── core/                           # Main application
│   ├── management/
│   │   └── commands/
│   │       └── create_sample_data.py   # Sample data generator
│   ├── migrations/                 # Database migrations
│   ├── templates/
│   │   └── core/
│   │       ├── base.html           # Base template
│   │       ├── dashboard.html      # Main dashboard
│   │       ├── login.html          # Login page
│   │       ├── project_detail.html # Project detail view
│   │       └── partials/           # HTMX partial templates
│   │           ├── project_form.html
│   │           ├── project_row.html
│   │           ├── task_form.html
│   │           ├── task_row.html
│   │           └── search_results.html
│   ├── admin.py                    # Django admin configuration
│   ├── managers.py                 # Custom managers and querysets
│   ├── middleware.py               # Tenant middleware
│   ├── models.py                   # Data models
│   ├── urls.py                     # URL routing
│   └── views.py                    # View functions
├── saas_app/                       # Project configuration
│   ├── settings.py                 # Django settings
│   ├── urls.py                     # Root URL configuration
│   └── wsgi.py                     # WSGI configuration
├── demo_tenant_operations.py       # Tenant operations demo
├── manage.py                       # Django management script
└── requirements.txt                # Python dependencies
```

## 🚀 Installation

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- SQLite (included with Python)

### Setup Steps

1. **Clone or navigate to the project directory**

```bash
cd saas_app
```

2. **Create a virtual environment** (recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Run migrations**

```bash
python manage.py migrate
```

5. **Create sample data**

```bash
python manage.py create_sample_data
```

This creates:
- 2 tenants: "Acme Corp" and "TechStart Inc"
- 3 users:
  - `tenant1user` / `password123` (Acme Corp)
  - `tenant2user` / `password123` (TechStart Inc)
  - `admin` / `admin123` (Superuser, no tenant)
- Sample projects and tasks for each tenant

6. **Run the development server**

```bash
python manage.py runserver
```

7. **Access the application**

Open your browser to `http://127.0.0.1:8000/`

## 📖 Usage

### Login

Navigate to `http://127.0.0.1:8000/login/` and use one of the sample credentials:

- **Tenant 1 User**: `tenant1user` / `password123`
- **Tenant 2 User**: `tenant2user` / `password123`
- **Admin**: `admin` / `admin123`

### Dashboard

After logging in, you'll see:
- **Statistics**: Overview of projects and current tenant
- **Project List**: All projects for your tenant
- **Actions**: Create, edit, delete projects

### Project Management

**Create a Project:**
1. Click "New Project" button
2. Enter project name
3. Submit (HTMX updates the list dynamically)

**Edit a Project:**
1. Click "Edit" on any project
2. Modify the name
3. Submit to update

**Delete a Project:**
1. Click "Delete" on any project
2. Confirm the deletion
3. Project is removed instantly

### Task Management

**View Project Tasks:**
1. Click "View Tasks" on any project
2. See all tasks for that project

**Create a Task:**
1. In project detail view, click "New Task"
2. Enter task title
3. Submit to create

**Toggle Task Status:**
1. Click the checkbox next to any task
2. Status updates immediately

**Edit/Delete Tasks:**
1. Use the Edit or Delete buttons on each task
2. Changes are reflected instantly

### Search

Use the search functionality to find projects and tasks by name/title across your tenant's data.

## 🔒 Security Features

### 1. Automatic Query Filtering

All database queries are automatically filtered by tenant:

```python
# This query only returns Tenant A's projects if Tenant A is logged in
projects = Project.objects.all()
```

### 2. Cross-Tenant Access Prevention

Attempting to access another tenant's data raises `DoesNotExist`:

```python
# If Tenant A tries to access Tenant B's project by ID
project = Project.objects.get(id=tenant_b_project_id)
# Raises: Project.DoesNotExist
```

### 3. Automatic Tenant Assignment

Objects automatically get the current tenant:

```python
# Tenant is automatically set to current user's tenant
project = Project.objects.create(name="My Project")
print(project.tenant)  # Current tenant
```

### 4. Deletion Protection

Cannot delete objects from other tenants:

```python
# Trying to delete a different tenant's object
other_tenant_project.delete()
# Raises: ValueError("Cross-tenant deletion prevented")
```

### 5. Update Protection

Cannot change tenant through update operations:

```python
# This is prevented
Project.objects.filter(id=1).update(tenant=other_tenant)
# Raises: ValueError("Cannot change tenant through update()")
```

### 6. Thread-Local Isolation

Each request has its own isolated tenant context using thread-local storage, preventing cross-contamination in concurrent requests.

### 7. Middleware Cleanup

Tenant context is always cleared after request processing, even on exceptions.

## 🛣️ API Routes

### Authentication

| Method | Route | Description |
|--------|-------|-------------|
| GET/POST | `/login/` | User login |
| POST | `/logout/` | User logout |

### Dashboard

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Main dashboard |

### Projects

| Method | Route | Description | HTMX |
|--------|-------|-------------|------|
| GET | `/projects/` | List all projects | ✓ |
| POST | `/projects/create/` | Create new project | ✓ |
| GET | `/projects/<id>/` | View project details | ✓ |
| POST | `/projects/<id>/edit/` | Edit project | ✓ |
| DELETE | `/projects/<id>/delete/` | Delete project | ✓ |

### Tasks

| Method | Route | Description | HTMX |
|--------|-------|-------------|------|
| POST | `/projects/<id>/tasks/create/` | Create task | ✓ |
| POST | `/tasks/<id>/toggle/` | Toggle completion | ✓ |
| POST | `/tasks/<id>/edit/` | Edit task | ✓ |
| DELETE | `/tasks/<id>/delete/` | Delete task | ✓ |

### Search

| Method | Route | Description | HTMX |
|--------|-------|-------------|------|
| GET | `/search/?q=<query>` | Search projects/tasks | ✓ |

**Note**: Routes marked with ✓ in HTMX column require HTMX headers and return HTML partials.

## 🛠️ Development

### Adding a New Tenant-Scoped Model

1. **Define the model with TenantModelMixin:**

```python
from core.managers import TenantModelMixin

class MyModel(TenantModelMixin, models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    # ... other fields
```

2. **Run migrations:**

```bash
python manage.py makemigrations
python manage.py migrate
```

3. **Use in views** (automatic filtering applies):

```python
@login_required
@tenant_check
def my_view(request):
    # Automatically filtered by current tenant
    my_objects = MyModel.objects.all()
    return render(request, 'template.html', {'objects': my_objects})
```

### Custom Decorators

The application provides useful decorators:

**`@tenant_check`**: Ensures user has a tenant before accessing view
```python
@login_required
@tenant_check
def my_view(request):
    # request.tenant is guaranteed to exist
    pass
```

**`@htmx_required`**: Ensures request is from HTMX
```python
@htmx_required
def my_htmx_view(request):
    # Only accepts HTMX requests
    return render(request, 'partials/my_partial.html')
```

### Testing Tenant Isolation

Use the included demo script:

```bash
python manage.py shell < demo_tenant_operations.py
```

This demonstrates:
- Automatic tenant filtering
- Creating tenant-scoped data
- Cross-tenant query protection
- Safe cross-tenant queries
- Bulk operations
- Security features

## 🎬 Demo Scripts

### 1. Create Sample Data

```bash
python manage.py create_sample_data
```

Creates tenants, users, projects, and tasks for testing.

### 2. Tenant Operations Demo

```bash
python manage.py shell < demo_tenant_operations.py
```

Interactive demonstration of:
- How tenant filtering works
- Creating tenant-scoped objects
- Cross-tenant access prevention
- QuerySet operations with tenant filtering
- Bulk operations
- Security features

**Demo Output Includes:**
- ✅ Automatic filtering examples
- ✅ Tenant context switching
- ✅ Security demonstrations
- ✅ Best practices
- ✅ Common patterns

## 🧰 Technology Stack

### Backend
- **Django 6.0**: Web framework
- **Python 3.10+**: Programming language
- **SQLite**: Database (easily swappable with PostgreSQL, MySQL, etc.)

### Frontend
- **HTMX**: Dynamic HTML updates without JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Alpine.js** (optional): Minimal JavaScript framework

### Key Libraries
- **asgiref 3.11.0**: ASGI utilities
- **sqlparse 0.5.5**: SQL parsing and formatting

### Architecture Patterns
- **Multi-tenancy**: Shared database with tenant column
- **Thread-local storage**: Request-scoped tenant context
- **Custom QuerySet/Manager**: Transparent query filtering
- **Middleware**: Request/response processing
- **HTMX**: Server-side rendering with dynamic updates

## 🧪 Testing

### Manual Testing Steps

1. **Login as Tenant 1 User**
   - Create projects and tasks
   - Note the project IDs

2. **Logout and Login as Tenant 2 User**
   - Verify you cannot see Tenant 1's projects
   - Try accessing Tenant 1's project by direct URL (should get 404)

3. **Test CRUD Operations**
   - Create, edit, delete projects
   - Create, edit, toggle, delete tasks
   - Verify changes are instant (HTMX)

4. **Test Search**
   - Search for projects/tasks
   - Verify only your tenant's data appears

### Database Verification

```bash
python manage.py shell
```

```python
from core.models import Tenant, Project
from core.managers import set_current_tenant

# Get tenants
tenant1 = Tenant.objects.get(name="Acme Corp")
tenant2 = Tenant.objects.get(name="TechStart Inc")

# Without tenant context - see all
print(Project.objects.without_tenant_filter().count())

# With tenant context - filtered
set_current_tenant(tenant1)
print(Project.objects.all().count())  # Only Tenant 1's projects
```

## 📝 Configuration

### Settings

Key settings in `saas_app/settings.py`:

```python
# Custom user model
AUTH_USER_MODEL = 'core.User'

# Tenant middleware (must be after AuthenticationMiddleware)
MIDDLEWARE = [
    # ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'core.middleware.TenantMiddleware',  # Add this
]

# Login/logout URLs
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'core:dashboard'
LOGOUT_REDIRECT_URL = 'login'
```

### Database

The application uses SQLite by default. To use PostgreSQL:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'your_db_name',
        'USER': 'your_db_user',
        'PASSWORD': 'your_db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## 🐛 Troubleshooting

### Issue: No tenant associated with user

**Cause**: User doesn't have a tenant assigned

**Solution**:
```bash
python manage.py shell
```
```python
from core.models import Tenant, User
tenant = Tenant.objects.first()
user = User.objects.get(username='your_username')
user.tenant = tenant
user.save()
```

### Issue: Cross-tenant data visible

**Cause**: Middleware not properly configured

**Solution**: Ensure `TenantMiddleware` is in `MIDDLEWARE` after `AuthenticationMiddleware`

### Issue: Objects created without tenant

**Cause**: Creating objects outside request context

**Solution**: Explicitly set tenant:
```python
from core.managers import set_current_tenant
set_current_tenant(tenant)
# Now create objects
```

### Issue: HTMX requests failing

**Cause**: Missing HTMX headers

**Solution**: Ensure HTMX is properly loaded:
```html
<script src="https://unpkg.com/htmx.org@1.9.10"></script>
```

## 🚀 Production Deployment

### Pre-deployment Checklist

- [ ] Change `SECRET_KEY` in settings
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use production database (PostgreSQL recommended)
- [ ] Set up static files serving
- [ ] Configure logging
- [ ] Set up SSL/HTTPS
- [ ] Enable CSRF protection
- [ ] Configure email backend
- [ ] Set up monitoring

### Environment Variables

Create a `.env` file:

```bash
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:pass@localhost/dbname
```

### Static Files

```bash
python manage.py collectstatic
```

### WSGI Server

Use Gunicorn for production:

```bash
pip install gunicorn
gunicorn saas_app.wsgi:application --bind 0.0.0.0:8000
```

## 📄 License

This project is provided as-is for educational and commercial use.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:

- Add unit tests
- Add integration tests
- Implement API endpoints (REST/GraphQL)
- Add more tenant isolation levels
- Implement tenant subdomain routing
- Add tenant-specific settings/customization
- Implement billing and subscription management
- Add analytics and reporting
- Improve error handling
- Add comprehensive logging

## 📧 Support

For questions or issues:
1. Check the troubleshooting section
2. Review the demo scripts
3. Examine the inline code documentation
4. Test with the sample data

## 🎓 Learning Resources

To understand the concepts better:

1. **Multi-tenancy Patterns**: Read about different multi-tenancy architectures
2. **Django ORM**: Understand QuerySets and Managers
3. **Thread-local Storage**: Learn about thread safety in web applications
4. **HTMX**: Explore hypermedia-driven applications
5. **Django Middleware**: Understand request/response processing

## 🔮 Future Enhancements

Potential features to add:

- [ ] Tenant signup and onboarding flow
- [ ] Subscription and billing integration (Stripe)
- [ ] Tenant usage analytics and metrics
- [ ] Multi-level user roles and permissions
- [ ] Tenant-specific branding and customization
- [ ] Data export and backup per tenant
- [ ] Audit logging for compliance
- [ ] Advanced search with ElasticSearch
- [ ] Real-time notifications (WebSockets)
- [ ] Mobile app integration (REST API)
- [ ] Tenant subdomain routing
- [ ] Data migration between tenants
- [ ] Tenant suspension and archiving

---

**Built with ❤️ using Django 6.0 and modern web technologies**

