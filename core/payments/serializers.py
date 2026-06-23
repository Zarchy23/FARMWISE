# core/payments/serializers.py
# Payment System Serializers

from rest_framework import serializers
from core.models_payments import (
    FarmWallet, WalletTransaction, PaymentMethod, PaymentTransaction,
    SubscriptionPlan, UserSubscription, Invoice, EscrowPayment,
    FarmLoan, LoanPayment, FarmSavings, FarmInvestmentProject
)


class FarmWalletSerializer(serializers.ModelSerializer):
    """Wallet serializer"""
    
    class Meta:
        model = FarmWallet
        fields = ['id', 'balance', 'currency', 'total_deposited', 'total_withdrawn', 'is_frozen', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Wallet transaction serializer"""
    
    class Meta:
        model = WalletTransaction
        fields = ['id', 'amount', 'transaction_type', 'reference', 'status', 'created_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'completed_at']


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Payment method serializer"""
    
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'method_type', 'display_name',
            'card_last_four', 'card_expiry_month', 'card_expiry_year',
            'mobile_provider', 'mobile_number',
            'bank_name', 'bank_code',
            'is_default', 'is_verified', 'is_active',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_display_name(self, obj):
        """Get display name for payment method"""
        if obj.method_type == 'card':
            return f"{obj.card_provider} ending in {obj.card_last_four}"
        elif obj.method_type == 'mobile_money':
            return f"{obj.mobile_provider} {obj.mobile_number}"
        elif obj.method_type == 'bank':
            return f"{obj.bank_name} {obj.account_number[-4:]}"
        return obj.get_method_type_display()


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer"""
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 'transaction_id', 'transaction_type', 'amount', 'currency',
            'status', 'payment_status', 'description', 'external_reference',
            'platform_fee', 'gateway_fee', 'total_fee',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'transaction_id', 'created_at', 'completed_at']


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Subscription plan serializer"""
    
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'plan_type', 'name', 'description',
            'price_monthly', 'price_yearly',
            'features', 'max_farms', 'max_fields', 'max_livestock',
            'api_access', 'priority_support', 'advanced_analytics',
            'display_order'
        ]
        read_only_fields = ['id']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """User subscription serializer"""
    
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'plan', 'plan_details', 'billing_cycle', 'status',
            'start_date', 'end_date', 'renewal_date',
            'auto_renew', 'total_paid', 'billing_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class InvoiceSerializer(serializers.ModelSerializer):
    """Invoice serializer"""
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'invoice_date', 'due_date',
            'status', 'subtotal', 'tax_amount', 'discount_amount',
            'total_amount', 'paid_amount', 'description',
            'sent_at', 'viewed_at', 'paid_at',
            'created_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'created_at']


class EscrowPaymentSerializer(serializers.ModelSerializer):
    """Escrow payment serializer"""
    
    class Meta:
        model = EscrowPayment
        fields = [
            'id', 'order', 'buyer', 'seller', 'amount', 'currency',
            'status', 'hold_date', 'release_date', 'refund_date',
            'dispute_reason'
        ]
        read_only_fields = ['id', 'hold_date', 'release_date', 'refund_date']


class FarmLoanSerializer(serializers.ModelSerializer):
    """Farm loan serializer"""
    
    total_paid = serializers.SerializerMethodField()
    remaining_balance = serializers.SerializerMethodField()
    
    class Meta:
        model = FarmLoan
        fields = [
            'id', 'amount_requested', 'amount_approved', 'interest_rate',
            'term_months', 'monthly_payment', 'status', 'purpose',
            'approved_at', 'disbursed_at', 'completed_at',
            'total_paid', 'remaining_balance',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_total_paid(self, obj):
        """Get total amount paid on loan"""
        return str(obj.payments.aggregate(total=serializers.Sum('amount')).get('total', 0))
    
    def get_remaining_balance(self, obj):
        """Get remaining balance on loan"""
        if obj.amount_approved:
            total_paid = obj.payments.aggregate(total=serializers.Sum('amount')).get('total', 0) or 0
            return str(obj.amount_approved - total_paid)
        return None


class LoanPaymentSerializer(serializers.ModelSerializer):
    """Loan payment serializer"""
    
    class Meta:
        model = LoanPayment
        fields = ['id', 'loan', 'amount', 'payment_date', 'payment_method', 'reference']
        read_only_fields = ['id', 'payment_date']


class FarmSavingsSerializer(serializers.ModelSerializer):
    """Farm savings serializer"""
    
    class Meta:
        model = FarmSavings
        fields = [
            'id', 'balance', 'interest_rate', 'goal_amount', 'goal_name',
            'total_interest_earned', 'last_interest_calculation',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FarmInvestmentProjectSerializer(serializers.ModelSerializer):
    """Farm investment project serializer"""
    
    progress_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = FarmInvestmentProject
        fields = [
            'id', 'title', 'description', 'goal_amount', 'current_amount',
            'progress_percentage', 'min_investment', 'expected_return',
            'start_date', 'end_date', 'duration_months', 'status',
            'images'
        ]
        read_only_fields = ['id', 'start_date']
    
    def get_progress_percentage(self, obj):
        """Calculate investment progress percentage"""
        if obj.goal_amount > 0:
            return int((obj.current_amount / obj.goal_amount) * 100)
        return 0
