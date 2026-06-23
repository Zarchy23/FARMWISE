# core/payments/webhooks_urls.py
# Webhook URL routing for payment gateways

from django.urls import path
from . import webhooks

urlpatterns = [
    # Stripe webhook
    path('stripe/', webhooks.stripe_webhook, name='stripe-webhook'),
    
    # M-Pesa webhook
    path('mpesa/', webhooks.mpesa_webhook, name='mpesa-webhook'),
    
    # EcoCash webhook
    path('ecocash/', webhooks.ecocash_webhook, name='ecocash-webhook'),
    
    # Zipit webhook
    path('zipit/', webhooks.zipit_webhook, name='zipit-webhook'),
    
    # Payout webhook (for seller payouts)
    path('payout/', webhooks.payout_webhook, name='payout-webhook'),
]
