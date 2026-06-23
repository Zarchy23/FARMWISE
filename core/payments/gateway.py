# core/payments/gateway.py
# FARMWISE - Unified Payment Gateway
# Stripe, M-Pesa, Zimbabwe Payments + Wallet

import stripe
import requests
import hashlib
import hmac
import base64
import json
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# ============================================================
# UNIFIED PAYMENT GATEWAY
# ============================================================

class PaymentGateway:
    """Unified payment gateway routing to appropriate provider"""
    
    PAYMENT_METHODS = {
        'card': 'Stripe',
        'mobile_money': 'Mobile Money',
        'ecocash': 'EcoCash',
        'zipit': 'Zipit',
        'rtgs': 'Bank Transfer',
        'wallet': 'FarmWise Wallet',
    }
    
    def __init__(self):
        self.stripe = StripePayment()
        self.mpesa = MpesaPayment()
        self.ecocash = EcoCashPayment()
        self.zipit = ZipitPayment()
    
    def process_payment(self, amount, currency, payment_method, customer_details):
        """Route payment to appropriate processor"""
        
        if payment_method == 'card':
            return self.stripe.process_payment(amount, currency, customer_details)
        elif payment_method == 'mobile_money':
            return self.mpesa.initiate_payment(
                phone_number=customer_details.get('phone'),
                amount=amount,
                reference=customer_details.get('reference'),
                description=customer_details.get('description', 'FarmWise Payment')
            )
        elif payment_method == 'ecocash':
            return self.ecocash.initiate_payment(
                phone_number=customer_details.get('phone'),
                amount=amount,
                reference=customer_details.get('reference'),
                description=customer_details.get('description', 'FarmWise Payment')
            )
        elif payment_method == 'zipit':
            return self.zipit.initiate_payment(
                account_number=customer_details.get('account_number'),
                bank_code=customer_details.get('bank_code'),
                amount=amount,
                reference=customer_details.get('reference')
            )
        elif payment_method == 'wallet':
            return {'success': True, 'message': 'Payment via wallet'}
        else:
            return {'success': False, 'error': 'Payment method not supported'}
    
    def get_payment_status(self, payment_method, reference):
        """Check payment status"""
        if payment_method == 'card':
            return self.stripe.get_status(reference)
        elif payment_method == 'mobile_money':
            return self.mpesa.query_status(reference)
        elif payment_method == 'ecocash':
            return self.ecocash.check_transaction_status(reference)
        else:
            return {'status': 'unknown'}


# ============================================================
# STRIPE PAYMENT PROCESSOR
# ============================================================

