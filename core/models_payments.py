# core/models_payments.py
# FARMWISE - Complete Payment System
# Global + Zimbabwe Payment Integration

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
import uuid

User = get_user_model()

# ============================================================
# SECTION 1: WALLET & BALANCE
# ============================================================

class FarmWallet(models.Model):
    """Internal wallet system for FarmWise users"""
    
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('ZWL', 'Zimbabwe Dollar'),
        ('KES', 'Kenyan Shilling'),
        ('UGX', 'Uganda Shilling'),
        ('TZS', 'Tanzanian Shilling'),
        ('GHS', 'Ghanaian Cedis'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    total_deposited = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_withdrawn = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    is_frozen = models.BooleanField(default=False, help_text='Prevent transactions if frozen')
    frozen_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farm_wallets'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['balance']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.balance} {self.currency}"
    
    def deposit(self, amount, reference, source='manual'):
        """Add funds to wallet"""
        if self.is_frozen:
            raise Exception(f"Wallet frozen: {self.frozen_reason}")
        
        amount = Decimal(str(amount))
        self.balance += amount
        self.total_deposited += amount
        self.save(update_fields=['balance', 'total_deposited', 'updated_at'])
        
        WalletTransaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type='deposit',
            reference=reference,
            source=source,
            status='completed'
        )
        return True
    
    def withdraw(self, amount, reference, destination='manual'):
        """Withdraw funds from wallet"""
        if self.is_frozen:
            raise Exception(f"Wallet frozen: {self.frozen_reason}")
        
        amount = Decimal(str(amount))
        if self.balance >= amount:
            self.balance -= amount
            self.total_withdrawn += amount
            self.save(update_fields=['balance', 'total_withdrawn', 'updated_at'])
            
            WalletTransaction.objects.create(
                wallet=self,
                amount=amount,
                transaction_type='withdrawal',
                reference=reference,
                destination=destination,
                status='completed'
            )
            return True
        return False
    
    def transfer(self, recipient_wallet, amount, reference):
        """Transfer funds to another wallet"""
        amount = Decimal(str(amount))
        if self.balance >= amount:
            self.balance -= amount
            self.save(update_fields=['balance', 'updated_at'])
            
            recipient_wallet.balance += amount
            recipient_wallet.save(update_fields=['balance', 'updated_at'])
            
            # Record transfer out
            WalletTransaction.objects.create(
                wallet=self,
                amount=amount,
                transaction_type='transfer_out',
                reference=reference,
                status='completed',
                related_wallet=recipient_wallet
            )
            
            # Record transfer in
            WalletTransaction.objects.create(
                wallet=recipient_wallet,
                amount=amount,
                transaction_type='transfer_in',
                reference=reference,
                status='completed',
                related_wallet=self
            )
            return True
        return False
    
    def get_available_balance(self):
        """Get available balance (accounting for pending transactions)"""
        pending = WalletTransaction.objects.filter(
            wallet=self,
            status='pending',
            transaction_type__in=['withdrawal', 'transfer_out']
        ).aggregate(total=models.Sum('amount'))['total'] or 0
        
        return self.balance - pending


