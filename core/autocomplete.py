# core/autocomplete.py
"""
Intelligent Auto-Completion Service
Learns from user behavior and suggests completions
"""

from django.db.models import F, Q
from django.utils import timezone
from .models import UserHistory, FarmHistory, Farm, User
from decimal import Decimal


class AutoCompleteService:
    """Machine learning auto-completion service"""
    
    LEARNING_WEIGHTS = {
        'user_history': 0.50,      # User's own history
        'farm_history': 0.25,      # Farm's history
        'cooperative': 0.15,       # Cooperative members' trends
        'regional': 0.10,          # Regional trends
    }
    
    @staticmethod
    def record_field_value(
        user: User,
        farm: Farm,
        field_name: str,
        field_value: str,
        is_successful: bool = True
    ) -> None:
        """
        Record a field value for learning
        
        Args:
            user: User entering the value
            farm: Farm context
            field_name: Name of the field
            field_value: The value entered
            is_successful: Whether it was a successful entry
        """
        
        # Update user history
        user_history, created = UserHistory.objects.get_or_create(
            user=user,
            field_name=field_name,
            field_value=field_value,
            defaults={'usage_count': 1}
        )
        
        if not created:
            user_history.usage_count += 1
            user_history.last_used = timezone.now()
        
        # Update success rate
        if is_successful:
            if user_history.success_rate is None or user_history.success_rate == 0:
                user_history.success_rate = Decimal('100')
            else:
                # Weighted average
                user_history.success_rate = (
                    (user_history.success_rate * (user_history.usage_count - 1) + 100) / 
                    user_history.usage_count
                )
        
        user_history.save()
        
        # Update farm history
        farm_history, created = FarmHistory.objects.get_or_create(
            farm=farm,
            field_name=field_name,
            field_value=field_value,
            defaults={'usage_count': 1}
        )
        
        if not created:
            farm_history.usage_count += 1
            farm_history.last_used = timezone.now()
        
        if is_successful:
            if farm_history.success_rate is None or farm_history.success_rate == 0:
                farm_history.success_rate = Decimal('100')
            else:
                farm_history.success_rate = (
                    (farm_history.success_rate * (farm_history.usage_count - 1) + 100) / 
                    farm_history.usage_count
                )
        
        farm_history.save()
    
    @staticmethod
    def get_user_suggestions(
        user: User,
        field_name: str,
        limit: int = 10
    ) -> list:
        """
        Get auto-completion suggestions from user history
        
        Returns list of dicts with: value, score, usage_count, success_rate
        """
        
        histories = UserHistory.objects.filter(
            user=user,
            field_name=field_name
        ).order_by('-last_used')[:limit]
        
        suggestions = []
        for history in histories:
            score = history.usage_count * (float(history.success_rate) / 100) \
                if history.success_rate else history.usage_count
            
            suggestions.append({
                'value': history.field_value,
                'score': float(score),
                'usage_count': history.usage_count,
                'success_rate': float(history.success_rate) if history.success_rate else 0,
                'last_used': history.last_used.isoformat(),
                'source': 'user',
                'weight': AutoCompleteService.LEARNING_WEIGHTS['user_history']
            })
        
        # Sort by score descending
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions
    
    @staticmethod
    def get_farm_suggestions(
        farm: Farm,
        field_name: str,
        limit: int = 10
    ) -> list:
        """
        Get auto-completion suggestions from farm history
        """
        
        histories = FarmHistory.objects.filter(
            farm=farm,
            field_name=field_name
        ).order_by('-last_used')[:limit]
        
        suggestions = []
        for history in histories:
            score = history.usage_count * (float(history.success_rate) / 100) \
                if history.success_rate else history.usage_count
            
            suggestions.append({
                'value': history.field_value,
                'score': float(score),
                'usage_count': history.usage_count,
                'success_rate': float(history.success_rate) if history.success_rate else 0,
                'last_used': history.last_used.isoformat(),
                'source': 'farm',
                'weight': AutoCompleteService.LEARNING_WEIGHTS['farm_history']
            })
        
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        return suggestions
    
    @staticmethod
    def get_cooperative_suggestions(
        farm: Farm,
        field_name: str,
        limit: int = 10
    ) -> list:
        """
        Get suggestions from other cooperative members (if in cooperative)
        """
        
        if not farm.cooperative:
            return []
        
        # Get farms in same cooperative
        coop_farms = Farm.objects.filter(
            cooperative=farm.cooperative
        ).exclude(id=farm.id)
        
        # Get most common values in cooperative
        histories = FarmHistory.objects.filter(
            farm__in=coop_farms,
            field_name=field_name
        ).values('field_value').annotate(
            total_count=F('usage_count')
        ).order_by('-total_count')[:limit]
        
        suggestions = []
        for hist in histories:
            suggestions.append({
                'value': hist['field_value'],
                'score': float(hist['total_count']),
                'usage_count': hist['total_count'],
                'source': 'cooperative',
                'weight': AutoCompleteService.LEARNING_WEIGHTS['cooperative']
            })
        
        return suggestions
    
    @staticmethod
    def get_combined_suggestions(
        user: User,
        farm: Farm,
        field_name: str,
        limit: int = 10
    ) -> list:
        """
        Get combined suggestions from all sources with weighted ranking
        """
        
        all_suggestions = {}
        
        # Get suggestions from each source
        user_sugg = AutoCompleteService.get_user_suggestions(user, field_name, limit)
        farm_sugg = AutoCompleteService.get_farm_suggestions(farm, field_name, limit)
        coop_sugg = AutoCompleteService.get_cooperative_suggestions(farm, field_name, limit)
        
        # Combine and weight
        for sugg in user_sugg:
            key = sugg['value']
            if key not in all_suggestions:
                all_suggestions[key] = {
                    'value': key,
                    'weighted_score': 0,
                    'sources': []
                }
            all_suggestions[key]['weighted_score'] += sugg['score'] * sugg['weight']
            all_suggestions[key]['sources'].append('user')
        
        for sugg in farm_sugg:
            key = sugg['value']
            if key not in all_suggestions:
                all_suggestions[key] = {
                    'value': key,
                    'weighted_score': 0,
                    'sources': []
                }
            all_suggestions[key]['weighted_score'] += sugg['score'] * sugg['weight']
            all_suggestions[key]['sources'].append('farm')
        
        for sugg in coop_sugg:
            key = sugg['value']
            if key not in all_suggestions:
                all_suggestions[key] = {
                    'value': key,
                    'weighted_score': 0,
                    'sources': []
                }
            all_suggestions[key]['weighted_score'] += sugg['score'] * sugg['weight']
            all_suggestions[key]['sources'].append('cooperative')
        
        # Convert to list and sort by weighted score
        result = list(all_suggestions.values())
        result.sort(key=lambda x: x['weighted_score'], reverse=True)
        
        return result[:limit]
    
    @staticmethod
    def get_field_auto_fill(
        farm: Farm,
        field_name: str
    ) -> dict:
        """
        Get recommended values for auto-filling dependent fields
        when a user selects a value
        
        Example: Select "Maize" -> suggests default spacing, depth, seed rate
        """
        
        auto_fill_rules = {
            'crop_type': {
                'Maize': {
                    'planting_depth_cm': '5',
                    'spacing_cm': '75x25',
                    'seed_rate_kg_per_ha': '25',
                    'optimal_temp_min': '20',
                    'optimal_temp_max': '28',
                    'growing_days': '120'
                },
                'Beans': {
                    'planting_depth_cm': '4',
                    'spacing_cm': '60x20',
                    'seed_rate_kg_per_ha': '40',
                    'optimal_temp_min': '18',
                    'optimal_temp_max': '25',
                    'growing_days': '90'
                },
                'Tomatoes': {
                    'planting_depth_cm': '3',
                    'spacing_cm': '50x50',
                    'seed_rate_kg_per_ha': '1',
                    'optimal_temp_min': '20',
                    'optimal_temp_max': '30',
                    'growing_days': '80'
                }
            },
            'fertilizer_type': {
                'DAP': {'cost_per_unit': '0.50', 'unit': 'kg'},
                'NPK': {'cost_per_unit': '0.55', 'unit': 'kg'},
                'Urea': {'cost_per_unit': '0.45', 'unit': 'kg'},
            }
        }
        
        return auto_fill_rules.get(field_name, {})
    
    @staticmethod
    def clear_user_history(user: User, field_name: str = None) -> int:
        """
        Clear user history (for privacy/reset)
        Returns count of deleted records
        """
        
        if field_name:
            count, _ = UserHistory.objects.filter(
                user=user,
                field_name=field_name
            ).delete()
        else:
            count, _ = UserHistory.objects.filter(
                user=user
            ).delete()
        
        return count
