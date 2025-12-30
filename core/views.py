from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Project, Task
from .managers import get_current_tenant


# ============================================================================
# HTMX Helper Decorators and Functions
# ============================================================================

def htmx_required(view_func):
    """Decorator to ensure the request is from HTMX."""
    def wrapper(request, *args, **kwargs):
        if not request.headers.get('HX-Request'):
            return HttpResponse('HTMX request required', status=400)
        return view_func(request, *args, **kwargs)
    return wrapper


def tenant_check(view_func):
    """Decorator to ensure a tenant is set."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.tenant:
            return HttpResponse('No tenant associated with user', status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================================================================
# Dashboard Views
# ============================================================================

@login_required
@tenant_check
def dashboard(request):
    """Main dashboard view."""
    projects = Project.objects.all()  # Automatically filtered by tenant
    context = {
        'projects': projects,
        'tenant': request.tenant,
    }
    return render(request, 'core/dashboard.html', context)


# ============================================================================
# Project Views
# ============================================================================

@login_required
@tenant_check
def project_list(request):
    """List all projects for the current tenant."""
    projects = Project.objects.all()
    context = {'projects': projects}
    
    # Return partial template for HTMX requests
    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/project_list.html', context)
    
    return render(request, 'core/project_list.html', context)


@login_required
@tenant_check
@htmx_required
def project_create(request):
    """Create a new project (HTMX only)."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        
        if not name:
            return HttpResponse(
                '<div class="error">Project name is required</div>',
                status=400
            )
        
        # Create project - tenant is automatically set
        project = Project.objects.create(name=name)
        
        # Return the new project row
        context = {'project': project}
        response = render(request, 'core/partials/project_row.html', context)
        response['HX-Trigger'] = 'projectCreated'
        return response
    
    # Return the create form
    return render(request, 'core/partials/project_form.html')


@login_required
@tenant_check
@htmx_required
def project_edit(request, project_id):
    """Edit a project (HTMX only)."""
    # get_object_or_404 automatically filters by tenant
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        
        if not name:
            return HttpResponse(
                '<div class="error">Project name is required</div>',
                status=400
            )
        
        project.name = name
        project.save()
        
        # Return updated project row
        context = {'project': project}
        response = render(request, 'core/partials/project_row.html', context)
        response['HX-Trigger'] = 'projectUpdated'
        return response
    
    # Return the edit form
    context = {'project': project}
    return render(request, 'core/partials/project_form.html', context)


@login_required
@tenant_check
@htmx_required
@require_http_methods(['DELETE'])
def project_delete(request, project_id):
    """Delete a project (HTMX only)."""
    # get_object_or_404 automatically filters by tenant
    project = get_object_or_404(Project, id=project_id)
    project.delete()
    
    # Return empty response with trigger
    response = HttpResponse('')
    response['HX-Trigger'] = 'projectDeleted'
    return response


@login_required
@tenant_check
def project_detail(request, project_id):
    """View project details with tasks."""
    # get_object_or_404 automatically filters by tenant
    project = get_object_or_404(Project, id=project_id)
    tasks = Task.objects.filter(project=project)  # Also auto-filtered by tenant
    
    context = {
        'project': project,
        'tasks': tasks,
    }
    
    if request.headers.get('HX-Request'):
        return render(request, 'core/partials/project_detail.html', context)
    
    return render(request, 'core/project_detail.html', context)


# ============================================================================
# Task Views
# ============================================================================

@login_required
@tenant_check
@htmx_required
def task_create(request, project_id):
    """Create a new task for a project (HTMX only)."""
    # Ensure project belongs to current tenant
    project = get_object_or_404(Project, id=project_id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        
        if not title:
            return HttpResponse(
                '<div class="error">Task title is required</div>',
                status=400
            )
        
        # Create task - tenant is automatically set
        task = Task.objects.create(
            project=project,
            title=title,
            is_done=False
        )
        
        # Return the new task row
        context = {'task': task}
        response = render(request, 'core/partials/task_row.html', context)
        response['HX-Trigger'] = 'taskCreated'
        return response
    
    # Return the create form
    context = {'project': project}
    return render(request, 'core/partials/task_form.html', context)


@login_required
@tenant_check
@htmx_required
def task_toggle(request, task_id):
    """Toggle task completion status (HTMX only)."""
    # get_object_or_404 automatically filters by tenant
    task = get_object_or_404(Task, id=task_id)
    task.is_done = not task.is_done
    task.save()
    
    # Return updated task row
    context = {'task': task}
    response = render(request, 'core/partials/task_row.html', context)
    response['HX-Trigger'] = 'taskToggled'
    return response


@login_required
@tenant_check
@htmx_required
def task_edit(request, task_id):
    """Edit a task (HTMX only)."""
    # get_object_or_404 automatically filters by tenant
    task = get_object_or_404(Task, id=task_id)
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        
        if not title:
            return HttpResponse(
                '<div class="error">Task title is required</div>',
                status=400
            )
        
        task.title = title
        task.save()
        
        # Return updated task row
        context = {'task': task}
        response = render(request, 'core/partials/task_row.html', context)
        response['HX-Trigger'] = 'taskUpdated'
        return response
    
    # Return the edit form
    context = {'task': task}
    return render(request, 'core/partials/task_form.html', context)


@login_required
@tenant_check
@htmx_required
@require_http_methods(['DELETE'])
def task_delete(request, task_id):
    """Delete a task (HTMX only)."""
    # get_object_or_404 automatically filters by tenant
    task = get_object_or_404(Task, id=task_id)
    task.delete()
    
    # Return empty response with trigger
    response = HttpResponse('')
    response['HX-Trigger'] = 'taskDeleted'
    return response


# ============================================================================
# Search View (Tenant-Safe)
# ============================================================================

@login_required
@tenant_check
@htmx_required
def search(request):
    """Search projects and tasks within current tenant."""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return HttpResponse('')
    
    # Both queries automatically filtered by tenant
    projects = Project.objects.filter(name__icontains=query)
    tasks = Task.objects.filter(title__icontains=query)
    
    context = {
        'projects': projects,
        'tasks': tasks,
        'query': query,
    }
    
    return render(request, 'core/partials/search_results.html', context)
