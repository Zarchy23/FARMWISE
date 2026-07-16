# core/api/views_market.py
# Market Price API Views

from rest_framework import viewsets, status, views
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta
import logging

from core.models_market import (
    Commodity, MarketPrice, PriceTrend, PriceAlert,
    SellerListing, BuyerInquiry, MarketAnalytics
)
from core.api.serializers_market import (
    CommoditySerializer, MarketPriceSerializer, PriceTrendSerializer,
    PriceAlertSerializer, SellerListingSerializer, BuyerInquirySerializer,
    MarketAnalyticsSerializer
)
from core.services.market_price_service import MarketPriceService

logger = logging.getLogger(__name__)


class CommodityViewSet(viewsets.ReadOnlyModelViewSet):
    """View commodity catalog"""
    queryset = Commodity.objects.all()
    serializer_class = CommoditySerializer
    permission_classes = [IsAuthenticated]


class MarketPriceViewSet(viewsets.ReadOnlyModelViewSet):
    """View current market prices"""
    queryset = MarketPrice.objects.all().order_by('-recorded_at')
    serializer_class = MarketPriceSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['commodity', 'region', 'source']
    search_fields = ['commodity__name', 'region']
    
    @action(detail=False, methods=['get'])
    def by_commodity(self, request):
        """Get prices for a specific commodity"""
        commodity_id = request.query_params.get('commodity_id')
        region = request.query_params.get('region', 'Kenya')
        
        prices = MarketPrice.objects.filter(
            commodity_id=commodity_id,
            region=region
        ).order_by('-price_date')[:100]
        
        serializer = self.get_serializer(prices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest prices for all commodities"""
        latest_prices = MarketPrice.objects.filter(
            price_date=timezone.now().date()
        ).select_related('commodity')
        
        serializer = self.get_serializer(latest_prices, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def refresh(self, request):
        """Refresh prices from external APIs"""
        commodity_id = request.data.get('commodity_id')
        
        try:
            # Fetch new prices
            commodity = Commodity.objects.get(id=commodity_id)
            prices = MarketPriceService.fetch_prices_from_api(commodity.name)
            
            # Store prices
            stored = MarketPriceService.store_market_prices(commodity_id, prices)
            
            return Response({
                'status': 'success',
                'prices_stored': stored,
                'message': f'Stored {stored} new price records'
            })
        except Exception as e:
            logger.error(f"Error refreshing prices: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PriceTrendViewSet(viewsets.ReadOnlyModelViewSet):
    """View price trends and analytics"""
    queryset = PriceTrend.objects.all()
    serializer_class = PriceTrendSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['commodity', 'region', 'period']
    
    @action(detail=False, methods=['get'])
    def current_trends(self, request):
        """Get current price trends for all commodities"""
        end_date = timezone.now().date()
        trends = PriceTrend.objects.filter(
            period_end=end_date
        ).order_by('-period_start')
        
        serializer = self.get_serializer(trends, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate price trends for a commodity"""
        commodity_id = request.data.get('commodity_id')
        period_days = request.data.get('period_days', 30)
        
        success = MarketPriceService.calculate_price_trends(commodity_id, period_days)
        
        if success:
            trends = PriceTrend.objects.filter(commodity_id=commodity_id)
            serializer = self.get_serializer(trends, many=True)
            return Response({
                'status': 'success',
                'trends': serializer.data
            })
        else:
            return Response(
                {'error': 'Failed to calculate trends'},
                status=status.HTTP_400_BAD_REQUEST
            )


class PriceAlertViewSet(viewsets.ModelViewSet):
    """Manage price alerts"""
    serializer_class = PriceAlertSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter alerts for current user"""
        return PriceAlert.objects.filter(farmer=self.request.user)
    
    def perform_create(self, serializer):
        """Create alert for current user"""
        serializer.save(farmer=self.request.user)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active alerts"""
        alerts = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def triggered(self, request):
        """Get triggered alerts"""
        alerts = self.get_queryset().filter(is_triggered=True)
        serializer = self.get_serializer(alerts, many=True)
        return Response(serializer.data)


class SellerListingViewSet(viewsets.ModelViewSet):
    """Manage seller product listings"""
    serializer_class = SellerListingSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['commodity', 'status', 'quality_grade']
    search_fields = ['title', 'description', 'commodity__name']
    
    def get_queryset(self):
        """Get public listings or user's own listings"""
        if self.request.user.is_staff or self.request.user.is_superuser:
            return SellerListing.objects.all()
        
        # Public listings for browsing
        public = SellerListing.objects.filter(
            is_public=True,
            status='available',
            expires_at__gt=timezone.now()
        )
        
        # User's own listings
        own = SellerListing.objects.filter(seller=self.request.user)
        
        from django.db.models import Q
        return public | own
    
    def perform_create(self, serializer):
        """Create listing for current user"""
        serializer.save(seller=self.request.user)
    
    @action(detail=True, methods=['post'])
    def increment_views(self, request, pk=None):
        """Increment view count"""
        listing = self.get_object()
        listing.views += 1
        listing.save(update_fields=['views'])
        
        return Response({
            'status': 'success',
            'views': listing.views
        })
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like/unlike a listing"""
        listing = self.get_object()
        
        if listing.likes.filter(id=request.user.id).exists():
            listing.likes.remove(request.user)
            liked = False
        else:
            listing.likes.add(request.user)
            liked = True
        
        return Response({
            'status': 'success',
            'liked': liked,
            'likes': listing.likes.count()
        })
    
    @action(detail=False, methods=['get'])
    def my_listings(self, request):
        """Get current user's listings"""
        listings = SellerListing.objects.filter(seller=request.user)
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured/popular listings"""
        listings = SellerListing.objects.filter(
            is_public=True,
            status='available'
        ).order_by('-views', '-likes')[:50]
        
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)


class BuyerInquiryViewSet(viewsets.ModelViewSet):
    """Manage buyer inquiries"""
    serializer_class = BuyerInquirySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter inquiries for current user (as buyer or seller)"""
        from django.db.models import Q
        
        user_inquiries = BuyerInquiry.objects.filter(buyer=self.request.user)
        seller_inquiries = BuyerInquiry.objects.filter(
            listing__seller=self.request.user
        )
        
        return user_inquiries | seller_inquiries
    
    def perform_create(self, serializer):
        """Create inquiry for current user"""
        serializer.save(buyer=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_inquiries(self, request):
        """Get inquiries I made"""
        inquiries = BuyerInquiry.objects.filter(buyer=request.user)
        serializer = self.get_serializer(inquiries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def received_inquiries(self, request):
        """Get inquiries for my listings"""
        inquiries = BuyerInquiry.objects.filter(
            listing__seller=request.user
        )
        serializer = self.get_serializer(inquiries, many=True)
        return Response(serializer.data)


class MarketAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """View market analytics and recommendations"""
    queryset = MarketAnalytics.objects.all()
    serializer_class = MarketAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_recommendations(self, request):
        """Get personalized market recommendations"""
        recommendations = MarketPriceService.get_market_recommendations(
            request.user.id
        )
        return Response({
            'recommendations': recommendations,
            'timestamp': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['get'])
    def trending_commodities(self, request):
        """Get trending commodities"""
        analytics = MarketAnalytics.objects.filter(
            recommendation__in=['buy_now', 'sell_now']
        ).order_by('-confidence_score')[:10]
        
        serializer = self.get_serializer(analytics, many=True)
        return Response(serializer.data)


class MarketDashboardView(views.APIView):
    """Dashboard view for market overview"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get market dashboard data"""
        try:
            # Get user's crops and market recommendations
            recommendations = MarketPriceService.get_market_recommendations(
                request.user.id
            )
            
            # Get latest price trends
            trends = PriceTrend.objects.filter(
                period_end=timezone.now().date()
            ).order_by('-percent_change')[:5]
            
            trend_serializer = PriceTrendSerializer(trends, many=True)
            
            # Get active listings count
            active_listings = SellerListing.objects.filter(
                status='available',
                expires_at__gt=timezone.now()
            ).count()
            
            # Get user's active alerts
            active_alerts = PriceAlert.objects.filter(
                farmer=request.user,
                is_active=True
            ).count()
            
            return Response({
                'recommendations': recommendations,
                'top_trends': trend_serializer.data,
                'active_listings': active_listings,
                'active_alerts': active_alerts,
                'timestamp': timezone.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error loading market dashboard: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
