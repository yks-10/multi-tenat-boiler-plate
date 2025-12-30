from django.contrib import admin
from django.contrib.auth.models import Permission

from .models import Tenant, User, Project, Task

admin.site.register(Tenant)
admin.site.register(Permission)
admin.site.register(User)
admin.site.register(Project)
admin.site.register(Task)