class WalletTransaction(models.Model):
    """Wallet transaction history and audit trail"""
    
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('interest', 'Interest'),
        ('fee', 'Fee'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    wallet = models.ForeignKey(FarmWallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    reference = models.CharField(max_length=255, db_index=True)
    source = models.CharField(max_length=50, blank=True)  # 'payment', 'reward', 'manual', etc.
    destination = models.CharField(max_length=50, blank=True)  # where withdrawal went
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    related_wallet = models.ForeignKey(FarmWallet, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transfers')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'wallet_transactions'
        indexes = [
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.wallet.user} - {self.transaction_type} - {self.amount}"


# ============================================================
# SECTION 2: PAYMENT PROCESSING
# ============================================================

class PaymentMethod(models.Model):
    """Saved payment methods for users"""
    
    PAYMENT_METHODS = [
        ('card', 'Credit/Debit Card'),
        ('bank', 'Bank Account'),
        ('mobile_money', 'Mobile Money'),
        ('wallet', 'FarmWise Wallet'),
    ]
    
    CARD_PROVIDERS = [
        ('visa', 'Visa'),
        ('mastercard', 'Mastercard'),
        ('amex', 'American Express'),
        ('discover', 'Discover'),
    ]
    
    MOBILE_PROVIDERS = [
        ('mpesa', 'M-Pesa'),
        ('onemoney', 'OneMoney'),
        ('telecash', 'Telecash'),
        ('ecocash', 'EcoCash'),
        ('airtel', 'Airtel Money'),
        ('mtn', 'MTN Mobile Money'),
    ]
    
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='payment_methods')
    method_type = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    
    # Card details (encrypted in production)
    card_provider = models.CharField(max_length=20, choices=CARD_PROVIDERS, blank=True)
    card_last_four = models.CharField(max_length=4, blank=True)
    card_expiry_month = models.IntegerField(null=True, blank=True)
    card_expiry_year = models.IntegerField(null=True, blank=True)
    card_holder_name = models.CharField(max_length=255, blank=True)
    stripe_payment_method_id = models.CharField(max_length=255, blank=True)
    
    # Mobile money
    mobile_provider = models.CharField(max_length=20, choices=MOBILE_PROVIDERS, blank=True)
    mobile_number = models.CharField(max_length=20, blank=True)
    
    # Bank account
    bank_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    account_holder_name = models.CharField(max_length=255, blank=True)
    bank_code = models.CharField(max_length=10, blank=True)
    swift_code = models.CharField(max_length=12, blank=True)
    
    is_default = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        indexes = [
            models.Index(fields=['user', 'is_default']),
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        if self.method_type == 'card':
            return f"{self.card_provider} **** {self.card_last_four}"
        elif self.method_type == 'mobile_money':
            return f"{self.mobile_provider} {self.mobile_number}"
        elif self.method_type == 'bank':
            return f"{self.bank_name} {self.account_number[-4:]}"
        return self.method_type


class PaymentTransaction(models.Model):
    """Payment transactions (orders, payments, transfers)"""
    
    TRANSACTION_TYPES = [
        ('purchase', 'Product Purchase'),
        ('subscription', 'Subscription Payment'),
        ('loan_payment', 'Loan Payment'),
        ('transfer', 'User Transfer'),
        ('refund', 'Refund'),
        ('fee', 'Platform Fee'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUSES = [
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
    ]
    
    transaction_id = models.CharField(max_length=100, unique=True, db_index=True)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='transactions')
    recipient = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transactions')
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUSES, default='unpaid')
    
    # Payment method used
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    external_reference = models.CharField(max_length=255, blank=True, help_text='Stripe, M-Pesa, etc ref')
    
    # Gateway integrations
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    mpesa_request_id = models.CharField(max_length=255, blank=True)
    ecocash_transaction_id = models.CharField(max_length=255, blank=True)
    
    # Order details
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    # Fees and calculations
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    platform_fee = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    gateway_fee = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_fee = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Related entities
    farm = models.ForeignKey('Farm', on_delete=models.SET_NULL, null=True, blank=True, related_name='payment_transactions')
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    failed_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'payment_transactions'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['external_reference']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user} - {self.amount} {self.currency}"
    
    def mark_completed(self):
        """Mark transaction as completed"""
        self.status = 'completed'
        self.payment_status = 'paid'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, reason=''):
        """Mark transaction as failed"""
        self.status = 'failed'
        self.failed_at = timezone.now()
        self.failure_reason = reason
        self.save()


# ============================================================
# SECTION 3: SUBSCRIPTIONS & BILLING
# ============================================================

class SubscriptionPlan(models.Model):
    """FarmWise subscription plans"""
    
    PLAN_TYPES = [
        ('free', 'Free Plan'),
        ('basic', 'Basic Plan'),
        ('pro', 'Professional Plan'),
        ('enterprise', 'Enterprise Plan'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly (3 months)'),
        ('yearly', 'Yearly'),
    ]
    
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Features
    features = models.JSONField(default=list, blank=True, help_text='List of included features')
    max_farms = models.IntegerField(default=1)
    max_fields = models.IntegerField(default=5)
    max_livestock = models.IntegerField(default=50)
    max_equipment = models.IntegerField(default=10)
    max_users = models.IntegerField(default=1)
    
    # Feature toggles
    api_access = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    advanced_analytics = models.BooleanField(default=False)
    integration_enabled = models.BooleanField(default=False)
    custom_branding = models.BooleanField(default=False)
    dedicated_account_manager = models.BooleanField(default=False)
    
    stripe_product_id = models.CharField(max_length=255, blank=True)
    stripe_price_id_monthly = models.CharField(max_length=255, blank=True)
    stripe_price_id_yearly = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'subscription_plans'
        ordering = ['display_order']
    
    def __str__(self):
        return f"{self.name} - ${self.price_monthly}/month"


class UserSubscription(models.Model):
    """User subscription management"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending_activation', 'Pending Activation'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    
    # Billing details
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='monthly')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Dates
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    renewal_date = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Stripe integration
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True)
    
    # Preferences
    auto_renew = models.BooleanField(default=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Tracking
    billing_count = models.IntegerField(default=0)
    total_paid = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['renewal_date']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.plan.name}"
    
    def is_trial(self):
        """Check if user is in trial period"""
        return self.plan.plan_type == 'free' and (timezone.now() - self.start_date).days < 30
    
    def needs_renewal(self):
        """Check if subscription needs renewal"""
        return timezone.now() >= self.renewal_date
    
    def cancel_at_end_of_period(self):
        """Schedule cancellation at end of billing period"""
        self.auto_renew = False
        self.save()
        
        if self.stripe_subscription_id:
            import stripe
            stripe.Subscription.modify(
                self.stripe_subscription_id,
                cancel_at_period_end=True
            )
    
    def upgrade_plan(self, new_plan):
        """Upgrade to different plan"""
        old_plan = self.plan
        self.plan = new_plan
        self.save()
        
        # Calculate pro-rata credit
        # This would be more complex in production


class PlanChange(models.Model):
    """Track all plan changes and upgrades"""
    
    CHANGE_TYPES = [
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade'),
        ('trial_start', 'Trial Started'),
        ('trial_end', 'Trial Ended'),
    ]
    
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='plan_changes')
    old_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True, related_name='plan_changes_from')
    new_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='plan_changes_to')
    change_type = models.CharField(max_length=20, choices=CHANGE_TYPES)
    reason = models.TextField(blank=True)
    credit_applied = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'plan_changes'
    
    def __str__(self):
        return f"{self.user} - {self.change_type} to {self.new_plan.name}"


# ============================================================
# SECTION 4: INVOICES & BILLING
# ============================================================

class Invoice(models.Model):
    """Invoice generation and tracking"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('paid', 'Paid'),
        ('partially_paid', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(max_length=50, unique=True, db_index=True)
    user = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='invoices')
    transaction = models.OneToOneField(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoice')
    
    invoice_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Amounts
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2)
    paid_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Details
    description = models.TextField(blank=True)
    items = models.JSONField(default=list, blank=True)  # Line items
    notes = models.TextField(blank=True)
    
    # Tracking
    pdf_file = models.FileField(upload_to='invoices/', null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        indexes = [
            models.Index(fields=['user', 'invoice_date']),
            models.Index(fields=['status', 'due_date']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            from datetime import datetime
            self.invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)


# ============================================================
# SECTION 5: ESCROW & MARKETPLACE
# ============================================================

class EscrowPayment(models.Model):
    """Secure escrow for marketplace transactions"""
    
    STATUS_CHOICES = [
        ('held', 'Funds Held'),
        ('released', 'Funds Released'),
        ('refunded', 'Refunded'),
        ('disputed', 'Disputed'),
    ]
    
    order = models.OneToOneField('core.Order', on_delete=models.CASCADE, related_name='escrow')
    buyer = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='escrow_buyer')
    seller = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='escrow_seller')
    
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='held')
    
    # External references
    payment_intent_id = models.CharField(max_length=255, blank=True)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timing
    hold_date = models.DateTimeField(auto_now_add=True)
    release_date = models.DateTimeField(null=True, blank=True)
    refund_date = models.DateTimeField(null=True, blank=True)
    dispute_end_date = models.DateTimeField(null=True, blank=True)
    
    # Dispute info
    dispute_reason = models.TextField(blank=True)
    dispute_resolved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_disputes')
    
    class Meta:
        db_table = 'escrow_payments'
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['buyer', 'seller']),
        ]
    
    def __str__(self):
        return f"Escrow {self.id} - {self.seller.username} - {self.amount}"
    
    def release_payment(self):
        """Release funds to seller after delivery confirmation"""
        self.status = 'released'
        self.release_date = timezone.now()
        self.save()
        
        # Transfer to seller's wallet
        seller_wallet = self.seller.wallet
        seller_wallet.deposit(self.amount, f'escrow_{self.id}', source='escrow_release')
        
        return True
    
    def refund_payment(self):
        """Refund payment to buyer"""
        self.status = 'refunded'
        self.refund_date = timezone.now()
        self.save()
        
        # Refund to buyer's wallet
        buyer_wallet = self.buyer.wallet
        buyer_wallet.deposit(self.amount, f'escrow_refund_{self.id}', source='escrow_refund')
        
        return True


