# core/permissions.py
# FARMWISE - Role-Based Access Control (RBAC) System
# Comprehensive permission checking and enforcement

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from typing import List, Dict, Any

# ============================================================
# PERMISSION MAPPING - Who can do what
# ============================================================

ROLE_PERMISSIONS = {
    'farmer': {
        'farms': ['view_own', 'create', 'edit_own', 'delete_own'],
        'fields': ['view_own', 'create', 'edit_own', 'delete_own'],
        'crops': ['view_own', 'create', 'edit_own', 'delete_own', 'harvest'],
        'livestock': ['view_own', 'create', 'edit_own', 'delete_own', 'health_record'],
        'equipment': ['view_all', 'book', 'list_own'],
        'marketplace': ['view_all', 'create_listing', 'buy', 'sell'],
        'pest': ['view_own', 'upload', 'view_analysis'],
        'weather': ['view_all'],
        'insurance': ['view_own', 'buy', 'claim'],
        'labor': ['view_own', 'create', 'edit_own'],
        'reports': ['view_own', 'generate_own'],
    },
    'large_farmer': {
        'farms': ['view_own', 'create', 'edit_own', 'delete_own'],
        'fields': ['view_own', 'create', 'edit_own', 'delete_own'],
        'crops': ['view_own', 'create', 'edit_own', 'delete_own', 'harvest', 'bulk_plant'],
        'livestock': ['view_own', 'create', 'edit_own', 'delete_own', 'health_record'],
        'equipment': ['view_all', 'book', 'list_own', 'create_rental'],
        'marketplace': ['view_all', 'create_listing', 'buy', 'sell', 'bulk_listing'],
        'pest': ['view_own', 'upload', 'view_analysis'],
        'weather': ['view_all'],
        'insurance': ['view_own', 'buy', 'claim'],
        'labor': ['view_own', 'create', 'edit_own', 'manage_payroll'],
        'reports': ['view_own', 'generate_own', 'export'],
    },
    'cooperative_admin': {
        'farms': ['view_coop', 'view_only'],
        'fields': ['view_coop', 'view_only'],
        'crops': ['view_coop', 'view_only'],
        'livestock': ['view_coop', 'view_only'],
        'equipment': ['view_coop', 'coordinate'],
        'marketplace': ['view_all', 'create_listing', 'buy', 'bulk_coordination'],
        'pest': ['view_coop', 'coordinate'],
        'weather': ['view_all'],
        'insurance': ['view_coop', 'view_only'],
        'cooperative': ['manage', 'invite_members', 'view_members', 'generate_reports'],
        'reports': ['view_coop', 'generate_coop_reports'],
    },
    'agronomist': {
        'farms': ['view_assigned', 'view_only'],
        'fields': ['view_assigned', 'view_only'],
        'crops': ['view_assigned', 'view_only', 'add_notes'],
        'livestock': ['view_assigned', 'view_only'],
        'pest': ['view_all_pending', 'verify', 'add_treatment', 'send_alerts'],
        'weather': ['view_all'],
        'soil_testing': ['request', 'view_results'],
        'reports': ['view_assigned', 'generate_assigned'],
        'advisory': ['send_alerts', 'schedule_visits', 'add_notes'],
    },
    'equipment_owner': {
        'equipment': ['view_own', 'create', 'edit_own', 'delete_own', 'manage_bookings'],
        'marketplace': ['view_all', 'create_listing', 'buy', 'sell'],
        'reports': ['equipment_utilization', 'earnings'],
    },
    'insurance_agent': {
        'insurance': ['view_all', 'sell', 'process_claims', 'view_policies'],
        'marketplace': ['view_all', 'buy'],
        'reports': ['sales_reports', 'claim_reports'],
        'farmer_info': ['view_basic'],
    },
    'market_trader': {
        'marketplace': ['view_all', 'create_buy_orders', 'create_listings', 'bulk_operations', 'price_analytics'],
        'weather': ['view_all'],
        'reports': ['sales', 'price_trends', 'export_history', 'api_access'],
    },
    'veterinarian': {
        'livestock': ['view_assigned', 'view_only'],
        'health_records': ['view_assigned', 'create', 'edit_own', 'prescribe'],
        'breeding': ['view_assigned', 'view_only'],
        'marketplace': ['view_all', 'buy', 'sell'],
        'health_certificates': ['view_own', 'create', 'sign'],
    },
    'lab_technician': {
        'soil_testing': ['view_pending', 'record_results', 'generate_reports'],
        'marketplace': ['view_all', 'buy'],
    },
    'supermarket': {
        'marketplace': ['view_all', 'create_listings', 'buy', 'sell', 'manage_own_listings'],
        'reports': ['sales', 'inventory', 'transactions', 'export_all'],
        'transactions': ['view_own', 'view_detailed'],
    },
    'admin': {
        # System admin has full access
        'all': ['full_access'],
    }
}

