# core/analytics/views.py
# REST API views for analytics endpoints

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Min, Max, Count
from django.utils import timezone
from datetime import timedelta

from core.models_analytics import (
    DashboardMetric, MetricHistory, YieldPrediction,
    ResourceUsageAnalytics, FarmPerformanceScore, AlertTrigger,
    BenchmarkComparison, AnalyticsReport, NotificationQueue
)
from core.models import Farm

from .serializers import (
    DashboardMetricSerializer, MetricHistorySerializer,
    YieldPredictionSerializer, ResourceUsageAnalyticsSerializer,
    FarmPerformanceScoreSerializer, AlertTriggerSerializer,
    BenchmarkComparisonSerializer, AnalyticsReportSerializer,
    NotificationQueueSerializer
)


# ============================================================
# DASHBOARD METRICS VIEWSET
# ============================================================

class DashboardMetricViewSet(viewsets.ModelViewSet):
    """
    ViewSet for real-time dashboard metrics.
    
    List filters:
    - farm_id: Filter by farm
    - metric_type: Filter by metric type
    - severity: Filter by severity level
    """
    
    serializer_class = DashboardMetricSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['farm_id', 'metric_type', 'severity']
    ordering_fields = ['-timestamp', 'metric_type']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Only return metrics for current user's farms"""
        return DashboardMetric.objects.filter(
            user=self.request.user
        ).select_related('farm', 'field')
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest metric for each type"""
        farm_id = request.query_params.get('farm_id')
        
        queryset = self.get_queryset()
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        
        latest_metrics = []
        metric_types = DashboardMetric.METRIC_TYPES
        
        for metric_type, _ in metric_types:
            metric = queryset.filter(metric_type=metric_type).latest('timestamp', default=None)
            if metric:
                latest_metrics.append(metric)
        
        serializer = self.get_serializer(latest_metrics, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def with_alerts(self, request):
        """Get metrics that are currently triggering alerts"""
        queryset = self.get_queryset().filter(severity__in=['warning', 'critical'])
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ============================================================
# METRIC HISTORY VIEWSET
# ============================================================

class MetricHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for historical metric data and trends.
    
    List filters:
    - farm_id: Filter by farm
    - metric_type: Filter by metric type
    - period: Filter by time period (hourly, daily, weekly, monthly)
    """
    
    serializer_class = MetricHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['farm_id', 'metric_type', 'period']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """Only return history for current user's farms"""
        return MetricHistory.objects.filter(
            user=self.request.user
        ).select_related('farm', 'field')
    
    @action(detail=False, methods=['get'])
    def trends(self, request):
        """Get trending metrics over past 30 days"""
        farm_id = request.query_params.get('farm_id')
        metric_type = request.query_params.get('metric_type')
        
        queryset = self.get_queryset()
        queryset = queryset.filter(
            period='daily',
            timestamp__gte=timezone.now() - timedelta(days=30)
        )
        
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        
        if metric_type:
            queryset = queryset.filter(metric_type=metric_type)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ============================================================
# YIELD PREDICTION VIEWSET
# ============================================================

class YieldPredictionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for yield predictions and actual vs predicted analysis.
    """
    
    serializer_class = YieldPredictionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['farm_id', 'field_id', 'crop_id', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only return predictions for current user"""
        return YieldPrediction.objects.filter(
            user=self.request.user
        ).select_related('farm', 'field', 'crop')
    
    @action(detail=True, methods=['post'])
    def record_harvest(self, request, pk=None):
        """Record actual yield after harvest"""
        prediction = self.get_object()
        
        actual_yield = request.data.get('actual_yield_kg_ha')
        if not actual_yield:
            return Response(
                {'error': 'actual_yield_kg_ha required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prediction.actual_yield_kg_ha = actual_yield
        prediction.harvest_date = timezone.now().date()
        accuracy = prediction.calculate_accuracy()
        
        serializer = self.get_serializer(prediction)
        return Response({
            **serializer.data,
            'message': f'Accuracy calculated: {accuracy}%'
        })
    
    @action(detail=False, methods=['get'])
    def accuracy_stats(self, request):
        """Get accuracy statistics for all past predictions"""
        predictions = self.get_queryset().filter(
            actual_yield_kg_ha__isnull=False
        )
        
        avg_accuracy = predictions.aggregate(Avg('prediction_accuracy'))['prediction_accuracy__avg']
        total_predictions = predictions.count()
        
        return Response({
            'total_predictions': total_predictions,
            'average_accuracy': avg_accuracy,
            'predictions': YieldPredictionSerializer(predictions, many=True).data
        })


# ============================================================
# FARM PERFORMANCE VIEWSET
# ============================================================

class FarmPerformanceScoreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for farm performance scores and trends.
    """
    
    serializer_class = FarmPerformanceScoreSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['farm_id', 'score_period']
    ordering = ['-period_end']
    
    def get_queryset(self):
        """Only return scores for current user's farms"""
        return FarmPerformanceScore.objects.filter(
            user=self.request.user
        ).select_related('farm')
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current performance score for a farm"""
        farm_id = request.query_params.get('farm_id')
        
        if not farm_id:
            return Response(
                {'error': 'farm_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        score = self.get_queryset().filter(
            farm_id=farm_id
        ).order_by('-period_end').first()
        
        if not score:
            return Response(
                {'error': 'No performance score found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = self.get_serializer(score)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get performance history for a farm"""
        farm_id = request.query_params.get('farm_id')
        period = request.query_params.get('period', 'daily')
        
        if not farm_id:
            return Response(
                {'error': 'farm_id parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            farm_id=farm_id,
            score_period=period
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ============================================================
# ALERT VIEWSET
# ============================================================

class AlertTriggerViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alert triggers.
    """
    
    serializer_class = AlertTriggerSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['farm_id', 'alert_type', 'importance', 'is_resolved']
    search_fields = ['title', 'description']
    ordering = ['-importance', '-created_at']
    
    def get_queryset(self):
        """Only return alerts for current user"""
        return AlertTrigger.objects.filter(
            user=self.request.user
        ).select_related('farm')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active (unresolved) alerts"""
        farm_id = request.query_params.get('farm_id')
        
        queryset = self.get_queryset().filter(is_resolved=False)
        
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark alert as resolved"""
        alert = self.get_object()
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolution_notes = request.data.get('resolution_notes', '')
        alert.save()
        
        serializer = self.get_serializer(alert)
        return Response(serializer.data)


# ============================================================
# ANALYTICS REPORTS VIEWSET
# ============================================================

class AnalyticsReportViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for accessing generated analytics reports.
    """
    
    serializer_class = AnalyticsReportSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['farm_id', 'report_type']
    ordering = ['-generated_at']
    
    def get_queryset(self):
        """Only return reports for current user"""
        return AnalyticsReport.objects.filter(
            user=self.request.user
        ).select_related('farm')
    
    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """Mark report as viewed"""
        report = self.get_object()
        report.last_viewed = timezone.now()
        report.save()
        
        serializer = self.get_serializer(report)
        return Response(serializer.data)


# ============================================================
# NOTIFICATIONS VIEWSET
# ============================================================

class NotificationQueueViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user notifications.
    """
    
    serializer_class = NotificationQueueSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['notification_type', 'severity', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Only return notifications for current user"""
        return NotificationQueue.objects.filter(
            user=self.request.user,
            is_sent=True
        ).select_related('farm')
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        queryset = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'count': queryset.count(),
            'notifications': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read"""
        queryset = self.get_queryset().filter(is_read=False)
        count = queryset.count()
        
        queryset.update(is_read=True, read_at=timezone.now())
        
        return Response({
            'message': f'{count} notifications marked as read',
            'count': count
        })
