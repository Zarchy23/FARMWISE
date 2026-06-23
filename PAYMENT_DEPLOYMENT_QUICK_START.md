# Quick Migration & Deployment Guide

## 🚀 Deploy Payment System in 3 Steps

### Step 1: Prepare Database (2 minutes)

```bash
# Navigate to project
cd c:\Users\Zarchy\farmwise

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate
```

### Step 2: Configure Environment (5 minutes)

```bash
# Copy template
cp .env.payments .env

# Get your credentials:
# 1. Stripe: dashboard.stripe.com/apikeys
# 2. M-Pesa: safaricom.co.ke/business
# 3. EcoCash: econet.co.zw/business
# 4. Other providers similarly

# Edit .env with YOUR actual keys
nano .env
```

**How to get API keys:**

**Stripe:**
- Go to https://dashboard.stripe.com/apikeys
- Copy "Publishable Key" (starts with pk_test_)
- Copy "Secret Key" (starts with sk_test_)
- Get webhook signing secret from webhooks section

**M-Pesa (Safaricom):**
- Business: https://safaricom.co.ke/business
- Register for Daraja platform: https://developer.safaricom.co.ke
- Get Consumer Key & Secret from your app

**EcoCash (Econet):**
- Business portal: https://business.econet.co.zw
- Contact: business@econet.co.zw
- Request API credentials & sandbox access

**Others:**
- OneMoney (NetOne): https://onemoney.co.zw
- Telecash (Telecel): https://telecash.co.zw
- Zipit: https://zipit.co.zw

### Step 3: Create Subscription Plans (3 minutes)

```bash
# Open Django shell
python manage.py shell

# Paste this code:
from core.payments.models_payments import SubscriptionPlan
from decimal import Decimal

plans = [
    {
        'plan_type': 'free',
        'name': 'Free Plan',
        'description': 'Perfect for getting started',
        'price_monthly': Decimal('0'),
        'price_yearly': Decimal('0'),
        'max_farms': 1,
        'max_fields': 5,
        'max_livestock': 50,
        'max_equipment': 5,
        'display_order': 1,
        'features': ['Dashboard', 'Weather updates', 'Basic support']
    },
    {
        'plan_type': 'basic',
        'name': 'Basic Plan',
        'description': 'For small farms',
        'price_monthly': Decimal('9.99'),
        'price_yearly': Decimal('99.99'),
        'max_farms': 3,
        'max_fields': 20,
        'max_livestock': 200,
        'max_equipment': 10,
        'api_access': True,
        'display_order': 2,
        'features': ['Full dashboard', 'API access', 'Email support']
    },
    {
        'plan_type': 'pro',
        'name': 'Professional Plan',
        'description': 'For growing operations',
        'price_monthly': Decimal('29.99'),
        'price_yearly': Decimal('299.99'),
        'max_farms': 10,
        'max_fields': 100,
        'max_livestock': 1000,
        'max_equipment': 50,
        'api_access': True,
        'priority_support': True,
        'advanced_analytics': True,
        'display_order': 3,
        'features': ['Advanced analytics', 'Priority support', 'API access']
    },
    {
        'plan_type': 'enterprise',
        'name': 'Enterprise Plan',
        'description': 'For large operations',
        'price_monthly': Decimal('99.99'),
        'price_yearly': Decimal('999.99'),
        'max_farms': 999,
        'max_fields': 9999,
        'max_livestock': 99999,
        'max_equipment': 999,
        'api_access': True,
        'priority_support': True,
        'advanced_analytics': True,
        'integration_enabled': True,
        'custom_branding': True,
        'dedicated_account_manager': True,
        'display_order': 4,
        'features': ['Everything', 'Dedicated support', 'Custom integration']
    }
]

for plan_data in plans:
    SubscriptionPlan.objects.create(**plan_data)
    print(f"✅ Created {plan_data['name']}")

print("✅ All plans created!")

# Exit shell
exit()
```

---

## 🧪 Test Payment Processing

### Test Stripe (Recommended First)

```bash
# In Django shell:
python manage.py shell

from core.payments.gateway import StripePayment
from decimal import Decimal

stripe_payment = StripePayment()

# Create test payment
result = stripe_payment.create_payment_intent(
    amount=Decimal('10.00'),
    currency='usd',
    metadata={'test': 'true'}
)

if result['success']:
    print(f"✅ Payment intent created: {result['payment_intent_id']}")
    print(f"Client secret: {result['client_secret']}")
else:
    print(f"❌ Error: {result['error']}")

exit()
```

### Test M-Pesa (Kenya)

```bash
python manage.py shell

from core.payments.gateway import MpesaPayment

mpesa = MpesaPayment()

# Test STK push - use TEST phone number
result = mpesa.stk_push(
    phone_number='254712345678',  # Test Safaricom number
    amount=100,
    account_reference='TEST-001',
    transaction_desc='FarmWise Test'
)

print(result)
exit()
```

### Test EcoCash (Zimbabwe)

```bash
python manage.py shell

from core.payments.gateway import EcoCashPayment
from decimal import Decimal

ecocash = EcoCashPayment()

result = ecocash.initiate_payment(
    phone_number='263771234567',  # Test EcoCash number
    amount=Decimal('10.00'),
    reference='TEST-002',
    description='FarmWise Test'
)

print(result)
exit()
```

---

## 🔗 Set Up Webhooks

After deploying to production, add webhook endpoints:

