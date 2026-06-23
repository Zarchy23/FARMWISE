# core/payments/urls.py
# Payment URLs

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WalletViewSet, PaymentMethodViewSet, ProcessPaymentView,
    SubscriptionViewSet, LoanViewSet
)

router = DefaultRouter()
router.register(r'wallet', WalletViewSet, basename='wallet')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'loans', LoanViewSet, basename='loan')

urlpatterns = [
    path('', include(router.urls)),
    path('process-payment/', ProcessPaymentView.as_view(), name='process-payment'),
]
