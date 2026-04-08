# core/templates_service.py
"""
Template Library Service
Save and reuse templates for crops, treatments, equipment, schedules, reports
"""

from django.db import models
from django.utils import timezone
from .models import Farm, User
from decimal import Decimal
from typing import Dict, Any, List


class TemplateService:
    """Manage template library"""
    
    TEMPLATE_CATEGORIES = [
        ('crop_plan', 'Crop Plan'),
        ('treatment', 'Treatment Protocol'),
        ('equipment', 'Equipment Listing'),
        ('schedule', 'Work Schedule'),
        ('report', 'Report Template'),
    ]
    
    SHARE_LEVELS = [
        ('private', 'Only Me'),
        ('farm', 'My Farm'),
        ('cooperative', 'My Cooperative'),
        ('public', 'Public Marketplace'),
    ]
    
    @staticmethod
    def create_template(
        user: User,
        name: str,
        category: str,
        description: str = '',
        template_data: Dict[str, Any] = None,
        share_level: str = 'private',
        farm: Farm = None,
        price: Decimal = None
    ) -> 'Template':
        """
        Create a new template
        
        Args:
            user: User creating template
            name: Template name
            category: crop_plan, treatment, equipment, schedule, report
            description: Description
            template_data: Template configuration (JSON)
            share_level: private, farm, cooperative, public
            farm: Associated farm (optional)
            price: Price if selling in marketplace (optional)
        """
        
        from .models import Template
        
        template = Template.objects.create(
            user=user,
            name=name,
            category=category,
            description=description,
            template_data=template_data or {},
            share_level=share_level,
            farm=farm,
            price=price or Decimal('0.00'),
            usage_count=0,
            rating=Decimal('0.00'),
            is_active=True
        )
        
        return template
    
    @staticmethod
    def clone_template(
        template_id: int,
        user: User,
        new_name: str = None,
        customize_data: Dict[str, Any] = None
    ) -> 'Template':
        """
        Clone an existing template for user's own use
        """
        
        from .models import Template
        
        original = Template.objects.get(id=template_id)
        
        # Get copy of template data
        new_data = original.template_data.copy() if original.template_data else {}
        
        # Apply customizations
        if customize_data:
            new_data.update(customize_data)
        
        new_template = Template.objects.create(
            user=user,
            name=new_name or f"{original.name} (Copy)",
            category=original.category,
            description=original.description,
            template_data=new_data,
            share_level='private',  # Clones are private by default
            farm=None,
            price=Decimal('0.00'),
            usage_count=0,
            is_active=True
        )
        
        return new_template
    
    @staticmethod
    def apply_template(
        template_id: int,
        user: User,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get template data ready to use (pre-fill form, etc.)
        Records usage for analytics
        """
        
        from .models import Template
        
        template = Template.objects.get(id=template_id)
        
        # Record usage
        template.usage_count += 1
        template.last_used = timezone.now()
        template.save()
        
        # Return template data (ready to use)
        return {
            'template_id': template.id,
            'name': template.name,
            'category': template.category,
            'data': template.template_data,
            'context': context or {}
        }
    
    @staticmethod
    def get_user_templates(
        user: User,
        category: str = None
    ) -> list:
        """Get templates created by user"""
        
        from .models import Template
        
        query = Template.objects.filter(user=user)
        if category:
            query = query.filter(category=category)
        
        return query.order_by('-created_at')
    
    @staticmethod
    def get_available_templates(
        user: User,
        category: str = None
    ) -> list:
        """
        Get templates available to user
        (public + user's farm + cooperative + user's own)
        """
        
        from .models import Template
        
        templates = Template.objects.filter(
            is_active=True
        ).filter(
            models.Q(share_level='public') |
            models.Q(user=user) |
            models.Q(share_level='farm', farm__owner=user) |
            models.Q(share_level='cooperative', farm__cooperative=user.cooperative_member)
        )
        
        if category:
            templates = templates.filter(category=category)
        
        return templates.order_by('-rating', '-usage_count')
    
    @staticmethod
    def get_marketplace_templates(
        category: str = None,
        min_price: Decimal = None,
        max_price: Decimal = None,
        order_by: str = 'rating'
    ) -> list:
        """
        Get public templates available for purchase/use
        """
        
        from .models import Template
        
        templates = Template.objects.filter(
            share_level='public',
            is_active=True
        )
        
        if category:
            templates = templates.filter(category=category)
        
        if min_price:
            templates = templates.filter(price__gte=min_price)
        
        if max_price:
            templates = templates.filter(price__lte=max_price)
        
        order_map = {
            'rating': '-rating',
            'popularity': '-usage_count',
            'newest': '-created_at',
            'price_low': 'price',
            'price_high': '-price'
        }
        
        templates = templates.order_by(order_map.get(order_by, '-rating'))
        
        return templates
    
    @staticmethod
    def rate_template(
        template_id: int,
        user: User,
        rating: int
    ) -> float:
        """
        Rate a template (1-5 stars)
        Returns new average rating
        """
        
        from .models import Template, TemplateRating
        
        template = Template.objects.get(id=template_id)
        
        # Create or update rating
        template_rating, created = TemplateRating.objects.update_or_create(
            template=template,
            user=user,
            defaults={'rating': rating}
        )
        
        # Recalculate average rating
        avg_rating = TemplateRating.objects.filter(
            template=template
        ).aggregate(
            avg=models.Avg('rating')
        )['avg'] or Decimal('0.00')
        
        template.rating = Decimal(str(avg_rating))
        template.save()
        
        return float(avg_rating)
    
    @staticmethod
    def search_templates(
        search_term: str,
        user: User,
        category: str = None
    ) -> list:
        """Search templates by name or description"""
        
        from .models import Template
        from django.db.models import Q
        
        templates = Template.objects.filter(
            is_active=True
        ).filter(
            Q(share_level='public') |
            Q(user=user) |
            Q(share_level='farm', farm__owner=user) |
            Q(share_level='cooperative', farm__cooperative=user.cooperative_member)
        ).filter(
            Q(name__icontains=search_term) |
            Q(description__icontains=search_term) |
            Q(category__icontains=search_term)
        )
        
        if category:
            templates = templates.filter(category=category)
        
        return templates.order_by('-rating')


# Example: Crop Plan Template Structure
CROP_PLAN_TEMPLATE_EXAMPLE = {
    'crop_type': 'Maize',
    'variety': 'Hybrid H614',
    'planting': {
        'depth_cm': 5,
        'spacing_cm': '75x25',
        'seed_rate_kg_per_ha': 25
    },
    'fertilizer_schedule': [
        {
            'timing': 'at_planting',
            'type': 'DAP',
            'quantity_kg_per_ha': 50,
            'cost_per_kg': 0.50
        },
        {
            'timing': 'week_4',
            'type': 'Urea',
            'quantity_kg_per_ha': 50,
            'cost_per_kg': 0.45
        },
        {
            'timing': 'week_8',
            'type': 'NPK',
            'quantity_kg_per_ha': 50,
            'cost_per_kg': 0.55
        }
    ],
    'irrigation_schedule': [
        {'week': '1-3', 'frequency': 'daily', 'duration_minutes': 30},
        {'week': '4-8', 'frequency': 'every_3_days', 'duration_minutes': 45},
        {'week': '9+', 'frequency': 'as_needed', 'duration_minutes': 60}
    ],
    'pest_control': [
        {
            'timing': 'week_2',
            'pest': 'Germination weeds',
            'product': 'Pre-emergence herbicide',
            'method': 'Spray'
        },
        {
            'timing': 'week_6',
            'pest': 'Fall Armyworm',
            'product': 'Emamectin benzoate',
            'method': 'Foliar spray'
        }
    ],
    'expected_yield': 4500,  # kg/ha
    'estimated_cost': 5000,  # USD/ha
    'estimated_revenue': 10000  # USD/ha
}


# Example: Equipment Listing Template
EQUIPMENT_TEMPLATE_EXAMPLE = {
    'title': 'John Deere 5055D Tractor',
    'category': 'tractor',
    'description': 'Well-maintained, recently serviced',
    'hourly_rate': 50,
    'daily_rate': 150,
    'weekly_rate': 800,
    'monthly_rate': 2500,
    'deposit_amount': 500,
    'terms': [
        'Fuel not included',
        'Return clean',
        'Late fee: $50/day'
    ],
    'availability': 'Monday-Friday'
}
