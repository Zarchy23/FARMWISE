# core/payments/views.py
# FARMWISE - Payment API Endpoints

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from decimal import Decimal
import json

from core.models_payments import (
    FarmWallet, WalletTransaction, PaymentMethod, PaymentTransaction,
    SubscriptionPlan, UserSubscription, Invoice, EscrowPayment,
    FarmLoan, LoanPayment, FarmSavings, FarmInvestmentProject
)
from .gateway import PaymentGateway
from .serializers import (
    FarmWalletSerializer, PaymentMethodSerializer, TransactionSerializer,
    SubscriptionPlanSerializer, UserSubscriptionSerializer, InvoiceSerializer
)


class WalletViewSet(viewsets.ViewSet):
    """Wallet operations endpoints"""
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get current user's wallet"""
        wallet, created = FarmWallet.objects.get_or_create(user=request.user)
        serializer = FarmWalletSerializer(wallet)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def deposit(self, request):
        """Deposit funds to wallet"""
        wallet, created = FarmWallet.objects.get_or_create(user=request.user)
        
        amount = request.data.get('amount')
        reference = request.data.get('reference')
        
        if not amount or not reference:
            return Response(
                {'error': 'Amount and reference required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            wallet.deposit(Decimal(amount), reference)
            return Response(
                {'success': True, 'balance': str(wallet.balance)},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def withdraw(self, request):
        """Withdraw funds from wallet"""
        wallet, created = FarmWallet.objects.get_or_create(user=request.user)
        
        amount = request.data.get('amount')
        reference = request.data.get('reference')
        destination = request.data.get('destination', 'manual')
        
        if not amount or not reference:
            return Response(
                {'error': 'Amount and reference required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if wallet.withdraw(Decimal(amount), reference, destination):
            return Response(
                {'success': True, 'balance': str(wallet.balance)},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'error': 'Insufficient balance'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def transfer(self, request):
        """Transfer funds to another user"""
        wallet = get_object_or_404(FarmWallet, user=request.user)
        
        recipient_id = request.data.get('recipient_id')
        amount = request.data.get('amount')
        
        if not recipient_id or not amount:
            return Response(
                {'error': 'Recipient ID and amount required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            recipient = User.objects.get(id=recipient_id)
            recipient_wallet = FarmWallet.objects.get_or_create(user=recipient)[0]
            
            if wallet.transfer(recipient_wallet, Decimal(amount), f'transfer_{wallet.user.id}_{recipient_id}'):
                return Response(
                    {'success': True, 'balance': str(wallet.balance)},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': 'Insufficient balance'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def balance(self, request):
        """Get wallet balance"""
        wallet, created = FarmWallet.objects.get_or_create(user=request.user)
        return Response({
            'balance': str(wallet.balance),
            'currency': wallet.currency,
            'available': str(wallet.get_available_balance())
        })
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get transaction history"""
        wallet, created = FarmWallet.objects.get_or_create(user=request.user)
        transactions = wallet.transactions.all().order_by('-created_at')[:50]
        
        data = []
        for t in transactions:
            data.append({
                'id': t.id,
                'type': t.transaction_type,
                'amount': str(t.amount),
                'reference': t.reference,
                'status': t.status,
                'created_at': t.created_at.isoformat()
            })
        
        return Response(data)


class PaymentMethodViewSet(viewsets.ViewSet):
    """Payment method management"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def list_methods(self, request):
        """List all payment methods for user"""
        methods = PaymentMethod.objects.filter(user=request.user, is_active=True)
        serializer = PaymentMethodSerializer(methods, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_card(self, request):
        """Add credit card as payment method"""
        # This would use Stripe's tokenization in production
        # For now, return the payment method creation
        
        card_data = {
            'user': request.user,
            'method_type': 'card',
            'card_provider': request.data.get('provider', 'visa'),
            'card_last_four': request.data.get('card_last_four'),
            'card_expiry_month': request.data.get('expiry_month'),
            'card_expiry_year': request.data.get('expiry_year'),
            'card_holder_name': request.data.get('holder_name'),
            'stripe_payment_method_id': request.data.get('stripe_token'),
            'is_default': request.data.get('is_default', False)
        }
        
        method = PaymentMethod.objects.create(**card_data)
        return Response(
            PaymentMethodSerializer(method).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'])
    def add_mobile_money(self, request):
        """Add mobile money as payment method"""
        method = PaymentMethod.objects.create(
            user=request.user,
            method_type='mobile_money',
            mobile_provider=request.data.get('provider'),
            mobile_number=request.data.get('phone_number'),
            is_default=request.data.get('is_default', False)
        )
        
        return Response(
            PaymentMethodSerializer(method).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['post'])
    def set_default(self, request):
        """Set default payment method"""
        method_id = request.data.get('method_id')
        
        PaymentMethod.objects.filter(user=request.user).update(is_default=False)
        method = get_object_or_404(PaymentMethod, id=method_id, user=request.user)
        method.is_default = True
        method.save()
        
        return Response({'success': True})


from rest_framework.views import APIView

class ProcessPaymentView(APIView):
    """Main payment processing endpoint"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Process payment through selected method"""
        amount = request.data.get('amount')
        order_id = request.data.get('order_id')
        method = request.data.get('method')  # 'card', 'mobile', 'wallet', etc.
        
        if not amount or not method:
            return Response(
                {'error': 'Amount and payment method required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Create transaction record
            transaction = PaymentTransaction.objects.create(
                transaction_id=f"TRX-{timezone.now().timestamp()}",
                user=request.user,
                transaction_type='purchase',
                amount=Decimal(amount),
                currency=request.data.get('currency', 'USD'),
                status='processing',
                metadata={'order_id': order_id}
            )
            
            # Route to appropriate payment processor
            gateway = PaymentGateway()
            
            if method == 'card':
                payment_result = gateway.stripe.create_payment_intent(
                    amount=Decimal(amount),
                    currency=request.data.get('currency', 'usd').lower(),
                    metadata={'order_id': order_id, 'user_id': request.user.id}
                )
                transaction.stripe_payment_intent_id = payment_result.get('payment_intent_id')
            
            elif method == 'mobile_money':
                payment_result = gateway.mpesa.initiate_payment(
                    phone_number=request.data.get('phone'),
                    amount=Decimal(amount),
                    reference=transaction.transaction_id,
                    description=f"FarmWise Order {order_id}"
                )
                transaction.mpesa_request_id = payment_result.get('transaction_id')
            
            elif method == 'ecocash':
                payment_result = gateway.ecocash.initiate_payment(
                    phone_number=request.data.get('phone'),
                    amount=Decimal(amount),
                    reference=transaction.transaction_id,
                    description=f"FarmWise Order {order_id}"
                )
                transaction.ecocash_transaction_id = payment_result.get('transaction_id')
            
            elif method == 'wallet':
                wallet = FarmWallet.objects.get(user=request.user)
                if wallet.balance >= Decimal(amount):
                    wallet.withdraw(Decimal(amount), transaction.transaction_id, 'payment')
                    transaction.status = 'completed'
                    payment_result = {'success': True}
                else:
                    transaction.status = 'failed'
                    transaction.failure_reason = 'Insufficient wallet balance'
                    payment_result = {'success': False, 'error': 'Insufficient balance'}
            
            transaction.save()
            
            return Response({
                'success': payment_result.get('success', False),
                'transaction_id': transaction.transaction_id,
                'client_secret': payment_result.get('client_secret'),
                'message': payment_result.get('message', 'Payment processing')
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class SubscriptionViewSet(viewsets.ViewSet):
    """Subscription management"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def available_plans(self, request):
        """Get available subscription plans"""
        plans = SubscriptionPlan.objects.filter(is_active=True)
        serializer = SubscriptionPlanSerializer(plans, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current subscription"""
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            serializer = UserSubscriptionSerializer(subscription)
            return Response(serializer.data)
        except UserSubscription.DoesNotExist:
            return Response({'error': 'No active subscription'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def upgrade(self, request):
        """Upgrade subscription plan"""
        new_plan_id = request.data.get('plan_id')
        
        try:
            new_plan = SubscriptionPlan.objects.get(id=new_plan_id)
            subscription = UserSubscription.objects.get(user=request.user)
            
            old_plan = subscription.plan
            subscription.plan = new_plan
            subscription.save()
            
            return Response({
                'success': True,
                'old_plan': old_plan.name,
                'new_plan': new_plan.name
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def cancel(self, request):
        """Cancel subscription"""
        try:
            subscription = UserSubscription.objects.get(user=request.user)
            subscription.cancel_at_end_of_period()
            return Response({'success': True, 'message': 'Subscription cancelled at end of period'})
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class LoanViewSet(viewsets.ViewSet):
    """Farm loan management"""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def apply(self, request):
        """Apply for farm loan"""
        farm_id = request.data.get('farm_id')
        amount_requested = request.data.get('amount')
        term_months = request.data.get('term_months', 12)
        purpose = request.data.get('purpose')
        
        try:
            from core.models import Farm
            farm = Farm.objects.get(id=farm_id, owner=request.user)
            
            loan = FarmLoan.objects.create(
                farmer=request.user,
                farm=farm,
                amount_requested=Decimal(amount_requested),
                term_months=term_months,
                purpose=purpose
            )
            
            return Response({
                'success': True,
                'loan_id': loan.id,
                'status': loan.status
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def list_loans(self, request):
        """List user's loans"""
        loans = FarmLoan.objects.filter(farmer=request.user).order_by('-created_at')
        
        data = []
        for loan in loans:
            data.append({
                'id': loan.id,
                'amount': str(loan.amount_requested),
                'approved_amount': str(loan.amount_approved) if loan.amount_approved else None,
                'status': loan.status,
                'term_months': loan.term_months,
                'created_at': loan.created_at.isoformat()
            })
        
        return Response(data)