class SellerPayout(models.Model):
    """Track seller payouts"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    PAYOUT_METHODS = [
        ('wallet', 'To Wallet'),
        ('bank', 'To Bank Account'),
        ('mobile_money', 'To Mobile Money'),
    ]
    
    seller = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='payouts')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    payout_method = models.CharField(max_length=20, choices=PAYOUT_METHODS)
    destination = models.CharField(max_length=255, blank=True)  # Bank account, phone, etc.
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Tracking
    stripe_payout_id = models.CharField(max_length=255, blank=True)
    external_reference = models.CharField(max_length=255, blank=True)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'seller_payouts'
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"Payout to {self.seller.username} - {self.amount} {self.currency}"


# ============================================================
# SECTION 6: LOANS & CREDIT
# ============================================================

class FarmLoan(models.Model):
    """Farm loans and credit system"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active Loan'),
        ('completed', 'Completed'),
        ('defaulted', 'Defaulted'),
    ]
    
    farmer = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='loans')
    farm = models.ForeignKey('Farm', on_delete=models.SET_NULL, null=True, blank=True, related_name='loans')
    
    amount_requested = models.DecimalField(max_digits=14, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=12.0)
    term_months = models.IntegerField()
    monthly_payment = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    purpose = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Approval
    approved_by = models.ForeignKey('core.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_loans')
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Disbursement
    disbursed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    defaulted_at = models.DateTimeField(null=True, blank=True)
    
    # Collateral
    collateral_description = models.TextField(blank=True)
    collateral_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farm_loans'
        indexes = [
            models.Index(fields=['farmer', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Loan {self.id} - {self.farmer} - {self.amount_requested}"
    
    def calculate_monthly_payment(self):
        """Calculate monthly payment using amortization formula"""
        if self.amount_approved and self.interest_rate and self.term_months:
            monthly_rate = self.interest_rate / 100 / 12
            if monthly_rate == 0:
                self.monthly_payment = self.amount_approved / self.term_months
            else:
                numerator = self.amount_approved * monthly_rate * ((1 + monthly_rate) ** self.term_months)
                denominator = ((1 + monthly_rate) ** self.term_months) - 1
                self.monthly_payment = numerator / denominator
            self.save()
    
    def make_payment(self, amount):
        """Record loan payment"""
        LoanPayment.objects.create(
            loan=self,
            amount=amount,
            payment_date=timezone.now()
        )
        
        # Check if loan is completed
        total_paid = self.payments.aggregate(total=models.Sum('amount'))['total'] or 0
        if total_paid >= self.amount_approved:
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()


class LoanPayment(models.Model):
    """Individual loan payment records"""
    
    loan = models.ForeignKey(FarmLoan, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=50)  # 'wallet', 'card', 'bank', etc.
    reference = models.CharField(max_length=255, blank=True)
    transaction = models.ForeignKey(PaymentTransaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'loan_payments'
        indexes = [
            models.Index(fields=['loan', 'payment_date']),
        ]
    
    def __str__(self):
        return f"Payment {self.id} - Loan {self.loan.id} - {self.amount}"


class CreditScore(models.Model):
    """User credit scoring for lending decisions"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='credit_score')
    score = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(1000)])
    
    # Scoring factors
    farm_history_points = models.IntegerField(default=0)
    revenue_history_points = models.IntegerField(default=0)
    marketplace_activity_points = models.IntegerField(default=0)
    payment_history_points = models.IntegerField(default=0)
    
    # Details
    last_calculated = models.DateTimeField(auto_now=True)
    eligible_loan_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    eligible_for_credit = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'credit_scores'
    
    def __str__(self):
        return f"{self.user.username} - Score: {self.score}"
    
    def calculate_score(self):
        """Recalculate credit score based on user activity"""
        from core.models import Farm, Order
        
        score = 0
        
        # Farm history (max 200 points)
        farm_count = Farm.objects.filter(owner=self.user).count()
        farm_points = min(farm_count * 20, 200)
        score += farm_points
        
        # Revenue history (max 300 points)
        # total_revenue = Transaction.objects.filter(
        #     ???,
        #     transaction_type='income'
        # ).aggregate(total=models.Sum('amount'))['total'] or 0
        # revenue_points = min(int(total_revenue / 1000), 300)
        # score += revenue_points
        
        # Marketplace activity (max 200 points)
        # order_count = Order.objects.filter(buyer=self.user, status='completed').count()
        # marketplace_points = min(order_count * 10, 200)
        # score += marketplace_points
        
        # Payment history (max 300 points)
        on_time_payments = self.user.loans.filter(status='completed').count()
        payment_points = min(on_time_payments * 30, 300)
        score += payment_points
        
        self.score = min(score, 1000)
        self.eligible_for_credit = self.score >= 500
        self.eligible_loan_amount = Decimal(self.score * 10)  # Simple calculation
        self.save()
        
        return self.score


# ============================================================
# SECTION 7: SAVINGS & INVESTMENTS
# ============================================================

class FarmSavings(models.Model):
    """Savings accounts for farmers with interest"""
    
    farmer = models.OneToOneField(User, on_delete=models.CASCADE, related_name='savings')
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=2.0)  # Annual
    goal_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    goal_name = models.CharField(max_length=255, blank=True)
    
    total_interest_earned = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    last_interest_calculation = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'farm_savings'
    
    def __str__(self):
        return f"Savings {self.farmer.username} - ${self.balance}"
    
    def deposit(self, amount):
        """Deposit to savings"""
        amount = Decimal(str(amount))
        self.balance += amount
        self.save()
        
        SavingsTransaction.objects.create(
            savings=self,
            amount=amount,
            transaction_type='deposit'
        )
    
    def withdraw(self, amount):
        """Withdraw from savings"""
        amount = Decimal(str(amount))
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            
            SavingsTransaction.objects.create(
                savings=self,
                amount=amount,
                transaction_type='withdrawal'
            )
            return True
        return False
    
    def calculate_interest(self):
        """Calculate and apply monthly interest"""
        monthly_interest = self.balance * (self.interest_rate / 100 / 12)
        self.balance += monthly_interest
        self.total_interest_earned += monthly_interest
        self.last_interest_calculation = timezone.now()
        self.save()
        
        SavingsTransaction.objects.create(
            savings=self,
            amount=monthly_interest,
            transaction_type='interest'
        )


class SavingsTransaction(models.Model):
    """Savings transaction history"""
    
    TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('interest', 'Interest'),
    ]
    
    savings = models.ForeignKey(FarmSavings, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'savings_transactions'
    
    def __str__(self):
        return f"{self.savings.farmer} - {self.transaction_type} - {self.amount}"


class FarmInvestmentProject(models.Model):
    """Crowdfunding projects for farm expansion"""
    
    STATUS_CHOICES = [
        ('active', 'Accepting Investments'),
        ('funded', 'Fully Funded'),
        ('completed', 'Project Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    farmer = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='investment_projects')
    farm = models.ForeignKey('Farm', on_delete=models.SET_NULL, null=True, blank=True, related_name='investment_projects')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    goal_amount = models.DecimalField(max_digits=14, decimal_places=2)
    current_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    min_investment = models.DecimalField(max_digits=12, decimal_places=2, default=10)
    expected_return = models.DecimalField(max_digits=5, decimal_places=2, help_text="Expected ROI %")
    
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    duration_months = models.IntegerField()
    
    images = models.JSONField(default=list, blank=True)
    
    class Meta:
        db_table = 'farm_investment_projects'
    
    def __str__(self):
        return f"{self.title} - {self.farmer}"
    
    def invest(self, investor, amount):
        """Process investment"""
        amount = Decimal(str(amount))
        if self.current_amount + amount <= self.goal_amount:
            Investment.objects.create(
                project=self,
                investor=investor,
                amount=amount,
                expected_return=self.expected_return
            )
            self.current_amount += amount
            self.save()
            
            # Transfer funds to farmer's wallet (minus 5% platform fee)
            platform_fee = amount * Decimal('0.05')
            farmer_amount = amount - platform_fee
            
            self.farmer.wallet.deposit(farmer_amount, f'investment_{self.id}', source='investment')
            return True
        return False


class Investment(models.Model):
    """Individual investment record"""
    
    project = models.ForeignKey(FarmInvestmentProject, on_delete=models.CASCADE, related_name='investments')
    investor = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    expected_return = models.DecimalField(max_digits=5, decimal_places=2)
    
    invested_at = models.DateTimeField(auto_now_add=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    return_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'investments'
    
    def __str__(self):
        return f"{self.investor} - {self.project.title} - {self.amount}"
    
    def calculate_return(self):
        """Calculate final return amount"""
        self.return_amount = self.amount * (1 + self.expected_return / 100)
        return self.return_amount
