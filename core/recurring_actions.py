# core/recurring_actions.py
"""
One-Click Recurring Actions Service
Automate repetitive tasks
"""

from django.utils import timezone
from django.db import models
from datetime import datetime, timedelta, time
from typing import Dict, Any, List, Optional
import croniter
from .models import Farm, User


class RecurringActionService:
    """Manage recurring actions"""
    
    FREQUENCIES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('seasonal', 'Seasonal'),
    ]
    
    @staticmethod
    def create_recurring_action(
        farm: Farm,
        action_name: str,
        description: str = '',
        frequency: str = 'daily',
        time_of_day: time = None,
        days_of_week: List[int] = None,  # 0=Monday, 6=Sunday
        day_of_month: int = None,
        assigned_to: User = None,
        reminder_minutes_before: int = 15,
        start_date: datetime = None,
        end_date: datetime = None,
        cron_expression: str = None,
        action_data: Dict[str, Any] = None,
    ) -> 'RecurringAction':
        """
        Create a recurring action
        
        Args:
            farm: Farm for the action
            action_name: Name of the action
            frequency: daily, weekly, monthly, seasonal
            time_of_day: Time to perform action (e.g., 08:00)
            days_of_week: For weekly (0=Mon, 6=Sun)
            day_of_month: For monthly (1-31)
            assigned_to: User to assign to
            reminder_minutes_before: Minutes before to send reminder
            start_date: When to start recurring
            end_date: When to stop recurring
            cron_expression: Optional cron schedule
            action_data: Additional data (field values, etc.)
        """
        
        from .models import RecurringAction
        
        if start_date is None:
            start_date = timezone.now()
        
        # Generate CRON expression if not provided
        if cron_expression is None:
            cron_expression = RecurringActionService._generate_cron(
                frequency, time_of_day, days_of_week, day_of_month
            )
        
        action = RecurringAction.objects.create(
            farm=farm,
            action_name=action_name,
            description=description,
            frequency=frequency,
            time_of_day=time_of_day or time(8, 0),
            days_of_week=days_of_week or [],
            day_of_month=day_of_month,
            assigned_to=assigned_to,
            reminder_minutes_before=reminder_minutes_before,
            start_date=start_date,
            end_date=end_date,
            cron_expression=cron_expression,
            action_data=action_data or {},
            is_active=True,
            paused_at=None
        )
        
        return action
    
    @staticmethod
    def _generate_cron(
        frequency: str,
        time_of_day: time = None,
        days_of_week: List[int] = None,
        day_of_month: int = None
    ) -> str:
        """Generate cron expression from recurrence parameters"""
        
        if time_of_day is None:
            time_of_day = time(8, 0)
        
        hour = time_of_day.hour
        minute = time_of_day.minute
        
        if frequency == 'daily':
            return f"{minute} {hour} * * *"
        elif frequency == 'weekly':
            days = ','.join(str(d) for d in (days_of_week or [0]))
            return f"{minute} {hour} * * {days}"
        elif frequency == 'monthly':
            day = day_of_month or 1
            return f"{minute} {hour} {day} * *"
        elif frequency == 'seasonal':
            # Seasonal: run on specific day of month quarterly (Jan, Apr, Jul, Oct)
            day = day_of_month or 1
            return f"{minute} {hour} {day} 1,4,7,10 *"
        
        return "0 8 * * *"  # Default: daily at 8am
    
    @staticmethod
    def get_due_actions(
        farm: Farm,
        check_at: datetime = None
    ) -> List['RecurringAction']:
        """
        Get actions that are due to run
        """
        
        from .models import RecurringAction, RecurringActionLog
        
        if check_at is None:
            check_at = timezone.now()
        
        due_actions = []
        
        active_actions = RecurringAction.objects.filter(
            farm=farm,
            is_active=True,
            paused_at__isnull=True,
            start_date__lte=check_at
        ).exclude(end_date__lt=check_at)
        
        for action in active_actions:
            # Check if action should run at this time
            try:
                cron = croniter.croniter(action.cron_expression, check_at)
                last_execution = cron.get_prev(datetime)
                
                # Check if last execution was very recent (within 5 minutes)
                time_since_last = check_at - last_execution
                
                # Also check if we've already logged this execution
                already_logged = RecurringActionLog.objects.filter(
                    action=action,
                    created_at__gte=last_execution - timedelta(minutes=5),
                    status='completed'
                ).exists()
                
                if time_since_last < timedelta(minutes=5) and not already_logged:
                    due_actions.append(action)
            except Exception as e:
                print(f"Error checking cron for action {action.id}: {e}")
                continue
        
        return due_actions
    
    @staticmethod
    def execute_action(
        action_id: int,
        executed_by: User = None,
        notes: str = ''
    ) -> 'RecurringActionLog':
        """
        Execute/complete a recurring action
        Returns log entry
        """
        
        from .models import RecurringAction, RecurringActionLog
        
        action = RecurringAction.objects.get(id=action_id)
        
        log_entry = RecurringActionLog.objects.create(
            action=action,
            executed_by=executed_by,
            executed_at=timezone.now(),
            status='completed',
            notes=notes
        )
        
        return log_entry
    
    @staticmethod
    def mark_missed(
        action_id: int,
        notes: str = ''
    ) -> 'RecurringActionLog':
        """Mark an action as missed"""
        
        from .models import RecurringAction, RecurringActionLog
        
        action = RecurringAction.objects.get(id=action_id)
        
        log_entry = RecurringActionLog.objects.create(
            action=action,
            executed_at=timezone.now(),
            status='missed',
            notes=notes
        )
        
        return log_entry
    
    @staticmethod
    def pause_action(action_id: int) -> None:
        """Pause a recurring action"""
        
        from .models import RecurringAction
        
        action = RecurringAction.objects.get(id=action_id)
        action.paused_at = timezone.now()
        action.save()
    
    @staticmethod
    def resume_action(action_id: int) -> None:
        """Resume a paused action"""
        
        from .models import RecurringAction
        
        action = RecurringAction.objects.get(id=action_id)
        action.paused_at = None
        action.save()
    
    @staticmethod
    def get_action_history(
        action_id: int,
        days: int = 30
    ) -> List['RecurringActionLog']:
        """Get execution history for an action"""
        
        from .models import RecurringActionLog
        
        start_date = timezone.now() - timedelta(days=days)
        
        return RecurringActionLog.objects.filter(
            action_id=action_id,
            created_at__gte=start_date
        ).order_by('-created_at')
    
    @staticmethod
    def get_action_stats(
        farm: Farm,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get statistics about recurring actions on a farm"""
        
        from .models import RecurringAction, RecurringActionLog
        
        start_date = timezone.now() - timedelta(days=days)
        
        actions = RecurringAction.objects.filter(farm=farm)
        logs = RecurringActionLog.objects.filter(
            action__farm=farm,
            created_at__gte=start_date
        )
        
        stats = {
            'total_actions': actions.count(),
            'active_actions': actions.filter(paused_at__isnull=True).count(),
            'paused_actions': actions.filter(paused_at__isnull=False).count(),
            'total_executions': logs.count(),
            'completed': logs.filter(status='completed').count(),
            'missed': logs.filter(status='missed').count(),
            'failed': logs.filter(status='failed').count(),
            'completion_rate': 0
        }
        
        if logs.count() > 0:
            stats['completion_rate'] = (
                logs.filter(status='completed').count() / logs.count() * 100
            )
        
        return stats


# Example: Daily chicken feeding action
DAILY_FEEDING_EXAMPLE = {
    'action_name': 'Feed chickens',
    'description': 'Morning and evening chicken feeding',
    'frequency': 'daily',
    'times': ['08:00', '17:00'],  # Morning and evening
    'assigned_to': 'Farm Worker',
    'action_data': {
        'animal_type': 'chicken',
        'quantity_kg': 5,
        'feed_type': 'Layer mash'
    }
}

# Example: Weekly equipment cleaning
WEEKLY_CLEANING_EXAMPLE = {
    'action_name': 'Clean tractor',
    'description': 'Weekly tractor maintenance cleaning',
    'frequency': 'weekly',
    'day_of_week': 0,  # Monday
    'time': '09:00',
    'assigned_to': 'Maintenance Team',
    'reminder_minutes_before': 60,
    'action_data': {
        'equipment_id': 'tractor_123',
        'task': 'full_cleaning',
        'estimated_time_hours': 2
    }
}

# Example: Monthly inventory check
MONTHLY_INVENTORY_EXAMPLE = {
    'action_name': 'Inventory count',
    'description': 'Monthly farm inventory count',
    'frequency': 'monthly',
    'day_of_month': 1,
    'time': '08:00',
    'assigned_to': 'Farm Manager',
    'action_data': {
        'check_items': ['seed', 'fertilizer', 'pesticide', 'equipment']
    }
}
