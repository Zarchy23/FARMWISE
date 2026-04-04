# core/mixins.py
# FARMWISE - View Mixins for RBAC

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .permissions import (
    has_permission, can_access_farm, can_edit_farm, 
    can_access_field, can_edit_field, can_access_animal,
    can_add_health_record, can_access_equipment, can_edit_equipment,
    can_access_listing, can_edit_listing
)


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to require specific user role(s).
    
    Usage:
        class MyView(RoleRequiredMixin, View):
            required_roles = ['farmer', 'large_farmer']
    """
    required_roles = []
    
    def test_func(self):
        if self.request.user.user_type in self.required_roles:
            return True
        return False
    
    def handle_no_permission(self):
        raise PermissionDenied(
            f"This view requires one of these roles: {', '.join(self.required_roles)}"
        )


class PermissionRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to require specific module/action permission.
    
    Usage:
        class MyView(PermissionRequiredMixin, View):
            permission_module = 'crops'
            permission_action = 'create'
    """
    permission_module = None
    permission_action = None
    
    def test_func(self):
        if not self.permission_module or not self.permission_action:
            return True
        return has_permission(self.request.user, self.permission_module, self.permission_action)
    
    def handle_no_permission(self):
        raise PermissionDenied(
            f"You don't have permission to {self.permission_action} in {self.permission_module}"
        )


class FarmAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check farm access for views with farm_id in URL.
    
    Usage:
        class FarmDetailView(FarmAccessMixin, DetailView):
            model = Farm
            def test_func(self):
                farm = self.get_object()
                return can_access_farm(self.request.user, farm)
    """
    
    def test_func(self):
        farm = self.get_farm()
        if farm:
            return can_access_farm(self.request.user, farm)
        return False
    
    def get_farm(self):
        """Override this method to return the farm object"""
        if hasattr(self, 'object') and hasattr(self.object, 'farm'):
            return self.object.farm
        elif 'farm_id' in self.kwargs:
            from .models import Farm
            return get_object_or_404(Farm, id=self.kwargs['farm_id'])
        elif 'pk' in self.kwargs and self.model == Farm:
            from .models import Farm
            return get_object_or_404(Farm, id=self.kwargs['pk'])
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have access to this farm")


class FarmEditMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check farm edit permission.
    """
    
    def test_func(self):
        farm = self.get_farm()
        if farm:
            return can_edit_farm(self.request.user, farm)
        return False
    
    def get_farm(self):
        """Override this method to return the farm object"""
        if hasattr(self, 'object') and hasattr(self.object, 'farm'):
            return self.object.farm
        elif 'farm_id' in self.kwargs:
            from .models import Farm
            return get_object_or_404(Farm, id=self.kwargs['farm_id'])
        elif 'pk' in self.kwargs and self.model == Farm:
            from .models import Farm
            return get_object_or_404(Farm, id=self.kwargs['pk'])
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have permission to edit this farm")


class FieldAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check field access (via parent farm).
    """
    
    def test_func(self):
        field = self.get_field()
        if field:
            return can_access_field(self.request.user, field)
        return False
    
    def get_field(self):
        """Override this method to return the field object"""
        if hasattr(self, 'object'):
            return self.object
        elif 'field_id' in self.kwargs:
            from .models import Field
            return get_object_or_404(Field, id=self.kwargs['field_id'])
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have access to this field")


class FieldEditMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check field edit permission.
    """
    
    def test_func(self):
        field = self.get_field()
        if field:
            return can_edit_field(self.request.user, field)
        return False
    
    def get_field(self):
        """Override this method to return the field object"""
        if hasattr(self, 'object'):
            return self.object
        elif 'field_id' in self.kwargs:
            from .models import Field
            return get_object_or_404(Field, id=self.kwargs['field_id'])
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have permission to edit this field")


class AnimalAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check animal access (via parent farm).
    """
    
    def test_func(self):
        animal = self.get_animal()
        if animal:
            return can_access_animal(self.request.user, animal)
        return False
    
    def get_animal(self):
        """Override this method to return the animal object"""
        if hasattr(self, 'object'):
            return self.object
        elif 'animal_id' in self.kwargs:
            from .models import Animal
            return get_object_or_404(Animal, id=self.kwargs['animal_id'])
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have access to this animal")


class HealthRecordAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check permission to add health records.
    """
    
    def test_func(self):
        animal = self.get_animal()
        if animal:
            return can_add_health_record(self.request.user, animal)
        return False
    
    def get_animal(self):
        """Override this method or use context_data to get animal"""
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have permission to add health records for this animal")


class EquipmentAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check equipment access.
    """
    
    def test_func(self):
        equipment = self.get_equipment()
        if equipment:
            return can_access_equipment(self.request.user, equipment)
        return False
    
    def get_equipment(self):
        """Override this method to return the equipment object"""
        if hasattr(self, 'object'):
            return self.object
        elif 'equipment_id' in self.kwargs:
            from .models import Equipment
            return get_object_or_404(Equipment, id=self.kwargs['equipment_id'])
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have access to this equipment")


class EquipmentEditMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check equipment edit permission.
    """
    
    def test_func(self):
        equipment = self.get_equipment()
        if equipment:
            return can_edit_equipment(self.request.user, equipment)
        return False
    
    def get_equipment(self):
        """Override this method to return the equipment object"""
        if hasattr(self, 'object'):
            return self.object
        elif 'equipment_id' in self.kwargs:
            from .models import Equipment
            return get_object_or_404(Equipment, id=self.kwargs['equipment_id'])
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have permission to edit this equipment")


class MarketplaceListingAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check marketplace listing access.
    """
    
    def test_func(self):
        listing = self.get_listing()
        if listing:
            return can_access_listing(self.request.user, listing)
        return False
    
    def get_listing(self):
        """Override this method to return the listing object"""
        if hasattr(self, 'object'):
            return self.object
        elif 'listing_id' in self.kwargs:
            from .models import ProductListing
            return get_object_or_404(ProductListing, id=self.kwargs['listing_id'])
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have access to this listing")


class MarketplaceListingEditMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin to check marketplace listing edit permission.
    """
    
    def test_func(self):
        listing = self.get_listing()
        if listing:
            return can_edit_listing(self.request.user, listing)
        return False
    
    def get_listing(self):
        """Override this method to return the listing object"""
        if hasattr(self, 'object'):
            return self.object
        elif 'listing_id' in self.kwargs:
            from .models import ProductListing
            return get_object_or_404(ProductListing, id=self.kwargs['listing_id'])
        return None
    
    def handle_no_permission(self):
        raise PermissionDenied("You do not have permission to edit this listing")
