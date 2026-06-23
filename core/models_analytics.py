# core/models_analytics.py
# FARMWISE Analytics & Real-Time Data Models
# Tracks farm performance, yield predictions, and real-time metrics

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
import statistics

User = get_user_model()


# ============================================================
# REAL-TIME DASHBOARD METRICS
# ============================================================

class DashboardMetric(models.Model):
    """Real-time metric data for dashboard displays"""
    
    METRIC_TYPES = [
        ('soil_moisture', 'Soil Moisture %'),
        ('temperature', 'Temperature °C'),
        ('rainfall', 'Rainfall mm'),
        ('humidity', 'Humidity %'),
        ('ph_level', 'pH Level'),
        ('nitrogen', 'Nitrogen ppm'),
        ('crop_health', 'Crop Health %'),
        ('yield_estimate', 'Yield Estimate kg/ha'),
        ('water_usage', 'Water Usage liters'),
        ('pest_count', 'Pest Count'),
        ('disease_index', 'Disease Index %'),
        ('soil_temperature', 'Soil Temperature °C'),
    ]
    
    SEVERITY_LEVELS = [
        ('normal', 'Normal - All Good'),
        ('warning', 'Warning - Watch closely'),
        ('critical', 'Critical - Action needed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='dashboard_metrics')
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='dashboard_metrics')
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True, related_name='dashboard_metrics')
    
    metric_type = models.CharField(max_length=30, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_LEVELS, default='normal')
    
    # Thresholds for alerts
    threshold_warning = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    threshold_critical = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_dashboard_metrics'
        verbose_name_plural = 'Dashboard Metrics'
        indexes = [
            models.Index(fields=['user', 'farm', 'metric_type', '-timestamp']),
        ]
        unique_together = [['user', 'farm', 'field', 'metric_type']]
    
    def __str__(self):
        return f"{self.farm.name} - {self.metric_type}: {self.value}"
    
    def is_alert(self):
        """Check if metric requires alert"""
        if self.severity in ['warning', 'critical']:
            return True
        return False


class MetricHistory(models.Model):
    """Historical data for metric trends and analysis"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metric_history')
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='metric_history')
    field = models.ForeignKey('Field', on_delete=models.SET_NULL, null=True, blank=True)
    
    metric_type = models.CharField(max_length=30, choices=DashboardMetric.METRIC_TYPES)
    
    # Aggregated values
    value_avg = models.DecimalField(max_digits=10, decimal_places=2)
    value_min = models.DecimalField(max_digits=10, decimal_places=2)
    value_max = models.DecimalField(max_digits=10, decimal_places=2)
    value_latest = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Time period (hourly, daily, weekly, monthly)
    period = models.CharField(max_length=10, choices=[
        ('hourly', 'Hourly'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ])
    
    timestamp = models.DateTimeField()  # When this period ended
    data_points = models.IntegerField(default=0)  # Number of readings in period
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_metric_history'
        verbose_name_plural = 'Metric History'
        indexes = [
            models.Index(fields=['user', 'farm', 'metric_type', 'period', '-timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.farm.name} - {self.metric_type} ({self.period}): {self.value_avg}"


# ============================================================
# YIELD & PRODUCTION ANALYTICS
# ============================================================

class YieldPrediction(models.Model):
    """ML-based yield predictions for crops"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='yield_predictions')
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='yield_predictions')
    field = models.ForeignKey('Field', on_delete=models.CASCADE, related_name='yield_predictions')
    crop = models.ForeignKey('CropSeason', on_delete=models.CASCADE, related_name='yield_predictions')
    
    # Prediction data
    predicted_yield_kg_ha = models.DecimalField(max_digits=10, decimal_places=2)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, validators=[])  # 0-100%
    
    # Actual yield (recorded after harvest)
    actual_yield_kg_ha = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    prediction_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # 0-100%
    
    # Factors
    factors = models.JSONField(default=dict, help_text='ML factors affecting prediction')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timeline
    created_at = models.DateTimeField(auto_now_add=True)
    harvest_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_yield_predictions'
        verbose_name_plural = 'Yield Predictions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.crop.name} @ {self.field.name}: {self.predicted_yield_kg_ha} kg/ha"
    
    def calculate_accuracy(self):
        """Calculate prediction accuracy after harvest"""
        if self.actual_yield_kg_ha:
            accuracy = 100 - abs((self.actual_yield_kg_ha - self.predicted_yield_kg_ha) / self.predicted_yield_kg_ha * 100)
            self.prediction_accuracy = max(0, min(100, accuracy))
            self.save()
            return self.prediction_accuracy
        return None


