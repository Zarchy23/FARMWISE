# core/analytics/serializers.py
# Serializers for analytics REST endpoints

from rest_framework import serializers
from core.models_analytics import (
    DashboardMetric, MetricHistory, YieldPrediction,
    ResourceUsageAnalytics, FarmPerformanceScore, AlertTrigger,
    BenchmarkComparison, AnalyticsReport, NotificationQueue
)


class DashboardMetricSerializer(serializers.ModelSerializer):
    """Serialize real-time dashboard metrics"""
    
    metric_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = DashboardMetric
        fields = [
            'id', 'metric_type', 'metric_display', 'value', 'unit',
            'severity', 'severity_display', 'threshold_warning',
            'threshold_critical', 'timestamp', 'last_updated'
        ]
        read_only_fields = ['id', 'timestamp', 'last_updated']


class MetricHistorySerializer(serializers.ModelSerializer):
    """Serialize historical metric data"""
    
    metric_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    
    class Meta:
        model = MetricHistory
        fields = [
            'id', 'metric_type', 'metric_display', 'value_avg', 'value_min',
            'value_max', 'value_latest', 'period', 'period_display', 'timestamp',
            'data_points'
        ]
        read_only_fields = ['id']


class YieldPredictionSerializer(serializers.ModelSerializer):
    """Serialize yield predictions"""
    
    crop_name = serializers.CharField(source='crop.name', read_only=True)
    field_name = serializers.CharField(source='field.name', read_only=True)
    
    class Meta:
        model = YieldPrediction
        fields = [
            'id', 'crop', 'crop_name', 'field', 'field_name',
            'predicted_yield_kg_ha', 'confidence_score', 'actual_yield_kg_ha',
            'prediction_accuracy', 'factors', 'status', 'created_at',
            'harvest_date', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ResourceUsageAnalyticsSerializer(serializers.ModelSerializer):
    """Serialize resource usage tracking"""
    
    resource_display = serializers.CharField(source='get_resource_type_display', read_only=True)
    
    class Meta:
        model = ResourceUsageAnalytics
        fields = [
            'id', 'resource_type', 'resource_display', 'quantity_used',
            'quantity_available', 'cost_per_unit', 'total_cost', 'date_used', 'notes'
        ]
        read_only_fields = ['id', 'date_used']


class FarmPerformanceScoreSerializer(serializers.ModelSerializer):
    """Serialize farm performance scores"""
    
    trend_display = serializers.CharField(source='get_score_trend_display', read_only=True)
    period_display = serializers.CharField(source='get_score_period_display', read_only=True)
    rating = serializers.SerializerMethodField()
    
    class Meta:
        model = FarmPerformanceScore
        fields = [
            'id', 'health_score', 'soil_health', 'water_efficiency',
            'pest_disease_control', 'yield_performance', 'cost_efficiency',
            'sustainability', 'score_trend', 'trend_display', 'score_period',
            'period_display', 'period_start', 'period_end', 'recommendations',
            'rating', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_rating(self, obj):
        """Get text rating based on score"""
        return obj.get_rating()


class AlertTriggerSerializer(serializers.ModelSerializer):
    """Serialize alert triggers"""
    
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    importance_display = serializers.CharField(source='get_importance_display', read_only=True)
    
    class Meta:
        model = AlertTrigger
        fields = [
            'id', 'alert_type', 'alert_type_display', 'importance',
            'importance_display', 'title', 'description', 'recommended_actions',
            'is_resolved', 'resolved_at', 'resolution_notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class BenchmarkComparisonSerializer(serializers.ModelSerializer):
    """Serialize benchmark comparisons"""
    
    crop_name = serializers.CharField(source='crop.name', read_only=True)
    
    class Meta:
        model = BenchmarkComparison
        fields = [
            'id', 'crop', 'crop_name', 'benchmark_yield_kg_ha',
            'farm_yield_kg_ha', 'yield_performance_vs_benchmark',
            'benchmark_water_liters_per_ha', 'farm_water_liters_per_ha',
            'water_efficiency_vs_benchmark', 'benchmark_cost_per_ha',
            'farm_cost_per_ha', 'cost_efficiency_vs_benchmark',
            'region', 'age_group', 'comparison_date'
        ]
        read_only_fields = ['id', 'comparison_date']


class AnalyticsReportSerializer(serializers.ModelSerializer):
    """Serialize analytics reports"""
    
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    
    class Meta:
        model = AnalyticsReport
        fields = [
            'id', 'report_type', 'report_type_display', 'title', 'summary',
            'findings', 'recommendations', 'visualizations', 'report_file',
            'period_start', 'period_end', 'generated_at', 'last_viewed'
        ]
        read_only_fields = ['id', 'generated_at']


class NotificationQueueSerializer(serializers.ModelSerializer):
    """Serialize notification queue items"""
    
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = NotificationQueue
        fields = [
            'id', 'notification_type', 'type_display', 'title', 'message',
            'icon', 'severity', 'severity_display', 'is_sent', 'is_read',
            'sent_at', 'read_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# ============================================================
# Aggregate Summary Serializers
# ============================================================

class DashboardSummarySerializer(serializers.Serializer):
    """Summary of all dashboard data"""
    
    metrics = DashboardMetricSerializer(many=True, read_only=True)
    alerts = AlertTriggerSerializer(many=True, read_only=True)
    performance = FarmPerformanceScoreSerializer(read_only=True)
    notifications_count = serializers.SerializerMethodField()
    
    def get_notifications_count(self, obj):
        """Count unread notifications"""
        if hasattr(obj, 'notifications'):
            return obj.notifications.filter(is_read=False).count()
        return 0


class FarmAnalyticsSummarySerializer(serializers.Serializer):
    """Complete farm analytics summary"""
    
    farm_id = serializers.IntegerField()
    farm_name = serializers.CharField()
    
    # Performance
    performance = FarmPerformanceScoreSerializer(read_only=True)
    
    # Latest metrics
    latest_metrics = DashboardMetricSerializer(many=True, read_only=True)
    
    # Yield prediction
    yield_prediction = YieldPredictionSerializer(read_only=True)
    
    # Active alerts
    active_alerts = AlertTriggerSerializer(many=True, read_only=True)
    
    # Resource usage this month
    resource_usage = ResourceUsageAnalyticsSerializer(many=True, read_only=True)
    
    # Benchmarks
    benchmarks = BenchmarkComparisonSerializer(many=True, read_only=True)
