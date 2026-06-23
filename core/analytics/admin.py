# core/analytics/admin.py
# Django admin configuration for analytics models

from django.contrib import admin
from django.utils import timezone
from core.models_analytics import (
    DashboardMetric, MetricHistory, YieldPrediction,
    ResourceUsageAnalytics, FarmPerformanceScore, AlertTrigger,
    BenchmarkComparison, AnalyticsReport, NotificationQueue
)


@admin.register(DashboardMetric)
class DashboardMetricAdmin(admin.ModelAdmin):
    list_display = ['farm', 'metric_type', 'value', 'severity', 'timestamp']
    list_filter = ['metric_type', 'severity', 'timestamp']
    search_fields = ['farm__name', 'metric_type']
    readonly_fields = ['timestamp', 'last_updated']
    
    fieldsets = (
        ('Farm Information', {
            'fields': ['user', 'farm', 'field']
        }),
        ('Metric Data', {
            'fields': ['metric_type', 'value', 'unit', 'severity']
        }),
        ('Thresholds', {
            'fields': ['threshold_warning', 'threshold_critical']
        }),
        ('Timestamps', {
            'fields': ['timestamp', 'last_updated']
        }),
    )


@admin.register(MetricHistory)
class MetricHistoryAdmin(admin.ModelAdmin):
    list_display = ['farm', 'metric_type', 'period', 'value_avg', 'timestamp']
    list_filter = ['metric_type', 'period', 'timestamp']
    search_fields = ['farm__name']
    readonly_fields = ['created_at']


@admin.register(YieldPrediction)
class YieldPredictionAdmin(admin.ModelAdmin):
    list_display = ['farm', 'crop', 'predicted_yield_kg_ha', 'confidence_score', 'status']
    list_filter = ['crop', 'status', 'created_at']
    search_fields = ['farm__name', 'crop__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Farm Information', {
            'fields': ['user', 'farm', 'field', 'crop']
        }),
        ('Prediction', {
            'fields': ['predicted_yield_kg_ha', 'confidence_score', 'factors', 'status']
        }),
        ('Actual Results', {
            'fields': ['actual_yield_kg_ha', 'prediction_accuracy', 'harvest_date']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    )


@admin.register(ResourceUsageAnalytics)
class ResourceUsageAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['farm', 'resource_type', 'quantity_used', 'total_cost', 'date_used']
    list_filter = ['resource_type', 'date_used']
    search_fields = ['farm__name']
    readonly_fields = ['date_used']


@admin.register(FarmPerformanceScore)
class FarmPerformanceScoreAdmin(admin.ModelAdmin):
    list_display = ['farm', 'health_score', 'soil_health', 'score_trend', 'period_end']
    list_filter = ['score_period', 'score_trend', 'period_end']
    search_fields = ['farm__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Farm Information', {
            'fields': ['user', 'farm']
        }),
        ('Overall Score', {
            'fields': ['health_score', 'score_trend']
        }),
        ('Component Scores', {
            'fields': [
                'soil_health', 'water_efficiency', 'pest_disease_control',
                'yield_performance', 'cost_efficiency', 'sustainability'
            ]
        }),
        ('Period', {
            'fields': ['score_period', 'period_start', 'period_end']
        }),
        ('Recommendations', {
            'fields': ['recommendations']
        }),
        ('Timestamps', {
            'fields': ['created_at']
        }),
    )


@admin.register(AlertTrigger)
class AlertTriggerAdmin(admin.ModelAdmin):
    list_display = ['farm', 'title', 'importance', 'is_resolved', 'created_at']
    list_filter = ['alert_type', 'importance', 'is_resolved', 'created_at']
    search_fields = ['farm__name', 'title']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_resolved']
    
    fieldsets = (
        ('Farm Information', {
            'fields': ['user', 'farm']
        }),
        ('Alert Details', {
            'fields': ['alert_type', 'title', 'description', 'importance']
        }),
        ('Actions', {
            'fields': ['recommended_actions']
        }),
        ('Resolution', {
            'fields': ['is_resolved', 'resolved_at', 'resolution_notes']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at']
        }),
    )
    
    def mark_resolved(self, request, queryset):
        count = queryset.update(is_resolved=True, resolved_at=timezone.now())
        self.message_user(request, f'{count} alerts marked as resolved')
    
    mark_resolved.short_description = 'Mark selected alerts as resolved'


@admin.register(BenchmarkComparison)
class BenchmarkComparisonAdmin(admin.ModelAdmin):
    list_display = ['farm', 'crop', 'yield_performance_vs_benchmark', 'region']
    list_filter = ['region', 'comparison_date']
    search_fields = ['farm__name', 'crop__name']
    readonly_fields = ['comparison_date']


@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ['farm', 'report_type', 'title', 'period_end', 'last_viewed']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['farm__name', 'title']
    readonly_fields = ['generated_at']


@admin.register(NotificationQueue)
class NotificationQueueAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'severity', 'is_sent', 'is_read', 'created_at']
    list_filter = ['notification_type', 'severity', 'is_sent', 'is_read']
    search_fields = ['user__username', 'title']
    readonly_fields = ['created_at', 'sent_at', 'read_at']
    actions = ['mark_as_sent']
    
    def mark_as_sent(self, request, queryset):
        count = queryset.update(is_sent=True, sent_at=timezone.now())
        self.message_user(request, f'{count} notifications marked as sent')
    
    mark_as_sent.short_description = 'Mark selected notifications as sent'
