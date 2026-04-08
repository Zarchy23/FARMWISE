# core/views_api.py
"""
Complete API views for FarmWise enhancements (Phases 1-6)
Includes validation, activity timeline, templates, predictions, exports, and workspace management
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q

from .models import (
    AuditLog, ValidationRule, ValidationLog, 
    UserHistory, FarmHistory, Farm,
    HelpContent, Template, TemplateRating, RecurringAction, 
    RecurringActionLog, BatchOperation, Prediction, ScheduledExport, WorkspacePreference
)
from .serializers import (
    ActivityLogSerializer, ValidationRuleSerializer, 
    ValidationLogSerializer, UserHistorySerializer, 
    FarmHistorySerializer
)
from .activity import ActivityTimelineService
from .validators import ValidationEngine


# ============================================================
# PHASE 1: VALIDATION API VIEWS
# ============================================================

class ValidationRuleViewSet(viewsets.ModelViewSet):
    """CRUD for validation rules"""
    
    queryset = ValidationRule.objects.all()
    serializer_class = ValidationRuleSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'is_active']
    search_fields = ['rule_code', 'field_name', 'message']
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return ValidationRule.objects.all()
        return ValidationRule.objects.filter(is_active=True)


class ValidationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View validation logs"""
    
    serializer_class = ValidationLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'rule_code', 'form_or_api']
    search_fields = ['field_name', 'rule_code']
    ordering = ['-created_at']
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return ValidationLog.objects.all()
        return ValidationLog.objects.filter(user=self.request.user)