# ============================================================
# ACCESS CONTROL MATRICES
# ============================================================

FIELD_ACCESS_MATRIX = {
    # Entity -> (permission_type, required_role_permissions)
    'farm': ('ownership', ['view_own', 'create', 'edit_own', 'delete_own']),
    'field': ('ownership', ['view_own', 'create', 'edit_own', 'delete_own']),
    'crop': ('ownership', ['view_own', 'create', 'edit_own', 'delete_own']),
    'animal': ('ownership', ['view_own', 'create', 'edit_own', 'delete_own']),
    'equipment': ('ownership', ['view_own', 'create', 'edit_own', 'delete_own']),
    'product_listing': ('ownership', ['create_listing', 'edit_own', 'delete_own']),
    'health_record': ('assignment', ['create', 'edit_own']),
    'pest_report': ('ownership', ['view_own', 'upload']),
}

# ============================================================
# PERMISSION CHECKING FUNCTIONS
# ============================================================

def has_permission(user, module: str, action: str) -> bool:
    """Check if user has permission for a specific action in a module"""
    
    # Anonymous users have no permissions
    if not user.is_authenticated:
        return False
    
    # Admin can do everything
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    # Check if module and action exist in permissions
    user_perms = ROLE_PERMISSIONS.get(user.user_type, {})
    
    if module == 'all':
        return user.user_type == 'admin'
    
    module_perms = user_perms.get(module, [])
    return action in module_perms


def can_access_farm(user, farm) -> bool:
    """Check if user can access a specific farm"""
    
    # Anonymous users cannot access
    if not user.is_authenticated:
        return False
    
    # Admin can access everything
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    # Owner can access their own farm
    if farm.owner == user:
        return True
    
    # Cooperative admin can view farms in their cooperative
    if user.user_type == 'cooperative_admin' and farm.cooperative:
        return farm.cooperative.admin == user
    
    # Assigned agronomist/veterinarian
    if user.user_type in ['agronomist', 'veterinarian']:
        return farm in user.assigned_farms.all()
    
    return False


def can_edit_farm(user, farm) -> bool:
    """Check if user can edit a specific farm"""
    
    # Anonymous users cannot edit
    if not user.is_authenticated:
        return False
    
    # Admin can edit everything
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    # Only owner can edit
    if farm.owner == user:
        return True
    
    return False


def can_access_field(user, field) -> bool:
    """Check if user can access a specific field"""
    
    # Anonymous users cannot access
    if not user.is_authenticated:
        return False
    
    # Admin can access everything
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    # Check if user can access the parent farm
    return can_access_farm(user, field.farm)


def can_edit_field(user, field) -> bool:
    """Check if user can edit a specific field"""
    
    # Only field owner (farm owner) can edit
    return can_edit_farm(user, field.farm)


