# core/payments/admin.py
# Django admin interface for payment models

from django.contrib import admin
from core.models_payments import (
    FarmWallet, WalletTransaction, PaymentMethod, PaymentTransaction,
    SubscriptionPlan, UserSubscription, PlanChange, Invoice,
    EscrowPayment, SellerPayout, FarmLoan, LoanPayment, CreditScore,
    FarmSavings, SavingsTransaction, FarmInvestmentProject, Investment
)


@admin.register(FarmWallet)
class FarmWalletAdmin(admin.ModelAdmin):
    list_display = ['user', 'balance', 'currency', 'is_frozen', 'created_at']
    list_filter = ['is_frozen', 'currency']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['total_deposited', 'total_withdrawn', 'created_at', 'updated_at']


@admin.register(WalletTransaction)
class WalletTransactionAdmin(admin.ModelAdmin):
    list_display = ['wallet', 'transaction_type', 'amount', 'status', 'reference', 'created_at']
    list_filter = ['status', 'transaction_type', 'created_at']
    search_fields = ['wallet__user__username', 'reference']
    readonly_fields = ['created_at', 'completed_at']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'method_type', 'is_default', 'is_verified', 'is_active']
    list_filter = ['method_type', 'is_default', 'is_verified']
    search_fields = ['user__username', 'mobile_number', 'bank_name']


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'user', 'transaction_type', 'amount', 'status', 'created_at']
    list_filter = ['status', 'transaction_type', 'created_at']
    search_fields = ['transaction_id', 'user__username', 'external_reference']
    readonly_fields = ['transaction_id', 'created_at', 'completed_at', 'failed_at']


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price_monthly', 'price_yearly', 'is_active', 'display_order']
    list_filter = ['plan_type', 'is_active', 'api_access', 'priority_support']
    ordering = ['display_order']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'auto_renew', 'renewal_date']
    list_filter = ['status', 'billing_cycle', 'auto_renew']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['start_date', 'created_at', 'updated_at']


@admin.register(PlanChange)
class PlanChangeAdmin(admin.ModelAdmin):
    list_display = ['user', 'change_type', 'old_plan', 'new_plan', 'created_at']
    list_filter = ['change_type', 'created_at']
    search_fields = ['user__username']
    readonly_fields = ['created_at']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'user', 'invoice_date', 'status', 'total_amount']
    list_filter = ['status', 'invoice_date']
    search_fields = ['invoice_number', 'user__username']
    readonly_fields = ['invoice_number', 'created_at', 'updated_at']


@admin.register(EscrowPayment)
class EscrowPaymentAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'seller', 'amount', 'status', 'hold_date']
    list_filter = ['status', 'hold_date']
    search_fields = ['buyer__username', 'seller__username']


@admin.register(SellerPayout)
class SellerPayoutAdmin(admin.ModelAdmin):
    list_display = ['seller', 'amount', 'payout_method', 'status', 'created_at']
    list_filter = ['status', 'payout_method', 'created_at']
    search_fields = ['seller__username']


@admin.register(FarmLoan)
class FarmLoanAdmin(admin.ModelAdmin):
    list_display = ['farmer', 'amount_requested', 'amount_approved', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['farmer__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LoanPayment)
class LoanPaymentAdmin(admin.ModelAdmin):
    list_display = ['loan', 'amount', 'payment_date', 'payment_method']
    list_filter = ['payment_method', 'payment_date']
    readonly_fields = ['payment_date']


@admin.register(CreditScore)
class CreditScoreAdmin(admin.ModelAdmin):
    list_display = ['user', 'score', 'eligible_for_credit', 'eligible_loan_amount', 'last_calculated']
    list_filter = ['eligible_for_credit']
    search_fields = ['user__username']


@admin.register(FarmSavings)
class FarmSavingsAdmin(admin.ModelAdmin):
    list_display = ['farmer', 'balance', 'interest_rate', 'goal_amount', 'total_interest_earned']
    search_fields = ['farmer__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SavingsTransaction)
class SavingsTransactionAdmin(admin.ModelAdmin):
    list_display = ['savings', 'transaction_type', 'amount', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    readonly_fields = ['created_at']


@admin.register(FarmInvestmentProject)
class FarmInvestmentProjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'farmer', 'goal_amount', 'current_amount', 'status']
    list_filter = ['status', 'start_date']
    search_fields = ['title', 'farmer__username']


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['investor', 'project', 'amount', 'invested_at']
    list_filter = ['invested_at']
    search_fields = ['investor__username', 'project__title']
    readonly_fields = ['invested_at']
