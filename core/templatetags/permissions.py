# core/templatetags/permissions.py
# FARMWISE - Template Tags for RBAC

from django import template
from django.template.defaulttags import register
from core.permissions import has_permission, can_access_farm, can_edit_farm
from core.permissions import can_access_animal, can_add_health_record, can_access_equipment
from core.permissions import can_edit_equipment, can_access_listing, can_edit_listing

register = template.Library()


# ============================================================
# PERMISSION CHECKING TAGS
# ============================================================

@register.filter
def has_module_permission(user, module_action: str):
    """Check if user has permission for module/action"""
    # Anonymous users have no permissions
    if not user.is_authenticated:
        return False
    if '.' in module_action:
        module, action = module_action.split('.', 1)
        return has_permission(user, module, action)
    return False


@register.filter
def user_role(user):
    """Get user's role display name"""
    if hasattr(user, 'get_user_type_display'):
        return user.get_user_type_display()
    return user.user_type


@register.filter
def can_access(user, obj):
    """Generic permission check for various object types"""
    if obj.__class__.__name__ == 'Farm':
        return can_access_farm(user, obj)
    elif obj.__class__.__name__ == 'Animal':
        return can_access_animal(user, obj)
    elif obj.__class__.__name__ == 'Equipment':
        return can_access_equipment(user, obj)
    elif obj.__class__.__name__ == 'ProductListing':
        return can_access_listing(user, obj)
    return False


@register.filter
def can_edit(user, obj):
    """Generic edit permission check for various object types"""
    if obj.__class__.__name__ == 'Farm':
        return can_edit_farm(user, obj)
    elif obj.__class__.__name__ == 'Equipment':
        return can_edit_equipment(user, obj)
    elif obj.__class__.__name__ == 'ProductListing':
        return can_edit_listing(user, obj)
    return False


# ============================================================
# ROLE CHECKING TAGS
# ============================================================

@register.filter
def is_farmer(user):
    """Check if user is farmer (small or large)"""
    return user.is_authenticated and user.user_type in ['farmer', 'large_farmer']


@register.filter
def is_large_farmer(user):
    """Check if user is large scale farmer"""
    return user.is_authenticated and user.user_type == 'large_farmer'


@register.filter
def is_coop_admin(user):
    """Check if user is cooperative admin"""
    return user.is_authenticated and user.user_type == 'cooperative_admin'


@register.filter
def is_agronomist(user):
    """Check if user is agronomist"""
    return user.is_authenticated and user.user_type == 'agronomist'


@register.filter
def is_equipment_owner(user):
    """Check if user is equipment owner"""
    return user.is_authenticated and user.user_type == 'equipment_owner'


@register.filter
def is_insurance_agent(user):
    """Check if user is insurance agent"""
    return user.is_authenticated and user.user_type == 'insurance_agent'


@register.filter
def is_market_trader(user):
    """Check if user is market trader"""
    return user.is_authenticated and user.user_type == 'market_trader'


@register.filter
def is_veterinarian(user):
    """Check if user is veterinarian"""
    return user.is_authenticated and user.user_type == 'veterinarian'


@register.filter
def is_lab_technician(user):
    """Check if user is lab technician"""
    return user.is_authenticated and user.user_type == 'lab_technician'


@register.filter
def is_admin(user):
    """Check if user is system admin"""
    return user.user_type == 'admin' or user.is_superuser


# ============================================================
# CONDITIONAL RENDERING TAGS
# ============================================================

@register.simple_tag
def show_if_can_edit(user, obj):
    """Return True if user can edit object"""
    return can_edit(user, obj)


@register.simple_tag
def show_if_has_permission(user, module, action):
    """Return True if user has module/action permission"""
    return has_permission(user, module, action)


@register.simple_tag
def show_if_role(user, role):
    """Return True if user has specific role"""
    return user.user_type == role


@register.simple_tag
def show_if_role_in(user, roles_str):
    """Return True if user role is in comma-separated list"""
    roles = [r.strip() for r in roles_str.split(',')]
    return user.user_type in roles
