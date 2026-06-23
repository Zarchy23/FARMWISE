# core/payments/webhooks.py
# Payment Gateway Webhooks

import stripe
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings

from core.models_payments import PaymentTransaction, FarmWallet, EscrowPayment, SellerPayout
from core.models import User

logger = logging.getLogger(__name__)

# ============================================================
# STRIPE WEBHOOKS
# ============================================================

@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events"""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.error("Invalid Stripe payload")
        return JsonResponse({'error': 'Invalid payload'}, status=400)
    except stripe.error.SignatureVerificationError:
        logger.error("Invalid Stripe signature")
        return JsonResponse({'error': 'Invalid signature'}, status=400)
    
    # Handle different event types
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        try:
            transaction = PaymentTransaction.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            transaction.mark_completed()
            logger.info(f"Payment {payment_intent['id']} completed")
        except PaymentTransaction.DoesNotExist:
            logger.warning(f"Transaction not found for payment {payment_intent['id']}")
    
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        
        try:
            transaction = PaymentTransaction.objects.get(
                stripe_payment_intent_id=payment_intent['id']
            )
            transaction.mark_failed('Card declined or payment failed')
            logger.info(f"Payment {payment_intent['id']} failed")
        except PaymentTransaction.DoesNotExist:
            logger.warning(f"Transaction not found for failed payment {payment_intent['id']}")
    
    elif event['type'] == 'charge.refunded':
        charge = event['data']['object']
        
        try:
            transaction = PaymentTransaction.objects.get(
                stripe_payment_intent_id=charge['payment_intent']
            )
            if charge.get('refunded'):
                transaction.status = 'refunded'
                transaction.save()
                logger.info(f"Payment {charge['id']} refunded")
        except PaymentTransaction.DoesNotExist:
            logger.warning(f"Transaction not found for refund {charge['id']}")
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        logger.info(f"Subscription {subscription['id']} updated")
    
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        logger.info(f"Invoice {invoice['id']} paid")
    
    return JsonResponse({'status': 'success'})


# ============================================================
# MPESA WEBHOOKS
# ============================================================

@csrf_exempt
@require_POST
def mpesa_webhook(request):
    """Handle M-Pesa callback"""
    try:
        data = json.loads(request.body)
        
        # M-Pesa callback structure
        result = data.get('Body', {}).get('stkCallback', {})
        result_code = result.get('ResultCode')
        checkout_request_id = result.get('CheckoutRequestID')
        
        try:
            transaction = PaymentTransaction.objects.get(
                mpesa_request_id=checkout_request_id
            )
            
            if result_code == 0:  # Success
                transaction.mark_completed()
                logger.info(f"M-Pesa payment {checkout_request_id} successful")
            else:
                transaction.mark_failed(f"M-Pesa error code: {result_code}")
                logger.info(f"M-Pesa payment {checkout_request_id} failed with code {result_code}")
        
        except PaymentTransaction.DoesNotExist:
            logger.warning(f"Transaction not found for M-Pesa callback {checkout_request_id}")
        
        return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
    
    except Exception as e:
        logger.error(f"M-Pesa webhook error: {str(e)}")
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Error'}, status=400)


# ============================================================
# ECOCASH WEBHOOKS
# ============================================================

@csrf_exempt
@require_POST
def ecocash_webhook(request):
    """Handle EcoCash callback"""
    try:
        data = json.loads(request.body)
        
        transaction_id = data.get('transaction_id')
        status = data.get('status')
        
        try:
            transaction = PaymentTransaction.objects.get(
                ecocash_transaction_id=transaction_id
            )
            
            if status == 'SUCCESS':
                transaction.mark_completed()
                logger.info(f"EcoCash payment {transaction_id} successful")
            elif status in ['FAILED', 'CANCELLED']:
                transaction.mark_failed(f"EcoCash payment {status}")
                logger.info(f"EcoCash payment {transaction_id} failed: {status}")
            
        except PaymentTransaction.DoesNotExist:
            logger.warning(f"Transaction not found for EcoCash callback {transaction_id}")
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        logger.error(f"EcoCash webhook error: {str(e)}")
        return JsonResponse({'status': 'error'}, status=400)


# ============================================================
# ZIPIT WEBHOOKS
# ============================================================

@csrf_exempt
@require_POST
def zipit_webhook(request):
    """Handle Zipit payment callback"""
    try:
        data = json.loads(request.body)
        
        payment_id = data.get('payment_id')
        status = data.get('status')
        reference = data.get('reference')
        
        try:
            transaction = PaymentTransaction.objects.get(
                external_reference=reference
            )
            
            if status == 'completed':
                transaction.mark_completed()
                logger.info(f"Zipit payment {payment_id} successful")
            elif status == 'failed':
                transaction.mark_failed('Zipit payment failed')
                logger.info(f"Zipit payment {payment_id} failed")
            
        except PaymentTransaction.DoesNotExist:
            logger.warning(f"Transaction not found for Zipit callback {reference}")
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Zipit webhook error: {str(e)}")
        return JsonResponse({'status': 'error'}, status=400)


# ============================================================
# PAYOUT WEBHOOKS
# ============================================================

@csrf_exempt
@require_POST
def payout_webhook(request):
    """Handle payout status updates"""
    try:
        data = json.loads(request.body)
        
        payout_id = data.get('payout_id')
        status = data.get('status')
        
        try:
            from .models_payments import SellerPayout
            payout = SellerPayout.objects.get(id=payout_id)
            
            if status == 'completed':
                payout.status = 'completed'
                payout.processed_at = timezone.now()
                payout.save()
                logger.info(f"Payout {payout_id} completed")
            elif status == 'failed':
                payout.status = 'failed'
                payout.notes = data.get('error_message', 'Unknown error')
                payout.save()
                logger.error(f"Payout {payout_id} failed: {data.get('error_message')}")
        
        except SellerPayout.DoesNotExist:
            logger.warning(f"Payout not found: {payout_id}")
        
        return JsonResponse({'status': 'success'})
    
    except Exception as e:
        logger.error(f"Payout webhook error: {str(e)}")
        return JsonResponse({'status': 'error'}, status=400)