def can_access_animal(user, animal) -> bool:
    """Check if user can access a specific animal"""
    
    # Anonymous users cannot access
    if not user.is_authenticated:
        return False
    
    # Admin can access everything
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    # Farm owner can access their animals
    if animal.farm.owner == user:
        return True
    
    # Veterinarian assigned to farm
    if user.user_type == 'veterinarian':
        return animal.farm in user.assigned_farms.all()
    
    # Coop admin can view animals in their coop
    if user.user_type == 'cooperative_admin' and animal.farm.cooperative:
        return animal.farm.cooperative.admin == user
    
    return False


def can_add_health_record(user, animal) -> bool:
    """Check if user can add health records for an animal"""
    
    # Anonymous users cannot add records
    if not user.is_authenticated:
        return False
    
    # Admin can add records
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    # Farm owner can add records
    if animal.farm.owner == user:
        return True
    
    # Veterinarian assigned to farm can add records
    if user.user_type == 'veterinarian':
        return animal.farm in user.assigned_farms.all()
    
    return False


def can_access_equipment(user, equipment) -> bool:
    """Check if user can access equipment"""
    
    # Anonymous users cannot access
    if not user.is_authenticated:
        return False
    
    # Admin can access everything
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    # Equipment owner can access their own equipment
    if equipment.owner == user:
        return True
    
    # Everyone can view (not edit) available equipment
    if equipment.is_available:
        return True
    
    return False


def can_edit_equipment(user, equipment) -> bool:
    """Check if user can edit equipment"""
    
    # Anonymous users cannot edit
    if not user.is_authenticated:
        return False
    
    # Only equipment owner can edit
    if equipment.owner == user:
        return True
    
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    return False


def can_access_listing(user, listing) -> bool:
    """Check if user can access a marketplace listing"""
    
    # Anonymous users can only view active listings
    if not user.is_authenticated:
        return listing.status == 'active'
    
    # Admin can access everything
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    # Everyone can view active listings
    if listing.status == 'active':
        return True
    
    # Owner can view their own listings
    if listing.seller == user:
        return True
    
    return False


def can_edit_listing(user, listing) -> bool:
    """Check if user can edit a listing"""
    
    # Anonymous users cannot edit
    if not user.is_authenticated:
        return False
    
    # Only seller can edit
    if listing.seller == user:
        return True
    
    if user.user_type == 'admin' or user.is_superuser:
        return True
    
    return False


def get_accessible_farms(user):
    """Get all farms the user can access"""
    from .models import Farm
    
    # Anonymous users cannot access any farms
    if not user.is_authenticated:
        return Farm.objects.none()
    
    # Admin can access all
    if user.user_type == 'admin' or user.is_superuser:
        return Farm.objects.all()
    
    # Farmer/Large Farmer can access their own
    if user.user_type in ['farmer', 'large_farmer']:
        return Farm.objects.filter(owner=user)
    
    # Cooperative admin can access farms in their cooperative
    if user.user_type == 'cooperative_admin':
        return Farm.objects.filter(cooperative__admin=user)
    
    # Agronomist/Veterinarian can access assigned farms
    if user.user_type in ['agronomist', 'veterinarian']:
        return user.assigned_farms.all()
    
    # Others have no access
    return Farm.objects.none()


def get_accessible_animals(user):
    """Get all animals the user can access"""
    from .models import Animal
    
    # Anonymous users cannot access any animals
    if not user.is_authenticated:
        return Animal.objects.none()
    
    # Admin can access all
    if user.user_type == 'admin' or user.is_superuser:
        return Animal.objects.all()
    
    # Farmer/Large Farmer can access their own
    if user.user_type in ['farmer', 'large_farmer']:
        return Animal.objects.filter(farm__owner=user)
    
    # Cooperative admin can access animals in their coop
    if user.user_type == 'cooperative_admin':
        return Animal.objects.filter(farm__cooperative__admin=user)
    
    # Veterinarian can access animals on assigned farms
    if user.user_type == 'veterinarian':
        return Animal.objects.filter(farm__in=user.assigned_farms.all())
    
    # Others have no access
    return Animal.objects.none()


