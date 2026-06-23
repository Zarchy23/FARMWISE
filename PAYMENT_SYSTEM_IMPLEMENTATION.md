# FARMWISE PAYMENT SYSTEM - IMPLEMENTATION GUIDE

## 📋 Overview

Complete payment system integration for FarmWise including:
- ✅ Global payments (Stripe - cards)
- ✅ East African (M-Pesa)
- ✅ Zimbabwe payments (EcoCash, OneMoney, Telecash, Zipit, RTGS)
- ✅ Internal wallet system
- ✅ Subscriptions & billing
- ✅ Farm loans & credit
- ✅ Escrow for marketplace
- ✅ Seller payouts

---

## 🚀 Quick Start (15 minutes)

### Step 1: Install Payment Package

```bash
# Copy payment module files to core/payments/
# Already created: models_payments.py, gateway.py, views.py, serializers.py, etc.

# Create database tables
python manage.py makemigrations
python manage.py migrate
```

### Step 2: Update Django Settings

```python
# settings.py

INSTALLED_APPS = [
    # ... existing apps
    'core.payments',  # Add this
]

# Payment Gateway Configuration
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY')
MPESA_SHORTCODE = os.getenv('MPESA_SHORTCODE')
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL')

ECOCASH_API_KEY = os.getenv('ECOCASH_API_KEY')
ECOCASH_API_SECRET = os.getenv('ECOCASH_API_SECRET')
ECOCASH_MERCHANT_CODE = os.getenv('ECOCASH_MERCHANT_CODE')
ECOCASH_BASE_URL = os.getenv('ECOCASH_BASE_URL', 'https://api.ecocash.co.zw/v1')
ECOCASH_CALLBACK_URL = os.getenv('ECOCASH_CALLBACK_URL')

ZIPIT_API_KEY = os.getenv('ZIPIT_API_KEY')
ZIPIT_API_SECRET = os.getenv('ZIPIT_API_SECRET')
ZIPIT_MERCHANT_ID = os.getenv('ZIPIT_MERCHANT_ID')

# Payment Settings
DEFAULT_CURRENCY = 'USD'
PAYMENT_TIMEOUT = 30
PLATFORM_FEE = Decimal('0.05')  # 5%
ESCROW_HOLD_DAYS = 7
```

### Step 3: Update URL Routing

```python
# urls.py

from django.urls import path, include
from core.payments import webhooks

urlpatterns = [
    # ... existing urls
    
    # Payment APIs
    path('api/payments/', include('core.payments.urls')),
    
    # Webhooks
    path('webhooks/stripe/', webhooks.stripe_webhook, name='stripe-webhook'),
    path('webhooks/mpesa/', webhooks.mpesa_webhook, name='mpesa-webhook'),
    path('webhooks/ecocash/', webhooks.ecocash_webhook, name='ecocash-webhook'),
    path('webhooks/zipit/', webhooks.zipit_webhook, name='zipit-webhook'),
]
```

### Step 4: Configure Environment Variables

```bash
cp .env.payments .env
# Edit .env with your actual API keys
```

### Step 5: Create Subscription Plans

```python
# Run via Django shell or management command
from core.payments.models_payments import SubscriptionPlan

plans = [
    {
        'plan_type': 'free',
        'name': 'Free Plan',
        'price_monthly': Decimal('0'),
        'price_yearly': Decimal('0'),
        'max_farms': 1,
        'max_fields': 5,
        'max_livestock': 50,
        'features': ['Basic dashboard', 'Limited weather']
    },
    {
        'plan_type': 'basic',
        'name': 'Basic Plan',
        'price_monthly': Decimal('9.99'),
        'price_yearly': Decimal('99.99'),
        'max_farms': 3,
        'max_fields': 20,
        'max_livestock': 200,
        'api_access': True,
        'features': ['Full dashboard', 'Weather API', 'Email support']
    },
    # ... more plans
]

for plan_data in plans:
    SubscriptionPlan.objects.create(**plan_data)
```

---

## 💳 API ENDPOINTS

### Wallet Endpoints

```
GET    /api/payments/wallet/          - Get wallet info
POST   /api/payments/wallet/deposit/  - Deposit funds
POST   /api/payments/wallet/withdraw/ - Withdraw funds
POST   /api/payments/wallet/transfer/ - Transfer to user
GET    /api/payments/wallet/balance/  - Check balance
GET    /api/payments/wallet/history/  - Transaction history
```

### Payment Processing

```
POST   /api/payments/process-payment/ - Process payment
```

### Subscriptions

