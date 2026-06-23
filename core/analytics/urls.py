# core/analytics/urls.py
# URL routing for analytics REST API endpoints

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DashboardMetricViewSet,
    MetricHistoryViewSet,
    YieldPredictionViewSet,
    FarmPerformanceScoreViewSet,
    AlertTriggerViewSet,
    AnalyticsReportViewSet,
    NotificationQueueViewSet,
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'metrics', DashboardMetricViewSet, basename='metric')
router.register(r'metrics-history', MetricHistoryViewSet, basename='metric-history')
router.register(r'yield-predictions', YieldPredictionViewSet, basename='yield-prediction')
router.register(r'performance-scores', FarmPerformanceScoreViewSet, basename='performance-score')
router.register(r'alerts', AlertTriggerViewSet, basename='alert')
router.register(r'reports', AnalyticsReportViewSet, basename='report')
router.register(r'notifications', NotificationQueueViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