class ResourceUsageAnalytics(models.Model):
    """Track water, fertilizer, and chemical usage"""
    
    RESOURCE_TYPES = [
        ('water', 'Water (liters)'),
        ('fertilizer', 'Fertilizer (kg)'),
        ('pesticide', 'Pesticide (liters)'),
        ('herbicide', 'Herbicide (liters)'),
        ('fungicide', 'Fungicide (liters)'),
        ('labour', 'Labour (hours)'),
        ('fuel', 'Fuel (liters)'),
        ('seed', 'Seed (kg)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resource_usage')
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='resource_usage')
    field = models.ForeignKey('Field', on_delete=models.CASCADE, null=True, blank=True)
    crop = models.ForeignKey('CropSeason', on_delete=models.SET_NULL, null=True, blank=True)
    
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPES)
    quantity_used = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_available = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    
    date_used = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'analytics_resource_usage'
        verbose_name_plural = 'Resource Usage'
        indexes = [
            models.Index(fields=['user', 'farm', 'resource_type', '-date_used']),
        ]
    
    def __str__(self):
        return f"{self.get_resource_type_display()} @ {self.farm.name}: {self.quantity_used}"


# ============================================================
# FARM PERFORMANCE ANALYTICS
# ============================================================

class FarmPerformanceScore(models.Model):
    """Overall farm health and performance rating"""
    
    SCORING_PERIOD_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='performance_scores')
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='performance_scores')
    
    # Overall health score (0-100)
    health_score = models.IntegerField(validators=[])  # 0-100
    
    # Component scores
    soil_health = models.IntegerField()  # 0-100
    water_efficiency = models.IntegerField()  # 0-100
    pest_disease_control = models.IntegerField()  # 0-100
    yield_performance = models.IntegerField()  # 0-100
    cost_efficiency = models.IntegerField()  # 0-100
    sustainability = models.IntegerField()  # 0-100
    
    # Trend
    score_trend = models.CharField(max_length=20, choices=[
        ('improving', 'Improving'),
        ('stable', 'Stable'),
        ('declining', 'Declining'),
    ])
    
    score_period = models.CharField(max_length=10, choices=SCORING_PERIOD_CHOICES, default='daily')
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()
    
    recommendations = models.JSONField(default=list, help_text='AI-generated recommendations')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_farm_performance'
        verbose_name_plural = 'Farm Performance Scores'
        ordering = ['-period_end']
    
    def __str__(self):
        return f"{self.farm.name} - Score: {self.health_score}/100"
    
    def get_rating(self):
        """Get text rating based on score"""
        if self.health_score >= 85:
            return 'Excellent'
        elif self.health_score >= 70:
            return 'Good'
        elif self.health_score >= 50:
            return 'Average'
        else:
            return 'Needs Improvement'


class AlertTrigger(models.Model):
    """System alerts based on metrics and predictions"""
    
    ALERT_TYPES = [
        ('drought', 'Drought Alert'),
        ('pest_outbreak', 'Pest Outbreak'),
        ('disease', 'Disease Risk'),
        ('extreme_weather', 'Extreme Weather'),
        ('soil_degradation', 'Soil Degradation'),
        ('low_yield_forecast', 'Low Yield Forecast'),
        ('water_scarcity', 'Water Scarcity'),
        ('market_opportunity', 'Market Opportunity'),
        ('equipment_maintenance', 'Equipment Maintenance'),
        ('custom', 'Custom Alert'),
    ]
    
    IMPORTANCE_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='alerts')
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='alerts')
    
    alert_type = models.CharField(max_length=30, choices=ALERT_TYPES)
    importance = models.CharField(max_length=20, choices=IMPORTANCE_LEVELS, default='medium')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    # Recommended actions
    recommended_actions = models.JSONField(default=list)
    
    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_alert_triggers'
        verbose_name_plural = 'Alert Triggers'
        indexes = [
            models.Index(fields=['user', 'farm', 'is_resolved', '-created_at']),
        ]
        ordering = ['-importance', '-created_at']
    
    def __str__(self):
        return f"{self.farm.name} - {self.get_alert_type_display()}"


