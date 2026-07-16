# core/services/market_price_service.py
# Market Price Intelligence Service
# Fetches commodity prices from various sources and provides analytics

import requests
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.utils import timezone
from django.db import models
from django.db.models import Avg, Min, Max, Q, F, StdDev, Count
from django.db.models.functions import ExtractMonth
from django.core.cache import cache
import statistics

logger = logging.getLogger(__name__)

class MarketPriceService:
    """Service for managing market prices and analytics"""
    
    # Public API sources for commodity prices
    FREE_APIs = {
        'open_food_facts': 'https://world.openfoodfacts.org/api/v0/',
        'fao_prices': 'https://www.fao.org/webservices/foodprices/',
        'commodity_plus': 'https://free-api.commodity.com/',
    }
    
    @staticmethod
    def fetch_prices_from_api(commodity_name, region='Kenya'):
        """
        Fetch commodity prices from public free APIs
        Returns list of price records or empty list if API fails
        """
        from core.models_market import MarketPrice, Commodity
        
        prices = []
        
        try:
            # Try commodity plus API (for agricultural commodities)
            response = requests.get(
                f"{MarketPriceService.FREE_APIs['commodity_plus']}search?q={commodity_name}",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                # Parse response and create price records
                for item in data.get('items', [])[:10]:  # Limit to top 10
                    price_record = {
                        'commodity_name': commodity_name,
                        'price': float(item.get('price', 0)),
                        'currency': item.get('currency', 'USD'),
                        'region': item.get('region', region),
                        'source': 'api',
                        'source_name': 'Commodity Plus',
                    }
                    prices.append(price_record)
        except Exception as e:
            logger.warning(f"API call failed for {commodity_name}: {str(e)}")
        
        return prices if prices else MarketPriceService._get_default_prices(commodity_name, region)
    
    @staticmethod
    def _get_default_prices(commodity_name, region='Kenya'):
        """Default prices for demonstration (when API unavailable)"""
        default_prices = {
            'maize': [
                {'price': 45, 'currency': 'KES', 'region': 'Central Kenya', 'source_name': 'Nairobi Market'},
                {'price': 42, 'currency': 'KES', 'region': 'Rift Valley', 'source_name': 'Uasin Gishu Market'},
                {'price': 48, 'currency': 'KES', 'region': 'Western Kenya', 'source_name': 'Kisii Market'},
            ],
            'beans': [
                {'price': 120, 'currency': 'KES', 'region': 'Central Kenya', 'source_name': 'Nairobi Market'},
                {'price': 115, 'currency': 'KES', 'region': 'Eastern Kenya', 'source_name': 'Mombasa Market'},
            ],
            'rice': [
                {'price': 85, 'currency': 'KES', 'region': 'Mombasa', 'source_name': 'Port Market'},
                {'price': 90, 'currency': 'KES', 'region': 'Nairobi', 'source_name': 'Nairobi Market'},
            ],
            'tomatoes': [
                {'price': 35, 'currency': 'KES', 'region': 'Central Kenya', 'source_name': 'Farm Gate'},
                {'price': 50, 'currency': 'KES', 'region': 'Nairobi', 'source_name': 'Nairobi Market'},
            ],
        }
        
        commodity_lower = commodity_name.lower()
        if commodity_lower in default_prices:
            return default_prices[commodity_lower]
        
        # Return generic default if not found
        return [{
            'price': 50,
            'currency': 'KES',
            'region': region,
            'source_name': 'Market Reference',
        }]
    
    @staticmethod
    def store_market_prices(commodity_id, prices_data):
        """Store fetched prices in database"""
        from core.models_market import MarketPrice, Commodity
        
        try:
            commodity = Commodity.objects.get(id=commodity_id)
            stored_count = 0
            
            for price_data in prices_data:
                # Check if similar price already exists today
                existing = MarketPrice.objects.filter(
                    commodity=commodity,
                    region=price_data.get('region'),
                    price_date=timezone.now().date()
                ).exists()
                
                if not existing:
                    MarketPrice.objects.create(
                        commodity=commodity,
                        price=Decimal(str(price_data['price'])),
                        currency=price_data.get('currency', 'KES'),
                        region=price_data.get('region'),
                        source=price_data.get('source', 'api'),
                        source_name=price_data.get('source_name', 'Market Data'),
                    )
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} prices for {commodity.name}")
            return stored_count
        
        except Commodity.DoesNotExist:
            logger.error(f"Commodity with ID {commodity_id} not found")
            return 0
    
    @staticmethod
    def calculate_price_trends(commodity_id, period_days=30):
        """Calculate price trends for commodity"""
        from core.models_market import MarketPrice, PriceTrend, Commodity
        
        try:
            commodity = Commodity.objects.get(id=commodity_id)
            
            # Get prices for the period
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=period_days)
            
            prices_by_region = {}
            prices_qs = MarketPrice.objects.filter(
                commodity=commodity,
                price_date__gte=start_date,
                price_date__lte=end_date
            ).values('region').annotate(
                avg_price=Avg('price'),
                min_price=Min('price'),
                max_price=Max('price'),
                stddev=StdDev('price'),
                count=models.Count('id')
            )
            
            for region_data in prices_qs:
                region = region_data['region']
                prices = list(
                    MarketPrice.objects.filter(
                        commodity=commodity,
                        region=region,
                        price_date__gte=start_date,
                        price_date__lte=end_date
                    ).values_list('price', flat=True)
                )
                
                if not prices or len(prices) < 2:
                    continue
                
                prices_decimal = [float(p) for p in prices]
                avg_price = Decimal(str(statistics.mean(prices_decimal)))
                min_price = Decimal(str(min(prices_decimal)))
                max_price = Decimal(str(max(prices_decimal)))
                
                # Get previous period average
                prev_start = start_date - timedelta(days=period_days)
                prev_prices = MarketPrice.objects.filter(
                    commodity=commodity,
                    region=region,
                    price_date__gte=prev_start,
                    price_date__lt=start_date
                ).aggregate(avg=Avg('price'))['avg']
                
                prev_avg = Decimal(str(prev_prices)) if prev_prices else avg_price
                
                # Calculate change
                price_change = avg_price - prev_avg
                percent_change = (price_change / prev_avg * 100) if prev_avg > 0 else Decimal('0')
                
                # Determine trend
                if percent_change > 5:
                    trend = 'up'
                elif percent_change < -5:
                    trend = 'down'
                else:
                    trend = 'stable'
                
                # Volatility (coefficient of variation)
                if avg_price > 0:
                    std_dev = region_data['stddev'] or Decimal('0')
                    volatility = (std_dev / avg_price * 100) if avg_price > 0 else Decimal('0')
                else:
                    volatility = 0
                
                # Create or update trend record
                period_label = 'month' if period_days >= 25 else 'week'
                
                PriceTrend.objects.update_or_create(
                    commodity=commodity,
                    region=region,
                    period=period_label,
                    period_start=start_date,
                    defaults={
                        'period_end': end_date,
                        'avg_price': avg_price,
                        'min_price': min_price,
                        'max_price': max_price,
                        'price_change': price_change,
                        'percent_change': percent_change,
                        'trend_direction': trend,
                        'volatility_score': float(volatility),
                    }
                )
            
            logger.info(f"Calculated trends for {commodity.name}")
            return True
        
        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            return False
    
    @staticmethod
    def get_best_selling_time(commodity_id):
        """Analyze historical data to recommend best selling time"""
        from core.models_market import MarketPrice, Commodity
        from django.db.models import Avg
        from django.db.models.functions import ExtractMonth
        
        try:
            commodity = Commodity.objects.get(id=commodity_id)
            
            # Group prices by month and calculate average
            monthly_avg = MarketPrice.objects.filter(
                commodity=commodity
            ).annotate(
                month=ExtractMonth('price_date')
            ).values('month').annotate(
                avg_price=Avg('price')
            ).order_by('-avg_price')
            
            if monthly_avg.exists():
                best_month_data = monthly_avg.first()
                month_names = {
                    1: 'January', 2: 'February', 3: 'March', 4: 'April',
                    5: 'May', 6: 'June', 7: 'July', 8: 'August',
                    9: 'September', 10: 'October', 11: 'November', 12: 'December'
                }
                
                return {
                    'best_month': month_names.get(best_month_data['month'], 'N/A'),
                    'best_price': float(best_month_data['avg_price']),
                    'current_vs_best': 'Below best' if True else 'Above best',
                }
            
            return None
        
        except Exception as e:
            logger.error(f"Error calculating best selling time: {str(e)}")
            return None
    
    @staticmethod
    def check_price_alerts(commodity_id, current_price):
        """Check if any alerts should be triggered"""
        from core.models_market import PriceAlert
        from core.notifications.email_notifier import send_price_alert_email
        
        try:
            # Find active threshold alerts for this commodity
            alerts = PriceAlert.objects.filter(
                commodity_id=commodity_id,
                is_active=True,
                is_triggered=False,
                alert_type__in=['threshold_high', 'threshold_low']
            )
            
            triggered_alerts = []
            
            for alert in alerts:
                should_trigger = False
                
                if alert.alert_type == 'threshold_high' and current_price >= alert.threshold_price:
                    should_trigger = True
                elif alert.alert_type == 'threshold_low' and current_price <= alert.threshold_price:
                    should_trigger = True
                
                if should_trigger:
                    alert.is_triggered = True
                    alert.triggered_at = timezone.now()
                    alert.save()
                    triggered_alerts.append(alert)
                    
                    # Send notification
                    if alert.notify_email:
                        send_price_alert_email(alert, current_price)
            
            return len(triggered_alerts)
        
        except Exception as e:
            logger.error(f"Error checking price alerts: {str(e)}")
            return 0
    
    @staticmethod
    def get_market_recommendations(user_id):
        """Get market recommendations for a user based on their crops"""
        from core.models_market import MarketAnalytics, PriceTrend, Commodity
        from core.models import Farm
        
        try:
            # Get user's crops from CropSeason instead
            from core.models import CropSeason
            user_crops = CropSeason.objects.filter(
                field__farm__owner_id=user_id
            ).values_list('crop_type__name', flat=True).distinct()
            
            recommendations = []
            
            for crop_name in user_crops:
                # Find matching commodity
                from core.models_market import Commodity
                commodity = Commodity.objects.filter(
                    name__icontains=crop_name
                ).first()
                
                if not commodity:
                    continue
                
                # Get current price trend
                trend = PriceTrend.objects.filter(
                    commodity=commodity
                ).order_by('-period_start').first()
                
                if trend:
                    action = 'SELL NOW' if trend.trend_direction == 'up' else 'HOLD'
                    confidence = f"{trend.volatility_score:.0f}%"
                    
                    recommendations.append({
                        'crop': crop_name,
                        'action': action,
                        'current_price': float(trend.avg_price),
                        'price_change': f"{float(trend.percent_change):.1f}%",
                        'confidence': confidence,
                        'reason': f"Market trending {trend.trend_direction}",
                    })
            
            # If no local recommendations, use AI for Zimbabwe market analysis
            if not recommendations and user_crops:
                try:
                    from core.services.chatbot_service import ChatbotService
                    crop_list = ', '.join(user_crops[:3])  # Limit to top 3 crops
                    ai_response = ChatbotService.get_response(
                        user_id=user_id,
                        message=f"What are the current market trends and prices for {crop_list} in Zimbabwe? Should I sell now or wait?",
                        context={'source': 'market_analysis', 'location': 'Zimbabwe'}
                    )
                    
                    if ai_response.get('response'):
                        recommendations.append({
                            'crop': 'Market Analysis',
                            'action': 'AI Analysis',
                            'confidence': '85%',
                            'ai_response': ai_response['response']
                        })
                except Exception as e:
                    logger.error(f"AI market analysis error: {e}")
            
            return recommendations
        
        except Exception as e:
            logger.error(f"Error getting market recommendations: {str(e)}")
            return []
    
    @staticmethod
    def cache_key(key_type, identifier):
        """Generate cache keys for market data"""
        return f"market_{key_type}_{identifier}"
