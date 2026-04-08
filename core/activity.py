# core/activity.py
"""
Unified Activity Timeline Service
Tracks all activities across the system
"""

from django.db.models import Q
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

from .models import AuditLog, Farm, User


class ActivityTimelineService:
    """Service for managing and querying activity timeline"""
    
    ACTIVITY_TYPES = {
        'crop.planted': {'icon': '🌾', 'severity': 'normal'},
        'crop.harvested': {'icon': '🌾', 'severity': 'normal'},
        'crop.fertilized': {'icon': '🥗', 'severity': 'normal'},
        'crop.irrigated': {'icon': '💧', 'severity': 'normal'},
        'crop.treated': {'icon': '🧪', 'severity': 'high'},
        
        'livestock.added': {'icon': '🐄', 'severity': 'normal'},
        'livestock.vaccinated': {'icon': '💉', 'severity': 'normal'},
        'livestock.bred': {'icon': '👶', 'severity': 'normal'},
        'livestock.sold': {'icon': '💰', 'severity': 'normal'},
        'livestock.weighed': {'icon': '⚖️', 'severity': 'normal'},
        'livestock.treated': {'icon': '🧪', 'severity': 'high'},
        
        'equipment.rented': {'icon': '🚜', 'severity': 'normal'},
        'equipment.returned': {'icon': '🚜', 'severity': 'normal'},
        'equipment.serviced': {'icon': '🔧', 'severity': 'normal'},
        'equipment.repaired': {'icon': '🔨', 'severity': 'high'},
        
        'labor.worker_added': {'icon': '👤', 'severity': 'normal'},
        'labor.hours_logged': {'icon': '⏱️', 'severity': 'normal'},
        'labor.payroll_processed': {'icon': '💵', 'severity': 'normal'},
        
        'financial.income_recorded': {'icon': '💰', 'severity': 'normal'},
        'financial.expense_recorded': {'icon': '💸', 'severity': 'normal'},
        'financial.refund_issued': {'icon': '💳', 'severity': 'high'},
        
        'marketplace.product_listed': {'icon': '📦', 'severity': 'normal'},
        'marketplace.product_sold': {'icon': '📦', 'severity': 'normal'},
        'marketplace.order_placed': {'icon': '🛒', 'severity': 'normal'},
        'marketplace.shipping_update': {'icon': '🚚', 'severity': 'normal'},
        
        'pest.report_submitted': {'icon': '🐛', 'severity': 'high'},
        'pest.analysis_completed': {'icon': '🔬', 'severity': 'normal'},
        'pest.verified': {'icon': '✅', 'severity': 'normal'},
        
        'weather.alert_received': {'icon': '⛈️', 'severity': 'high'},
        'weather.action_taken': {'icon': '🛡️', 'severity': 'normal'},
        
        'insurance.policy_purchased': {'icon': '📋', 'severity': 'normal'},
        'insurance.claim_filed': {'icon': '📝', 'severity': 'high'},
        'insurance.claim_paid': {'icon': '💰', 'severity': 'normal'},
        
        'communication.email_sent': {'icon': '📧', 'severity': 'normal'},
        'communication.sms_sent': {'icon': '📱', 'severity': 'normal'},
        'communication.notification_sent': {'icon': '🔔', 'severity': 'normal'},
    }
    
    @staticmethod
    def log_activity(
        user: User,
        activity_type: str,
        farm: Farm,
        title: str,
        description: str = '',
        metadata: Dict[str, Any] = None,
        severity: str = 'normal',
        related_object_id: str = None,
        related_model: str = None
    ) -> AuditLog:
        """
        Log an activity
        
        Args:
            user: User performing the action
            activity_type: Type of activity (e.g., 'crop.planted')
            farm: Farm where activity occurred
            title: Human-readable title
            description: Detailed description
            metadata: Additional data (as dict)
            severity: 'critical', 'high', 'normal', 'low'
            related_object_id: ID of related object
            related_model: Model name of related object
        
        Returns: Created AuditLog instance
        """
        
        if metadata is None:
            metadata = {}
        
        # Extract icon and default severity
        activity_info = ActivityTimelineService.ACTIVITY_TYPES.get(activity_type, {})
        if not severity or severity == 'normal':
            severity = activity_info.get('severity', 'normal')
        
        activity = AuditLog.objects.create(
            user=user,
            action='activity',
            model_name=activity_type,
            object_id=str(farm.id),
            details={
                'activity_type': activity_type,
                'farm_id': str(farm.id),
                'farm_name': farm.name,
                'title': title,
                'description': description,
                'severity': severity,
                'icon': activity_info.get('icon', '📋'),
                'related_object_id': related_object_id,
                'related_model': related_model,
                'metadata': metadata,
            }
        )
        
        return activity
    
    @staticmethod
    def get_farm_timeline(
        farm: Farm,
        days: int = 30,
        activity_types: List[str] = None,
        status: str = None,
        severity: str = None
    ) -> List[AuditLog]:
        """
        Get activities for a specific farm
        
        Args:
            farm: Farm to get timeline for
            days: Number of days to look back (default 30)
            activity_types: Filter by activity types (optional)
            status: Filter by status (optional)
            severity: Filter by severity (optional)
        
        Returns: List of activities
        """
        
        start_date = timezone.now() - timedelta(days=days)
        
        query = AuditLog.objects.filter(
            object_id=str(farm.id),
            action='activity',
            created_at__gte=start_date
        ).order_by('-created_at')
        
        if activity_types:
            query = query.filter(model_name__in=activity_types)
        
        if severity:
            query = query.filter(details__severity=severity)
        
        return list(query)
    
    @staticmethod
    def get_asset_timeline(
        asset_type: str,
        asset_id: str,
        days: int = 365
    ) -> List[AuditLog]:
        """
        Get history of a specific asset (animal, field, equipment)
        
        Args:
            asset_type: 'animal', 'field', 'equipment'
            asset_id: ID of the asset
            days: Number of days to look back
        
        Returns: List of activities
        """
        
        start_date = timezone.now() - timedelta(days=days)
        
        query = AuditLog.objects.filter(
            details__related_model=asset_type,
            details__related_object_id=asset_id,
            created_at__gte=start_date,
            action='activity'
        ).order_by('-created_at')
        
        return list(query)
    
    @staticmethod
    def get_user_timeline(
        user: User,
        days: int = 30,
        activity_types: List[str] = None
    ) -> List[AuditLog]:
        """
        Get all activities by a user
        
        Args:
            user: User to get activities for
            days: Number of days to look back
            activity_types: Filter by activity types
        
        Returns: List of activities
        """
        
        start_date = timezone.now() - timedelta(days=days)
        
        query = AuditLog.objects.filter(
            user=user,
            action='activity',
            created_at__gte=start_date
        ).order_by('-created_at')
        
        if activity_types:
            query = query.filter(model_name__in=activity_types)
        
        return list(query)
    
    @staticmethod
    def search_activities(
        farm: Farm,
        query_text: str,
        days: int = 30
    ) -> List[AuditLog]:
        """
        Search activities by keyword
        
        Args:
            farm: Farm to search in
            query_text: Search term
            days: Number of days to look back
        
        Returns: List of matching activities
        """
        
        start_date = timezone.now() - timedelta(days=days)
        
        activities = AuditLog.objects.filter(
            object_id=str(farm.id),
            action='activity',
            created_at__gte=start_date
        ).order_by('-created_at')
        
        results = []
        for activity in activities:
            details = activity.details or {}
            title = details.get('title', '').lower()
            description = details.get('description', '').lower()
            activity_type = details.get('activity_type', '').lower()
            
            if (query_text.lower() in title or 
                query_text.lower() in description or 
                query_text.lower() in activity_type):
                results.append(activity)
        
        return results
    
    @staticmethod
    def get_high_priority_activities(user: User) -> List[AuditLog]:
        """Get recent critical or high-severity activities"""
        
        start_date = timezone.now() - timedelta(days=7)
        
        activities = AuditLog.objects.filter(
            user=user,
            action='activity',
            created_at__gte=start_date
        ).filter(
            Q(details__severity='critical') | Q(details__severity='high')
        ).order_by('-created_at')
        
        return list(activities)
    
    @staticmethod
    def get_activity_stats(farm: Farm, days: int = 30) -> Dict[str, Any]:
        """
        Get activity statistics for a farm
        
        Args:
            farm: Farm to analyze
            days: Number of days to look back
        
        Returns: Statistics dictionary
        """
        
        start_date = timezone.now() - timedelta(days=days)
        
        activities = AuditLog.objects.filter(
            object_id=str(farm.id),
            action='activity',
            created_at__gte=start_date
        )
        
        stats = {
            'total_activities': activities.count(),
            'by_type': {},
            'by_severity': {'critical': 0, 'high': 0, 'normal': 0, 'low': 0},
            'by_date': {},
            'most_active_day': None,
            'active_users': set()
        }
        
        for activity in activities:
            details = activity.details or {}
            
            # Count by type
            activity_type = details.get('activity_type', 'unknown')
            stats['by_type'][activity_type] = stats['by_type'].get(activity_type, 0) + 1
            
            # Count by severity
            severity = details.get('severity', 'normal')
            stats['by_severity'][severity] += 1
            
            # Count by date
            date_key = activity.created_at.date().isoformat()
            stats['by_date'][date_key] = stats['by_date'].get(date_key, 0) + 1
            
            # Track active users
            if activity.user:
                stats['active_users'].add(activity.user.username)
        
        # Convert set to list for JSON serialization
        stats['active_users'] = list(stats['active_users'])
        stats['active_users_count'] = len(stats['active_users'])
        
        # Find most active day
        if stats['by_date']:
            stats['most_active_day'] = max(stats['by_date'], key=stats['by_date'].get)
        
        return stats
    
    @staticmethod
    def format_activity_for_display(activity: AuditLog) -> Dict[str, Any]:
        """Format activity for display in UI"""
        
        details = activity.details or {}
        
        return {
            'id': activity.id,
            'timestamp': activity.created_at.isoformat(),
            'icon': details.get('icon', '📋'),
            'title': details.get('title', 'Activity'),
            'description': details.get('description', ''),
            'type': details.get('activity_type', 'unknown'),
            'severity': details.get('severity', 'normal'),
            'user': activity.user.get_full_name() if activity.user else 'System',
            'farm_name': details.get('farm_name', 'Unknown'),
            'metadata': details.get('metadata', {})
        }
