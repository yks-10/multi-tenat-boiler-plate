"""
Multi-tenant managers and querysets for automatic tenant filtering.
"""
from django.db import models
from django.db.models import QuerySet
from threading import local


# Thread-local storage for the current tenant
_thread_locals = local()


def get_current_tenant():
    """Get the current tenant from thread-local storage."""
    return getattr(_thread_locals, 'tenant', None)


def set_current_tenant(tenant):
    """Set the current tenant in thread-local storage."""
    _thread_locals.tenant = tenant


def clear_current_tenant():
    """Clear the current tenant from thread-local storage."""
    if hasattr(_thread_locals, 'tenant'):
        delattr(_thread_locals, 'tenant')


class TenantQuerySet(QuerySet):
    """
    Custom QuerySet that automatically filters by the current tenant.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._tenant_filtering_disabled = False
    
    def _filter_by_tenant(self):
        """Apply tenant filtering if a tenant is set and filtering is enabled."""
        if self._tenant_filtering_disabled:
            return self
        
        tenant = get_current_tenant()
        if tenant is None:
            return self
        
        # Check if the model has a tenant field
        if hasattr(self.model, 'tenant'):
            return self.filter(tenant=tenant)
        
        return self
    
    def _chain(self, **kwargs):
        """Override _chain to maintain tenant filtering state."""
        clone = super()._chain(**kwargs)
        clone._tenant_filtering_disabled = self._tenant_filtering_disabled
        return clone
    
    def all(self):
        """Override all() to apply tenant filtering."""
        result = super().all()
        return result._filter_by_tenant()
    
    def filter(self, *args, **kwargs):
        """Override filter() to apply tenant filtering first."""
        result = super().filter(*args, **kwargs)
        # Don't re-filter if we're already filtering by tenant explicitly
        if 'tenant' in kwargs or 'tenant__id' in kwargs or 'tenant_id' in kwargs:
            return result
        return result._filter_by_tenant()
    
    def get(self, *args, **kwargs):
        """Override get() to apply tenant filtering."""
        # Don't re-filter if we're already filtering by tenant explicitly
        if not ('tenant' in kwargs or 'tenant__id' in kwargs or 'tenant_id' in kwargs):
            tenant = get_current_tenant()
            if tenant is not None and hasattr(self.model, 'tenant') and not self._tenant_filtering_disabled:
                kwargs['tenant'] = tenant
        return super().get(*args, **kwargs)
    
    def create(self, **kwargs):
        """Override create() to automatically set the tenant."""
        tenant = get_current_tenant()
        if tenant is not None and hasattr(self.model, 'tenant') and 'tenant' not in kwargs:
            kwargs['tenant'] = tenant
        return super().create(**kwargs)
    
    def update(self, **kwargs):
        """Override update() to prevent changing tenant."""
        if 'tenant' in kwargs:
            raise ValueError("Cannot change tenant through update(). This is a security measure.")
        return self._filter_by_tenant().filter(*self._result_cache if hasattr(self, '_result_cache') else []).update(**kwargs)
    
    def delete(self):
        """Override delete() to ensure tenant filtering."""
        return self._filter_by_tenant().filter(*self._result_cache if hasattr(self, '_result_cache') else []).delete()
    
    def without_tenant_filter(self):
        """
        Return a clone of this queryset without tenant filtering.
        Use with caution - this bypasses tenant isolation!
        """
        clone = self._chain()
        clone._tenant_filtering_disabled = True
        return clone
    
    def for_tenant(self, tenant):
        """
        Return a queryset filtered for a specific tenant.
        This allows cross-tenant queries when necessary.
        """
        if tenant is None:
            return self.without_tenant_filter()
        return self.without_tenant_filter().filter(tenant=tenant)


class TenantManager(models.Manager):
    """
    Custom Manager that uses TenantQuerySet for automatic tenant filtering.
    """
    
    def get_queryset(self):
        """Return a TenantQuerySet instead of a regular QuerySet."""
        return TenantQuerySet(self.model, using=self._db)
    
    def without_tenant_filter(self):
        """
        Return a queryset without tenant filtering.
        Use with caution - this bypasses tenant isolation!
        """
        return self.get_queryset().without_tenant_filter()
    
    def for_tenant(self, tenant):
        """
        Return a queryset filtered for a specific tenant.
        This allows cross-tenant queries when necessary.
        """
        return self.get_queryset().for_tenant(tenant)
    
    def create(self, **kwargs):
        """Override create() to automatically set the tenant."""
        tenant = get_current_tenant()
        if tenant is not None and hasattr(self.model, 'tenant') and 'tenant' not in kwargs:
            kwargs['tenant'] = tenant
        return super().create(**kwargs)
    
    def bulk_create(self, objs, **kwargs):
        """Override bulk_create() to automatically set the tenant on all objects."""
        tenant = get_current_tenant()
        if tenant is not None and hasattr(self.model, 'tenant'):
            for obj in objs:
                if not hasattr(obj, 'tenant') or obj.tenant is None:
                    obj.tenant = tenant
        return super().bulk_create(objs, **kwargs)


class TenantModelMixin:
    """
    Mixin for models that should use tenant filtering.
    Add this to any model that has a tenant field.
    """
    objects = TenantManager()
    
    def save(self, *args, **kwargs):
        """Override save() to automatically set the tenant on new objects."""
        if self.pk is None:  # New object
            tenant = get_current_tenant()
            if tenant is not None and hasattr(self, 'tenant') and self.tenant is None:
                self.tenant = tenant
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Override delete() to verify tenant before deletion."""
        tenant = get_current_tenant()
        if tenant is not None and hasattr(self, 'tenant') and self.tenant != tenant:
            raise ValueError(
                f"Cannot delete object from tenant {self.tenant} while current tenant is {tenant}. "
                "This is a security measure."
            )
        return super().delete(*args, **kwargs)
    
    class Meta:
        abstract = True