# ============================================================
# COMPARATIVE ANALYTICS
# ============================================================

class BenchmarkComparison(models.Model):
    """Compare farm performance against regional/national benchmarks"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='benchmarks')
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='benchmarks')
    crop = models.ForeignKey('CropSeason', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Benchmark data
    benchmark_yield_kg_ha = models.DecimalField(max_digits=10, decimal_places=2)
    farm_yield_kg_ha = models.DecimalField(max_digits=10, decimal_places=2)
    yield_performance_vs_benchmark = models.DecimalField(max_digits=5, decimal_places=2)  # % above/below
    
    benchmark_water_liters_per_ha = models.DecimalField(max_digits=12, decimal_places=2)
    farm_water_liters_per_ha = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    water_efficiency_vs_benchmark = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    benchmark_cost_per_ha = models.DecimalField(max_digits=10, decimal_places=2)
    farm_cost_per_ha = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cost_efficiency_vs_benchmark = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    age_group = models.CharField(max_length=50, blank=True, help_text='Farmer age group for comparison')
    region = models.CharField(max_length=100, blank=True, help_text='Region for comparison')
    
    comparison_date = models.DateField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_benchmark_comparison'
        verbose_name_plural = 'Benchmark Comparisons'
        ordering = ['-comparison_date']
    
    def __str__(self):
        return f"{self.farm.name} vs Regional Benchmark"


# ============================================================
# REPORT GENERATION
# ============================================================

class AnalyticsReport(models.Model):
    """Generated analytics reports for farmers"""
    
    REPORT_TYPES = [
        ('seasonal', 'Seasonal Report'),
        ('monthly', 'Monthly Report'),
        ('yield_analysis', 'Yield Analysis'),
        ('resource_efficiency', 'Resource Efficiency'),
        ('pest_disease', 'Pest & Disease Report'),
        ('financial', 'Financial Summary'),
        ('forecast', 'Seasonal Forecast'),
        ('comparison', 'Benchmark Comparison'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_reports')
    farm = models.ForeignKey('Farm', on_delete=models.CASCADE, related_name='analytics_reports')
    
    report_type = models.CharField(max_length=30, choices=REPORT_TYPES)
    title = models.CharField(max_length=255)
    
    # Report content
    summary = models.TextField()
    findings = models.JSONField(default=list)  # Key findings as list
    recommendations = models.JSONField(default=list)  # Recommendations
    visualizations = models.JSONField(default=dict)  # Chart data
    
    # Report data
    report_file = models.FileField(upload_to='reports/', null=True, blank=True)
    report_data = models.JSONField(default=dict)  # Full report data
    
    # Timeline
    period_start = models.DateField()
    period_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    last_viewed = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'analytics_reports'
        verbose_name_plural = 'Analytics Reports'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.farm.name} - {self.get_report_type_display()}"


# ============================================================
# REAL-TIME WebSocket Notification Tracking
# ============================================================

class NotificationQueue(models.Model):
    """Queue for real-time notifications via WebSocket"""
    
    NOTIFICATION_TYPES = [
        ('alert', 'Alert'),
        ('update', 'Update'),
        ('reminder', 'Reminder'),
        ('forecast', 'Forecast'),
        ('market', 'Market Info'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notification_queue')
    farm = models.ForeignKey('Farm', on_delete=models.SET_NULL, null=True, blank=True)
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    icon = models.CharField(max_length=30, blank=True)  # Icon class for frontend
    severity = models.CharField(max_length=20, choices=[
        ('info', 'Info'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ], default='info')
    
    # Status
    is_sent = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)
    
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analytics_notification_queue'
        verbose_name_plural = 'Notification Queue'
        indexes = [
            models.Index(fields=['user', 'is_sent', '-created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
