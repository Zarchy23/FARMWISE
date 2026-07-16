# core/models_market.py
# Market Price Intelligence Models
# For agricultural commodity pricing, trends, and farmer sales

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import json

class Commodity(models.Model):
    """Agricultural commodity catalog"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=[
        ('grain', 'Grain/Cereals'),
        ('vegetable', 'Vegetables'),
        ('fruit', 'Fruits'),
        ('legume', 'Legumes'),
        ('oilseed', 'Oilseeds'),
        ('spice', 'Spices'),
        ('fiber', 'Fiber Crops'),
        ('root_tuber', 'Root & Tuber'),
        ('other', 'Other'),
    ])
    unit = models.CharField(max_length=20, default='kg')  # kg, ton, liter, bunch, etc.
    seasonality = models.JSONField(default=dict, help_text="JSON with peak/lean seasons")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'commodities'
        verbose_name_plural = 'Commodities'
    
    def __str__(self):
        return f"{self.name} ({self.unit})"


class MarketPrice(models.Model):
    """Real-time and historical commodity prices"""
    
    SOURCE_CHOICES = [
        ('api', 'External API'),
        ('market_report', 'Market Report'),
        ('farmer_submission', 'Farmer Submission'),
        ('crawler', 'Web Crawler'),
    ]
    
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, related_name='prices')
    region = models.CharField(max_length=100, help_text="Region/Market location")
    country = models.CharField(max_length=100, default='Kenya')
    
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='KES')
    
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='api')
    source_name = models.CharField(max_length=100, blank=True, help_text="Name of the market or source")
    
    price_date = models.DateField(auto_now_add=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    # Quality metrics
    quality_grade = models.CharField(max_length=50, blank=True, choices=[
        ('premium', 'Premium'),
        ('grade1', 'Grade 1'),
        ('grade2', 'Grade 2'),
        ('mixed', 'Mixed'),
    ])
    
    volume_traded = models.IntegerField(blank=True, null=True, help_text="In units of commodity")
    
    class Meta:
        db_table = 'market_prices'
        indexes = [
            models.Index(fields=['commodity', 'price_date', 'region']),
            models.Index(fields=['recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.commodity.name} - {self.price} {self.currency} ({self.region})"


class PriceTrend(models.Model):
    """Calculated price trends and analytics"""
    
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, related_name='trends')
    region = models.CharField(max_length=100)
    
    # Period: week, month, quarter
    period = models.CharField(max_length=20, choices=[
        ('week', 'Weekly'),
        ('month', 'Monthly'),
        ('quarter', 'Quarterly'),
        ('year', 'Yearly'),
    ])
    
    # Trend data
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    std_dev = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    
    # Change metrics
    price_change = models.DecimalField(max_digits=10, decimal_places=2)  # vs previous period
    percent_change = models.DecimalField(max_digits=5, decimal_places=2)
    
    trend_direction = models.CharField(max_length=10, choices=[
        ('up', 'Increasing'),
        ('down', 'Decreasing'),
        ('stable', 'Stable'),
    ])
    
    # Volatility
    volatility_score = models.FloatField(default=0.0)  # 0-100
    
    # Date info
    period_start = models.DateField()
    period_end = models.DateField()
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'price_trends'
        unique_together = ['commodity', 'region', 'period', 'period_start']
        indexes = [
            models.Index(fields=['commodity', 'period_start']),
        ]
    
    def __str__(self):
        return f"{self.commodity.name} - {self.period} trend ({self.region})"


class PriceAlert(models.Model):
    """Price alerts for farmers"""
    
    ALERT_TYPE = [
        ('threshold_high', 'Price Above Threshold'),
        ('threshold_low', 'Price Below Threshold'),
        ('trend_change', 'Trend Changed'),
        ('peak_price', 'Peak Price Detected'),
    ]
    
    farmer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='price_alerts')
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    region = models.CharField(max_length=100)
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE)
    
    # For threshold alerts
    threshold_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_triggered = models.BooleanField(default=False)
    triggered_at = models.DateTimeField(blank=True, null=True)
    
    # Notification
    notify_email = models.BooleanField(default=True)
    notify_sms = models.BooleanField(default=False)
    notify_push = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'price_alerts'
        indexes = [
            models.Index(fields=['farmer', 'is_active']),
            models.Index(fields=['commodity', 'is_triggered']),
        ]
    
    def __str__(self):
        return f"{self.alert_type} - {self.commodity.name}"


class SellerListing(models.Model):
    """Farmer's product listings for direct sales"""
    
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='seller_listings')
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, related_name='listings')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    
    asking_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    currency = models.CharField(max_length=3, default='KES')
    
    quantity_available = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    quantity_unit = models.CharField(max_length=20)
    
    quality_grade = models.CharField(max_length=50, blank=True, choices=[
        ('premium', 'Premium'),
        ('grade1', 'Grade 1'),
        ('grade2', 'Grade 2'),
        ('mixed', 'Mixed'),
    ])
    
    # Farm info
    harvest_date = models.DateField(blank=True, null=True)
    storage_location = models.CharField(max_length=255, blank=True)
    
    # Media
    images = models.JSONField(default=list)  # List of image URLs
    
    # Status
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('pending', 'Pending Sale'),
        ('sold', 'Sold'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    
    # Visibility
    is_public = models.BooleanField(default=True)
    views = models.IntegerField(default=0)
    inquiry_count = models.IntegerField(default=0)
    
    # Engagement
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_listings', blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="Listing expires after this date")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'seller_listings'
        indexes = [
            models.Index(fields=['commodity', 'status', 'created_at']),
            models.Index(fields=['seller', 'status']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.seller.first_name}"


class BuyerInquiry(models.Model):
    """Inquiries from buyers to sellers"""
    
    listing = models.ForeignKey(SellerListing, on_delete=models.CASCADE, related_name='buyer_inquiries_list')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='buyer_inquiries')
    
    quantity_interested = models.DecimalField(max_digits=12, decimal_places=2)
    message = models.TextField()
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('negotiating', 'Negotiating'),
        ('completed', 'Completed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Communication
    replies_count = models.IntegerField(default=0)
    last_reply_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'buyer_inquiries'
        unique_together = ['listing', 'buyer']
    
    def __str__(self):
        return f"Inquiry for {self.listing.title} from {self.buyer.first_name}"


class MarketAnalytics(models.Model):
    """Market-wide analytics and insights"""
    
    commodity = models.OneToOneField(Commodity, on_delete=models.CASCADE, related_name='analytics')
    
    # Current market state
    current_avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    last_7_day_avg = models.DecimalField(max_digits=10, decimal_places=2)
    last_30_day_avg = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Predictions
    next_week_forecast = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    next_month_forecast = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Market health
    active_sellers = models.IntegerField(default=0)
    total_listings = models.IntegerField(default=0)
    avg_listing_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Best time to sell (based on historical data)
    best_sell_month = models.CharField(max_length=20, blank=True)
    best_sell_season = models.CharField(max_length=20, blank=True)
    best_sell_price_avg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Recommendation
    recommendation = models.CharField(max_length=50, choices=[
        ('buy_now', 'Good Time to Buy'),
        ('sell_now', 'Good Time to Sell'),
        ('hold', 'Wait/Hold'),
        ('neutral', 'Market Neutral'),
    ], default='neutral')
    recommendation_reason = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)  # 0-100
    
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'market_analytics'
    
    def __str__(self):
        return f"Market Analytics for {self.commodity.name}"