```
GET    /api/payments/subscriptions/available_plans/
GET    /api/payments/subscriptions/current/
POST   /api/payments/subscriptions/upgrade/
POST   /api/payments/subscriptions/cancel/
```

### Loans

```
POST   /api/payments/loans/apply/
GET    /api/payments/loans/list_loans/
```

---

## 🧪 Testing Payment Integration

### Test Stripe Payments

```python
from core.payments.gateway import StripePayment

stripe_payment = StripePayment()

# Create test payment intent
result = stripe_payment.create_payment_intent(
    amount=Decimal('50.00'),
    currency='usd',
    metadata={'order_id': '12345', 'user': 'test@example.com'}
)

print(result)
# {
#     'success': True,
#     'client_secret': 'pi_xxx_secret_xxx',
#     'payment_intent_id': 'pi_xxx'
# }
```

### Test M-Pesa (Sandbox)

```python
from core.payments.gateway import MpesaPayment

mpesa = MpesaPayment()

# Initiate test STK push
result = mpesa.stk_push(
    phone_number='254712345678',
    amount=100,
    account_reference='ORDER-001',
    transaction_desc='FarmWise Order'
)

print(result)
# {
#     'success': True,
#     'transaction_id': 'xxx',
#     'message': 'Payment initiated'
# }

# Check status
status = mpesa.query_status(result['transaction_id'])
print(status)
# {'status': 'pending', ...}
```

### Test EcoCash (Zimbabwe)

```python
from core.payments.gateway import EcoCashPayment

ecocash = EcoCashPayment()

# Initiate payment
result = ecocash.initiate_payment(
    phone_number='263771234567',  # EcoCash number
    amount=Decimal('50.00'),
    reference='ORDER-001',
    description='FarmWise Order'
)

print(result)
# Check status
status = ecocash.check_transaction_status(result['transaction_id'])
```

---

## 🌐 Frontend Integration

### Include Payment Modal

```html
<!-- base.html -->
{% load static %}

<!DOCTYPE html>
<html>
<head>
    <!-- ... -->
    <script src="https://js.stripe.com/v3/"></script>
</head>
<body>
    <!-- Include payment modal -->
    {% include "payments/payment_modal.html" %}
    
    <!-- Your content -->
    
    <script>
        // Trigger payment modal
        function buyProduct(price, orderId) {
            openPaymentModal(price, orderId);
        }
    </script>
</body>
</html>
```

### Example: Marketplace Checkout

```html
<div class="checkout-container">
    <div class="order-summary">
        <h2>Order Summary</h2>
        <p>Total: USD <span id="total-price">0.00</span></p>
    </div>
    
    <button class="btn btn-primary" onclick="checkout()">
        Proceed to Payment
    </button>
</div>

<script>
function checkout() {
    const totalPrice = document.getElementById('total-price').textContent;
    const orderId = '{{ order.id }}';
    openPaymentModal(totalPrice, orderId);
}
</script>
```

---

## 📊 Admin Dashboard

Access payment admin at: `/admin/`

### Available Admin Views:
- FarmWallet - View user wallets and balances
- Transaction - Track all payments
- SubscriptionPlan - Manage subscription plans
- UserSubscription - View active subscriptions
- FarmLoan - Manage loan applications
- Invoice - Generate and track invoices
- EscrowPayment - Monitor marketplace escrow

---

## 🔒 Security Best Practices

### 1. PCI Compliance (Card Data)

**Never store card data directly.** Always use:

```python
# ✅ GOOD - Use Stripe tokens
payment_method = PaymentMethod.objects.create(
    user=request.user,
    stripe_payment_method_id=token,  # From Stripe
    card_last_four='4242',  # Only last 4 digits
)

# ❌ BAD - Never do this
# payment_method.card_number = '4242424242424242'  # NEVER!
```

### 2. Webhook Signature Verification

```python
# Always verify webhook signatures
@csrf_exempt
@require_POST
def stripe_webhook(request):
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = stripe.Webhook.construct_event(
        request.body, 
        sig_header, 
        settings.STRIPE_WEBHOOK_SECRET
    )
```

### 3. API Key Management

```python
# ✅ Use environment variables
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')

# ❌ Never commit keys
# STRIPE_SECRET_KEY = 'sk_live_xxx'  # NEVER!
```

### 4. Rate Limiting

```python
from rest_framework.throttling import UserRateThrottle

class PaymentRateThrottle(UserRateThrottle):
    scope = 'payments'
    THROTTLE_RATES = {'payments': '10/hour'}

# Apply to payment views
class ProcessPaymentView(APIView):
    throttle_classes = [PaymentRateThrottle]
```

