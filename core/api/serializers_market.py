# core/api/serializers_market.py
# Market Price API Serializers

from rest_framework import serializers
from core.models_market import (
    Commodity, MarketPrice, PriceTrend, PriceAlert, 
    SellerListing, BuyerInquiry, MarketAnalytics
)
from core.models import User


class CommoditySerializer(serializers.ModelSerializer):
    class Meta:
        model = Commodity
        fields = ['id', 'name', 'category', 'unit', 'description']


class MarketPriceSerializer(serializers.ModelSerializer):
    commodity_name = serializers.CharField(source='commodity.name', read_only=True)
    
    class Meta:
        model = MarketPrice
        fields = [
            'id', 'commodity_name', 'price', 'currency', 
            'region', 'source', 'source_name', 'price_date', 
            'quality_grade', 'volume_traded'
        ]
        read_only_fields = ['recorded_at']


class PriceTrendSerializer(serializers.ModelSerializer):
    commodity_name = serializers.CharField(source='commodity.name', read_only=True)
    
    class Meta:
        model = PriceTrend
        fields = [
            'id', 'commodity_name', 'region', 'period',
            'avg_price', 'min_price', 'max_price', 'std_dev',
            'price_change', 'percent_change', 'trend_direction',
            'volatility_score', 'period_start', 'period_end'
        ]


class PriceAlertSerializer(serializers.ModelSerializer):
    commodity_name = serializers.CharField(source='commodity.name', read_only=True)
    farmer_name = serializers.CharField(source='farmer.get_full_name', read_only=True)
    
    class Meta:
        model = PriceAlert
        fields = [
            'id', 'farmer_name', 'commodity_name', 'region',
            'alert_type', 'threshold_price', 'is_active',
            'is_triggered', 'triggered_at', 'notify_email',
            'notify_sms', 'notify_push'
        ]
        read_only_fields = ['triggered_at']


class SellerListingSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.get_full_name', read_only=True)
    commodity_name = serializers.CharField(source='commodity.name', read_only=True)
    likes_count = serializers.SerializerMethodField()
    days_to_expire = serializers.SerializerMethodField()
    
    class Meta:
        model = SellerListing
        fields = [
            'id', 'seller_name', 'commodity_name', 'title', 'description',
            'asking_price', 'currency', 'quantity_available', 'quantity_unit',
            'quality_grade', 'harvest_date', 'storage_location',
            'images', 'status', 'views', 'inquiries', 'likes_count',
            'created_at', 'expires_at', 'days_to_expire'
        ]
        read_only_fields = ['views', 'inquiries', 'created_at']
    
    def get_likes_count(self, obj):
        return obj.likes.count()
    
    def get_days_to_expire(self, obj):
        from django.utils import timezone
        delta = obj.expires_at - timezone.now()
        return max(delta.days, 0)


class BuyerInquirySerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.get_full_name', read_only=True)
    listing_title = serializers.CharField(source='listing.title', read_only=True)
    
    class Meta:
        model = BuyerInquiry
        fields = [
            'id', 'buyer_name', 'listing_title', 'quantity_interested',
            'message', 'status', 'replies_count', 'last_reply_at',
            'created_at'
        ]
        read_only_fields = ['replies_count', 'last_reply_at', 'created_at']


class MarketAnalyticsSerializer(serializers.ModelSerializer):
    commodity_name = serializers.CharField(source='commodity.name', read_only=True)
    
    class Meta:
        model = MarketAnalytics
        fields = [
            'commodity_name', 'current_avg_price', 'last_7_day_avg',
            'last_30_day_avg', 'next_week_forecast', 'next_month_forecast',
            'active_sellers', 'total_listings', 'avg_listing_price',
            'best_sell_month', 'best_sell_season', 'best_sell_price_avg',
            'recommendation', 'recommendation_reason', 'confidence_score'
        ]
