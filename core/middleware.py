# core/middleware.py
from django.utils.deprecation import MiddlewareMixin
from .managers import set_current_tenant, clear_current_tenant


class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        """Set the current tenant based on the authenticated user."""
        if request.user.is_authenticated:
            request.tenant = request.user.tenant
            set_current_tenant(request.user.tenant)
        else:
            request.tenant = None
            clear_current_tenant()
    
    def process_response(self, request, response):
        """Clear the tenant from thread-local storage after the request."""
        clear_current_tenant()
        return response
    
    def process_exception(self, request, exception):
        """Clear the tenant from thread-local storage on exception."""
        clear_current_tenant()