### 5. Transaction Logging

```python
# All transactions are logged with audit trail
transaction = Transaction.objects.create(
    user=request.user,
    amount=amount,
    transaction_type='purchase',
    status='processing',
    metadata={
        'ip_address': get_client_ip(request),
        'user_agent': request.META.get('HTTP_USER_AGENT'),
        'timestamp': timezone.now().isoformat()
    }
)
```

---

## 🧩 Integration Checklist

- [ ] Copy payment module files
- [ ] Run migrations (`makemigrations`, `migrate`)
- [ ] Update settings.py with payment config
- [ ] Update urls.py with payment routes
- [ ] Configure environment variables (.env)
- [ ] Create subscription plans via Django shell
- [ ] Include payment modal template in base.html
- [ ] Set up webhook URLs in each provider
- [ ] Test with sandbox credentials first
- [ ] Implement error handling and logging
- [ ] Set up monitoring/alerts for failed payments
- [ ] Create cron job for scheduled payouts
- [ ] Document API endpoints for frontend team

---

## 🔄 Scheduled Tasks (Celery)

### Create payment tasks:

```python
# core/payments/tasks.py
from celery import shared_task
from django.utils import timezone

@shared_task
def process_weekly_payouts():
    """Automatically pay sellers weekly"""
    from .models_payments import SellerPayout
    
    payouts = SellerPayout.objects.filter(
        status='pending',
        created_at__lte=timezone.now() - timezone.timedelta(days=7)
    )
    
    for payout in payouts:
        # Process payout to seller's wallet/bank
        pass

@shared_task
def calculate_interest_on_savings():
    """Calculate monthly interest on savings accounts"""
    from .models_payments import FarmSavings
    
    accounts = FarmSavings.objects.all()
    for account in accounts:
        account.calculate_interest()

# Add to celery beat schedule:
# CELERY_BEAT_SCHEDULE = {
#     'process-weekly-payouts': {
#         'task': 'core.payments.tasks.process_weekly_payouts',
#         'schedule': crontab(day_of_week=1, hour=3, minute=0),  # Mondays 3 AM
#     },
# }
```

---

## 📈 Monitoring & Analytics

### Track Payment Metrics

```python
# core/payments/analytics.py
from django.db.models import Sum, Avg, Count
from .models_payments import Transaction

def get_payment_stats():
    return {
        'total_transactions': Transaction.objects.count(),
        'total_revenue': Transaction.objects.filter(
            status='completed'
        ).aggregate(Sum('amount')),
        'average_transaction': Transaction.objects.filter(
            status='completed'
        ).aggregate(Avg('amount')),
        'failed_transactions': Transaction.objects.filter(
            status='failed'
        ).count(),
    }
```

---

## ❓ FAQ

**Q: How do I test Stripe without going live?**
A: Use test keys in `.env`:
```
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

**Q: What happens if a payment fails?**
A: Transaction marked as failed, user notified via email, retry offered after 24hrs

**Q: How are seller payouts processed?**
A: Weekly automatic payouts to seller's wallet, bank, or mobile money

**Q: Can I refund a payment?**
A: Yes, via admin dashboard or API:
```python
gateway.stripe.refund_payment(payment_intent_id, amount)
```

**Q: How do I handle Zimbabwe currency (ZWL)?**
A: Create separate wallet accounts with ZWL currency selected

---

## 🆘 Troubleshooting

### Payment stuck in "Processing"

```python
# Check transaction status
transaction = Transaction.objects.get(id=xxx)
print(transaction.status)

# Manually mark completed if confirmed
transaction.mark_completed()
```

### Webhook not receiving callbacks

1. Check that webhook URL is publicly accessible
2. Verify webhook signature matches settings
3. Check payment provider logs for errors
4. Enable Django debug logging on webhooks

### Mobile money payment failed

- Verify phone number format (country-specific)
- Check if customer has sufficient balance
- Verify API credentials haven't expired
- Contact payment provider support

---

## 📞 Support

For issues or questions:
1. Check error logs in Django admin
2. Review transaction history for clues
3. Contact payment provider support
4. Create GitHub issue with full error trace

---

## 🎯 Next Steps

1. **Test thoroughly** with sandbox credentials
2. **Monitor live transactions** in production
3. **Implement analytics** dashboard
4. **Add fraud detection** using payment signals
5. **Expand to more payment methods** as needed
6. **Optimize for mobile** payment experience

---

Generated: April 2026
FarmWise Payment System v1.0