class ValidateDataAPIView(viewsets.ViewSet):
    """Validate data using the validation engine"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def crop(self, request):
        """Validate crop data"""
        from .validators import get_crop_validators
        engine = get_crop_validators()
        result = engine.get_response(request.data)
        return Response(result, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def livestock(self, request):
        """Validate livestock data"""
        from .validators import get_livestock_validators
        engine = get_livestock_validators()
        result = engine.get_response(request.data)
        return Response(result, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'])
    def marketplace(self, request):
        """Validate marketplace listing data"""
        from .validators import get_marketplace_validators
        engine = get_marketplace_validators()
        result = engine.get_response(request.data)
        return Response(result, status=status.HTTP_200_OK)


# ============================================================
# PHASE 1: ACTIVITY TIMELINE API VIEWS
# ============================================================

class ActivityTimelineViewSet(viewsets.ReadOnlyModelViewSet):
    """Activity timeline with filtering and search"""
    
    serializer_class = ActivityLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['farm', 'severity', 'user']
    search_fields = ['details__title', 'details__description', 'model_name']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user_farms = Farm.objects.filter(owner=self.request.user)
        return AuditLog.objects.filter(
            farm__in=user_farms,
            is_activity=True,
            action='activity'
        ).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def farm_timeline(self, request):
        """Get timeline for a specific farm"""
        farm_id = request.query_params.get('farm_id')
        days = int(request.query_params.get('days', 30))
        
        if not farm_id:
            return Response(
                {'error': 'farm_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
        activities = ActivityTimelineService.get_farm_timeline(
            farm=farm,
            days=days
        )
        
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def asset_timeline(self, request):
        """Get timeline for specific asset"""
        asset_type = request.query_params.get('asset_type')
        asset_id = request.query_params.get('asset_id')
        days = int(request.query_params.get('days', 365))
        
        if not asset_type or not asset_id:
            return Response(
                {'error': 'asset_type and asset_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        activities = ActivityTimelineService.get_asset_timeline(
            asset_type=asset_type,
            asset_id=asset_id,
            days=days
        )
        
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search activities"""
        farm_id = request.query_params.get('farm_id')
        query = request.query_params.get('q', '')
        days = int(request.query_params.get('days', 30))
        
        if not farm_id or not query:
            return Response(
                {'error': 'farm_id and q (search query) are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
        activities = ActivityTimelineService.search_activities(
            farm=farm,
            query_text=query,
            days=days
        )
        
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get activity statistics"""
        farm_id = request.query_params.get('farm_id')
        days = int(request.query_params.get('days', 30))
        
        if not farm_id:
            return Response(
                {'error': 'farm_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
        stats = ActivityTimelineService.get_activity_stats(farm=farm, days=days)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def priority_activities(self, request):
        """Get critical/high priority activities"""
        activities = ActivityTimelineService.get_high_priority_activities(
            user=request.user
        )
        
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)


# ============================================================
# PHASE 1: AUTO-COMPLETION API VIEWS
# ============================================================

class UserHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """User history for auto-completion"""
    
    serializer_class = UserHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserHistory.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Get suggestions for a field"""
        field_name = request.query_params.get('field_name')
        
        if not field_name:
            return Response(
                {'error': 'field_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        histories = UserHistory.objects.filter(
            user=request.user,
            field_name=field_name
        ).order_by('-last_used')[:10]
        
        suggestions = []
        for history in histories:
            suggestions.append({
                'value': history.field_value,
                'count': history.usage_count,
                'success_rate': float(history.success_rate),
                'last_used': history.last_used.isoformat(),
                'score': history.usage_count * (history.success_rate / 100)
            })
        
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return Response({'suggestions': suggestions})


class FarmHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """Farm history for auto-completion"""
    
    serializer_class = FarmHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user_farms = Farm.objects.filter(owner=self.request.user)
        return FarmHistory.objects.filter(farm__in=user_farms)
    
    @action(detail=False, methods=['get'])
    def suggestions(self, request):
        """Get farm-level suggestions for a field"""
        field_name = request.query_params.get('field_name')
        farm_id = request.query_params.get('farm_id')
        
        if not field_name or not farm_id:
            return Response(
                {'error': 'field_name and farm_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
        
        histories = FarmHistory.objects.filter(
            farm=farm,
            field_name=field_name
        ).order_by('-last_used')[:10]
        
        suggestions = []
        for history in histories:
            suggestions.append({
                'value': history.field_value,
                'count': history.usage_count,
                'success_rate': float(history.success_rate),
                'last_used': history.last_used.isoformat(),
                'score': history.usage_count * (history.success_rate / 100)
            })
        
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        
        return Response({'suggestions': suggestions})


# ============================================================
# PHASE 2: CONTEXTUAL HELP SYSTEM
# ============================================================

class HelpContentViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only access to help content"""
    
    queryset = HelpContent.objects.filter(is_active=True)
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'trigger_type', 'content_type']
    search_fields = ['title', 'content']
    
    @action(detail=False, methods=['get'])
    def for_page(self, request):
        """Get help content for a specific page"""
        page = request.query_params.get('page')
        trigger_type = request.query_params.get('trigger', 'manual_request')
        
        if not page:
            return Response({'error': 'page parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        help_items = HelpContent.objects.filter(
            target_page=page,
            trigger_type=trigger_type,
            is_active=True
        ).order_by('-priority')
        
        data = [{
            'id': item.id,
            'title': item.title,
            'content': item.content,
            'content_type': item.content_type,
            'video_url': item.video_url,
            'target_element': item.target_element,
        } for item in help_items]
        
        return Response({'help_items': data})
    
    @action(detail=True, methods=['post'])
    def mark_helpful(self, request, pk=None):
        """Mark help content as helpful"""
        help_item = self.get_object()
        help_item.helpful_count += 1
        help_item.save()
        return Response({'status': 'marked helpful'})


# ============================================================
# PHASE 3: TEMPLATE LIBRARY
# ============================================================

class TemplateViewSet(viewsets.ModelViewSet):
    """Manage and share templates"""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'share_level']
    search_fields = ['name', 'description']
    
    def get_queryset(self):
        user = self.request.user
        return Template.objects.filter(
            Q(user=user) | Q(share_level='public') | Q(share_level='cooperative', farm__cooperative=user.cooperative_member)
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def marketplace(self, request):
        """Get public templates available in marketplace"""
        templates = Template.objects.filter(share_level='public', is_active=True).order_by('-average_rating')
        data = [{
            'id': t.id,
            'name': t.name,
            'category': t.category,
            'description': t.description,
            'price': str(t.price),
            'average_rating': str(t.average_rating),
            'total_ratings': t.total_ratings,
            'usage_count': t.usage_count,
        } for t in templates]
        return Response({'templates': data})
    
    @action(detail=True, methods=['post'])
    def clone(self, request, pk=None):
        """Clone an existing template"""
        template = self.get_object()
        farm_id = request.data.get('farm')
        farm = None
        if farm_id:
            farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
        
        new_template = Template.objects.create(
            user=request.user,
            farm=farm,
            name=f"{template.name} (Copy)",
            category=template.category,
            description=template.description,
            template_data=template.template_data,
            share_level='private'
        )
        return Response({
            'id': new_template.id,
            'name': new_template.name,
            'message': 'Template cloned successfully'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """Record template usage"""
        template = self.get_object()
        template.usage_count += 1
        template.save()
        return Response({'usage_count': template.usage_count})


class TemplateRatingViewSet(viewsets.ModelViewSet):
    """Rate and review templates"""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['template', 'rating']
    
    def get_queryset(self):
        return TemplateRating.objects.all()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ============================================================
# PHASE 3: RECURRING ACTIONS
# ============================================================

class RecurringActionViewSet(viewsets.ModelViewSet):
    """Manage recurring farm actions"""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['farm', 'status', 'frequency']
    ordering_fields = ['next_due', 'created_at', 'frequency']
    
    def get_queryset(self):
        user = self.request.user
        farms = Farm.objects.filter(owner=user)
        return RecurringAction.objects.filter(farm__in=farms)
    
    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Get actions due in the next 24 hours"""
        now = timezone.now()
        soon = now + timedelta(hours=24)
        
        farms = Farm.objects.filter(owner=request.user)
        actions = RecurringAction.objects.filter(
            farm__in=farms,
            status='active',
            next_due__lte=soon,
            next_due__gte=now
        )
        
        return Response([{
            'id': a.id,
            'action_name': a.action_name,
            'next_due': a.next_due,
            'farm': a.farm.id
        } for a in actions])
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Mark action as executed"""
        action = self.get_object()
        action.last_executed = timezone.now()
        action.execution_count += 1
        action.save()
        
        RecurringActionLog.objects.create(
            action=action,
            scheduled_for=action.next_due,
            executed_by=request.user,
            executed_at=timezone.now(),
            status='executed',
            notes=request.data.get('notes', '')
        )
        
        return Response({'status': 'executed', 'count': action.execution_count})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause recurring action"""
        action = self.get_object()
        action.status = 'paused'
        action.paused_at = timezone.now()
        action.save()
        return Response({'status': 'paused'})
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume recurring action"""
        action = self.get_object()
        action.status = 'active'
        action.paused_at = None
        action.save()
        return Response({'status': 'resumed'})


class RecurringActionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """View execution history of recurring actions"""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['action', 'status']
    ordering_fields = ['scheduled_for', 'executed_at']
    
    def get_queryset(self):
        farms = Farm.objects.filter(owner=self.request.user)
        return RecurringActionLog.objects.filter(action__farm__in=farms)


# ============================================================
# PHASE 3: BATCH OPERATIONS
# ============================================================

class BatchOperationViewSet(viewsets.ModelViewSet):
    """Batch operations on multiple records"""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['farm', 'operation_type', 'status']
    ordering_fields = ['created_at', 'status']
    
    def get_queryset(self):
        user = self.request.user
        farms = Farm.objects.filter(owner=user)
        return BatchOperation.objects.filter(farm__in=farms)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get batch operation progress"""
        batch = self.get_object()
        return Response({
            'status': batch.status,
            'progress_percent': batch.progress_percent,
            'record_count': batch.record_count,
            'created_at': batch.created_at,
            'completed_at': batch.completed_at
        })


# ============================================================
# PHASE 4: PREDICTIONS
# ============================================================

class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """View AI/ML predictions for farm decisions"""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['farm', 'prediction_type', 'object_type']
    ordering_fields = ['forecast_date', 'confidence_score']
    
    def get_queryset(self):
        farms = Farm.objects.filter(owner=self.request.user)
        return Prediction.objects.filter(farm__in=farms)
    
    @action(detail=False, methods=['get'])
    def high_confidence(self, request):
        """Get predictions with high confidence"""
        farms = Farm.objects.filter(owner=request.user)
        predictions = Prediction.objects.filter(
            farm__in=farms,
            confidence_score__gt=0.75
        ).order_by('-forecast_date')
        
        return Response([{
            'id': p.id,
            'prediction_type': p.prediction_type,
            'predicted_value': p.predicted_value,
            'confidence_score': str(p.confidence_score),
            'forecast_date': p.forecast_date
        } for p in predictions])
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get predictions grouped by type"""
        pred_type = request.query_params.get('type')
        farms = Farm.objects.filter(owner=request.user)
        
        predictions = Prediction.objects.filter(
            farm__in=farms,
            prediction_type=pred_type
        ).order_by('forecast_date')
        
        return Response([{
            'id': p.id,
            'object_id': p.object_id,
            'predicted_value': p.predicted_value,
            'confidence_score': str(p.confidence_score),
            'forecast_date': p.forecast_date
        } for p in predictions])


# ============================================================
# PHASE 5: SCHEDULED EXPORTS
# ============================================================

class ScheduledExportViewSet(viewsets.ModelViewSet):
    """Manage scheduled data exports"""
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['export_type', 'file_format', 'frequency', 'is_active']
    ordering_fields = ['next_run', 'last_run']
    
    def get_queryset(self):
        return ScheduledExport.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def export_now(self, request, pk=None):
        """Trigger export immediately"""
        export = self.get_object()
        export.last_run = timezone.now()
        export.run_count += 1
        export.save()
        
        return Response({
            'status': 'export queued',
            'export_id': export.id,
            'last_run': export.last_run
        })


# ============================================================
# PHASE 6: WORKSPACE PREFERENCES
# ============================================================

class WorkspacePreferenceViewSet(viewsets.ViewSet):
    """User workspace preferences and switching"""
    
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        obj, created = WorkspacePreference.objects.get_or_create(user=self.request.user)
        return obj
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current workspace preference"""
        pref = self.get_object()
        return Response({
            'primary_workspace': pref.primary_workspace,
            'last_accessed_workspace': pref.last_accessed_workspace,
            'last_accessed_at': pref.last_accessed_at,
            'default_farm': pref.default_farm_id,
            'theme_preference': pref.theme_preference,
        })
    
    @action(detail=False, methods=['post'])
    def switch_workspace(self, request):
        """Switch to a different workspace"""
        workspace_type = request.data.get('workspace_type')
        pref = self.get_object()
        
        valid_types = [w[0] for w in WorkspacePreference.WORKSPACE_TYPES]
        if workspace_type not in valid_types:
            return Response(
                {'error': 'Invalid workspace type'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pref.last_accessed_workspace = workspace_type
        pref.last_accessed_at = timezone.now()
        pref.save()
        
        return Response({
            'current_workspace': workspace_type,
            'switched_at': pref.last_accessed_at
        })
    
    @action(detail=False, methods=['post'])
    def set_default_farm(self, request):
        """Set default farm for workspace"""
        farm_id = request.data.get('farm_id')
        farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
        
        pref = self.get_object()
        pref.default_farm = farm
        pref.save()
        
        return Response({'default_farm': farm.id, 'farm_name': farm.name})