### Stripe Webhooks
1. Go to https://dashboard.stripe.com/webhooks
2. Click "Add endpoint"
3. Endpoint URL: `https://yourdomain.com/webhooks/stripe/`
4. Events to send:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`
   - `charge.refunded`
   - `invoice.payment_succeeded`

### M-Pesa Webhooks
1. In Safaricom Daraja portal
2. Set callback URL: `https://yourdomain.com/webhooks/mpesa/`

### EcoCash Webhooks
1. In EcoCash business portal
2. Set callback URL: `https://yourdomain.com/webhooks/ecocash/`

### Zipit Webhooks
1. In Zipit dashboard
2. Set callback URL: `https://yourdomain.com/webhooks/zipit/`

---

## ✅ Verification Checklist

Run these checks before going live:

```bash
# 1. Check migrations ran successfully
python manage.py migrate --plan  # Should show no pending migrations

# 2. Verify models created
python manage.py shell
from core.payments.models_payments import FarmWallet, Transaction
print("✅ Models imported successfully")
exit()

# 3. Check payment gateway configuration
python manage.py shell
from django.conf import settings
print(f"Stripe Key: {settings.STRIPE_PUBLISHABLE_KEY[:10]}...")
print(f"M-Pesa Key: {settings.MPESA_CONSUMER_KEY[:10]}...")
exit()

# 4. Test database connections
python manage.py check

# 5. Collect static files (if needed)
python manage.py collectstatic --noinput
```

---

## 🎯 First Payment Flow Test

### 1. Create a Test User

```bash
python manage.py shell

from django.contrib.auth import get_user_model

User = get_user_model()
test_user = User.objects.create_user(
    username='testfarm',
    email='test@farmwise.local',
    password='testpass123',
    user_type='farmer',
    phone_number='+254712345678'
)

print(f"✅ Created test user: {test_user.username}")

# Check wallet created automatically
wallet = test_user.wallet
print(f"Wallet balance: {wallet.balance}")

exit()
```

### 2. Test Wallet Operations

```bash
python manage.py shell

from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()
user = User.objects.get(username='testfarm')
wallet = user.wallet

# Test deposit
wallet.deposit(Decimal('50.00'), 'TEST-DEPOSIT-001')
print(f"After deposit: ${wallet.balance}")

# Test withdrawal
wallet.withdraw(Decimal('10.00'), 'TEST-WITHDRAW-001')
print(f"After withdrawal: ${wallet.balance}")

# View transactions
for t in wallet.transactions.all():
    print(f"{t.transaction_type}: {t.amount} - {t.status}")

exit()
```

### 3. Test Payment Processing

```bash
python manage.py shell

from django.contrib.auth import get_user_model
from core.payments.gateway import PaymentGateway
from decimal import Decimal

User = get_user_model()
user = User.objects.get(username='testfarm')

gateway = PaymentGateway()

# Test card payment
result = gateway.process_payment(
    amount=Decimal('25.00'),
    currency='USD',
    payment_method='card',
    customer_details={
        'user_id': user.id,
        'reference': 'TEST-ORDER-001'
    }
)

print(result)
exit()
```

---

## 🚀 Go Live Steps

1. **Update settings.py** with payment configuration
2. **Run migrations** on production database
3. **Create subscription plans** in production
4. **Set webhook URLs** in all payment providers
5. **Test with real sandbox credentials first**
6. **Enable SSL/HTTPS** on your domain
7. **Set up monitoring** for failed payments
8. **Configure logging** for payment debugging
9. **Train support team** on payment issues
10. **Launch to users!**

---

## 🐛 Troubleshooting

### Migrations Won't Run

```bash
# Check migration status
python manage.py showmigrations

# Reset migrations (dev only!)
python manage.py migrate zero  # WARNING: Deletes data
python manage.py migrate

# Check for errors
python manage.py check
```

### Payment Endpoints Not Working

```bash
# Verify URLs configured
python manage.py show_urls | grep payment

# Check API available
curl http://localhost:8000/api/payments/wallet/balance/

# Check permissions
# Must add @permission_classes([IsAuthenticated])
```

### Webhook Not Receiving Callbacks

1. Verify webhook URL is public (not localhost)
2. Check webhook signature matches (each provider different)
3. Enable Django logging to see requests
4. Check payment provider logs

```python
# Enable logging in settings.py:
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'core.payments': {'handlers': ['console'], 'level': 'DEBUG'},
    }
}
```

---

## 📈 Monitor After Launch

### Daily Checks

```bash
# Check failed transactions
python manage.py shell

from core.payments.models_payments import Transaction

failed = Transaction.objects.filter(status='failed')
print(f"Failed transactions: {failed.count()}")

for t in failed[:5]:
    print(f"{t.transaction_id}: {t.failure_reason}")

exit()
```

### Set Up Alerts

```python
# core/payments/tasks.py
from celery import shared_task
from core.payments.models_payments import Transaction
from django.core.mail import send_mail

@shared_task
def check_failed_payments():
    """Alert admin of failed payments"""
    failed = Transaction.objects.filter(status='failed')
    
    if failed.count() > 10:  # Alert if more than 10 failed
        send_mail(
            'Alert: Multiple Failed Payments',
            f'There are {failed.count()} failed transactions',
            'alerts@farmwise.com',
            ['admin@farmwise.com']
        )
```

---

## 🎉 You're Done!

Your payment system is now:
- ✅ Configured
- ✅ Tested
- ✅ Ready to process payments
- ✅ Scalable for millions of transactions

**Start accepting payments from your users now!**

For questions, see: `PAYMENT_SYSTEM_IMPLEMENTATION.md`

---

Generated: April 16, 2026
FarmWise Payment System - Deployment Ready