class StripePayment:
    """Stripe payment integration for card processing"""
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.publishable_key = settings.STRIPE_PUBLISHABLE_KEY
    
    @staticmethod
    def create_payment_intent(amount, currency='usd', metadata=None):
        """Create Stripe payment intent"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                metadata=metadata or {},
                automatic_payment_methods={'enabled': True}
            )
            return {
                'success': True,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def confirm_payment(payment_intent_id):
        """Confirm payment completion"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'success': intent.status == 'succeeded',
                'status': intent.status,
                'amount': intent.amount / 100  # Convert back to dollars
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def refund_payment(payment_intent_id, amount=None):
        """Process refund"""
        try:
            if amount:
                refund = stripe.Refund.create(
                    payment_intent=payment_intent_id,
                    amount=int(amount * 100)
                )
            else:
                refund = stripe.Refund.create(
                    payment_intent=payment_intent_id
                )
            return {
                'success': refund.status == 'succeeded',
                'refund_id': refund.id
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_customer(email, name):
        """Create Stripe customer"""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            return {'success': True, 'customer_id': customer.id}
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def create_subscription(customer_id, price_id):
        """Create Stripe subscription"""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            return {
                'success': True,
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def process_payment(self, amount, currency, customer_details):
        """Process card payment"""
        return self.create_payment_intent(
            amount=amount,
            currency=currency.lower(),
            metadata=customer_details
        )
    
    def get_status(self, payment_intent_id):
        """Get payment status"""
        return self.confirm_payment(payment_intent_id)


# ============================================================
# MPESA PAYMENT PROCESSOR
# ============================================================

class MpesaPayment:
    """M-Pesa integration for East Africa"""
    
    def __init__(self):
        self.consumer_key = settings.MPESA_CONSUMER_KEY
        self.consumer_secret = settings.MPESA_CONSUMER_SECRET
        self.passkey = settings.MPESA_PASSKEY
        self.shortcode = settings.MPESA_SHORTCODE
        self.callback_url = settings.MPESA_CALLBACK_URL
    
    def get_access_token(self):
        """Get M-Pesa API access token"""
        cache_key = 'mpesa_access_token'
        token = cache.get(cache_key)
        
        if token:
            return token
        
        try:
            api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
            response = requests.get(
                api_url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=10
            )
            data = response.json()
            token = data.get('access_token')
            cache.set(cache_key, token, 3600)
            return token
        except requests.RequestException as e:
            logger.error(f"M-Pesa token error: {str(e)}")
            return None
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Initiate STK push payment"""
        access_token = self.get_access_token()
        if not access_token:
            return {'success': False, 'error': 'Could not get access token'}
        
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": self._format_phone_number(phone_number),
            "PartyB": self.shortcode,
            "PhoneNumber": self._format_phone_number(phone_number),
            "CallBackURL": self.callback_url,
            "AccountReference": account_reference,
            "TransactionDesc": transaction_desc
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            data = response.json()
            return {
                'success': data.get('ResponseCode') == '0',
                'transaction_id': data.get('CheckoutRequestID'),
                'message': data.get('ResponseDescription', 'Payment initiated')
            }
        except requests.RequestException as e:
            logger.error(f"M-Pesa error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def query_status(self, checkout_request_id):
        """Query transaction status"""
        access_token = self.get_access_token()
        if not access_token:
            return {'status': 'unknown'}
        
        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query"
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            f"{self.shortcode}{self.passkey}{timestamp}".encode()
        ).decode()
        
        payload = {
            "BusinessShortCode": self.shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "CheckoutRequestID": checkout_request_id
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            data = response.json()
            
            status_map = {
                '0': 'completed',
                '1': 'pending',
                '1032': 'cancelled',
            }
            
            return {
                'status': status_map.get(data.get('ResultCode', '1'), 'unknown'),
                'merchant_request_id': data.get('MerchantRequestID'),
                'checkout_request_id': data.get('CheckoutRequestID'),
            }
        except requests.RequestException as e:
            logger.error(f"M-Pesa error: {str(e)}")
            return {'status': 'unknown'}
    
    def initiate_payment(self, phone_number, amount, reference, description):
        """Initiate M-Pesa payment"""
        return self.stk_push(phone_number, amount, reference, description)
    
    @staticmethod
    def _format_phone_number(phone):
        """Format phone number for M-Pesa (254XXXXXXXXX)"""
        phone = ''.join(filter(str.isdigit, phone))
        
        if phone.startswith('254'):
            return phone
        elif phone.startswith('+254'):
            return phone[1:]
        elif phone.startswith('0'):
            return '254' + phone[1:]
        else:
            return '254' + phone[-9:]


# ============================================================
# ECOCASH PAYMENT PROCESSOR (ZIMBABWE)
# ============================================================

class EcoCashPayment:
    """EcoCash payment integration for Zimbabwe"""
    
    def __init__(self):
        self.api_key = settings.ECOCASH_API_KEY
        self.api_secret = settings.ECOCASH_API_SECRET
        self.merchant_code = settings.ECOCASH_MERCHANT_CODE
        self.callback_url = settings.ECOCASH_CALLBACK_URL
        self.base_url = getattr(settings, 'ECOCASH_BASE_URL', 'https://api.ecocash.co.zw/v1')
    
    def get_access_token(self):
        """Get OAuth access token for EcoCash API"""
        cache_key = 'ecocash_access_token'
        token = cache.get(cache_key)
        
        if token:
            return token
        
        auth_string = f"{self.api_key}:{self.api_secret}"
        encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {encoded_auth}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/token",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)
                cache.set(cache_key, token, expires_in - 60)
                return token
        except requests.RequestException as e:
            logger.error(f"EcoCash error: {str(e)}")
        
        return None
    
    def initiate_payment(self, phone_number, amount, reference, description):
        """Initiate EcoCash payment (STK Push)"""
        access_token = self.get_access_token()
        if not access_token:
            return {'success': False, 'error': 'Could not get access token'}
        
        phone = self._format_phone_number(phone_number)
        
        payload = {
            "merchant_code": self.merchant_code,
            "msisdn": phone,
            "amount": str(amount),
            "reference": reference,
            "description": description,
            "callback_url": self.callback_url,
            "timestamp": datetime.now().isoformat()
        }
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/transactions/payment",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            data = response.json()
            return {
                'success': data.get('status') == 'pending',
                'transaction_id': data.get('transaction_id'),
                'status': data.get('status'),
                'message': data.get('message', 'Payment initiated')
            }
        except requests.RequestException as e:
            logger.error(f"EcoCash error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def check_transaction_status(self, transaction_id):
        """Check EcoCash transaction status"""
        access_token = self.get_access_token()
        if not access_token:
            return {'status': 'unknown'}
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/transactions/status/{transaction_id}",
                headers=headers,
                timeout=10
            )
            
            data = response.json()
            status_map = {
                'PENDING': 'pending',
                'SUCCESS': 'completed',
                'FAILED': 'failed',
                'CANCELLED': 'cancelled'
            }
            
            return {
                'status': status_map.get(data.get('status'), 'unknown'),
                'amount': data.get('amount'),
                'transaction_id': data.get('transaction_id'),
            }
        except requests.RequestException as e:
            logger.error(f"EcoCash error: {str(e)}")
            return {'status': 'unknown', 'error': str(e)}
    
    @staticmethod
    def _format_phone_number(phone):
        """Format phone number for EcoCash (077XXXXXXX)"""
        phone = ''.join(filter(str.isdigit, phone))
        
        if phone.startswith('263'):
            phone = '0' + phone[3:]
        elif phone.startswith('+263'):
            phone = '0' + phone[4:]
        
        if not phone.startswith('07'):
            phone = '07' + phone[-8:]
        
        return phone


# ============================================================
# ZIPIT PAYMENT PROCESSOR (ZIMBABWE)
# ============================================================

class ZipitPayment:
    """Zipit instant bank transfer integration"""
    
    def __init__(self):
        self.api_key = settings.ZIPIT_API_KEY
        self.api_secret = settings.ZIPIT_API_SECRET
        self.merchant_id = settings.ZIPIT_MERCHANT_ID
        self.base_url = getattr(settings, 'ZIPIT_BASE_URL', 'https://api.zipit.co.zw/v1')
    
    @staticmethod
    def generate_signature(payload, api_secret):
        """Generate HMAC signature for Zipit"""
        message = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def initiate_payment(self, account_number, bank_code, amount, reference):
        """Initiate Zipit payment from bank account"""
        payload = {
            "merchantId": self.merchant_id,
            "accountNumber": account_number,
            "bankCode": bank_code,
            "amount": str(amount),
            "reference": reference,
            "callbackUrl": getattr(settings, 'ZIPIT_CALLBACK_URL', 'https://yourdomain.com/webhooks/zipit/')
        }
        
        signature = self.generate_signature(payload, self.api_secret)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Signature": signature,
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/payments/initiate",
                json=payload,
                headers=headers,
                timeout=10
            )
            
            data = response.json()
            return {
                'success': data.get('status') == 'initiated',
                'payment_id': data.get('payment_id'),
                'message': data.get('message', 'Payment initiated')
            }
        except requests.RequestException as e:
            logger.error(f"Zipit error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_payment(self, payment_id):
        """Verify Zipit payment status"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/payments/{payment_id}/status",
                headers=headers,
                timeout=10
            )
            
            data = response.json()
            return {
                'status': data.get('status'),
                'amount': data.get('amount'),
            }
        except requests.RequestException as e:
            logger.error(f"Zipit error: {str(e)}")
            return {'status': 'unknown', 'error': str(e)}