def get_accessible_equipment(user):
    """Get all equipment the user can see"""
    from .models import Equipment
    
    # Anonymous users can only see available equipment
    if not user.is_authenticated:
        return Equipment.objects.filter(is_available=True)
    
    # Everyone can see available equipment
    accessible = Equipment.objects.filter(is_available=True)
    
    # Equipment owner can also see their own
    if user.user_type == 'equipment_owner':
        accessible = accessible | Equipment.objects.filter(owner=user)
    
    # Admin can see all
    if user.user_type == 'admin' or user.is_superuser:
        return Equipment.objects.all()
    
    return accessible.distinct()


def get_accessible_listings(user):
    """Get all marketplace listings the user can see"""
    from .models import ProductListing
    
    # Everyone (even anonymous) can see active listings
    accessible = ProductListing.objects.filter(status='active')
    
    # Authenticated users can also see their own
    if user.is_authenticated:
        accessible = accessible | ProductListing.objects.filter(seller=user)
        
        # Admin can see all
        if user.user_type == 'admin' or user.is_superuser:
            return ProductListing.objects.all()
    
    return accessible.distinct()


def get_accessible_pest_reports(user):
    """Get all pest reports the user can see"""
    from .models import PestReport
    
    # Anonymous users cannot access any reports
    if not user.is_authenticated:
        return PestReport.objects.none()
    
    # Admin can see all
    if user.user_type == 'admin' or user.is_superuser:
        return PestReport.objects.all()
    
    # Farmer/Large Farmer can see their own
    if user.user_type in ['farmer', 'large_farmer']:
        return PestReport.objects.filter(reporter=user)
    
    # Cooperative admin can see reports from their coop
    if user.user_type == 'cooperative_admin':
        return PestReport.objects.filter(farm__cooperative__admin=user)
    
    # Agronomist can see all pending reports
    if user.user_type == 'agronomist':
        return PestReport.objects.filter(status='pending') | PestReport.objects.filter(
            farm__in=user.assigned_farms.all()
        )
    
    return PestReport.objects.none()


# ============================================================
# DECORATORS FOR VIEWS
# ============================================================

def require_permission(module: str, action: str):
    """Decorator to check permission for a module/action"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not has_permission(request.user, module, action):
                raise PermissionDenied(
                    f"User does not have permission to {action} in {module}"
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def require_farm_access():
    """Decorator to check farm access for views with farm_id parameter"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, farm_id, *args, **kwargs):
            from .models import Farm
            farm = get_object_or_404(Farm, id=farm_id)
            
            if not can_access_farm(request.user, farm):
                raise PermissionDenied("You do not have access to this farm")
            
            return view_func(request, farm_id, *args, **kwargs)
        return wrapper
    return decorator


def require_farm_edit():
    """Decorator to check farm edit permission for views with farm_id parameter"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, farm_id, *args, **kwargs):
            from .models import Farm
            farm = get_object_or_404(Farm, id=farm_id)
            
            if not can_edit_farm(request.user, farm):
                raise PermissionDenied("You do not have permission to edit this farm")
            
            return view_func(request, farm_id, *args, **kwargs)
        return wrapper
    return decorator


# ============================================================
# CONTEXT PROCESSORS (for templates)
# ============================================================

def user_permissions_context(request):
    """Add user permissions to template context"""
    
    if not request.user.is_authenticated:
        return {}
    
    return {
        'user_permissions': ROLE_PERMISSIONS.get(request.user.user_type, {}),
        'user_role': request.user.user_type,
        'can_manage_users': request.user.user_type == 'admin',
        'can_manage_cooperative': request.user.user_type == 'cooperative_admin',
        'can_verify_pest': request.user.user_type == 'agronomist',
        'can_process_insurance': request.user.user_type == 'insurance_agent',
        'can_manage_equipment': request.user.user_type == 'equipment_owner',
    }
