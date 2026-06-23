# core/services/system_analytics_service.py
# Comprehensive System-Wide Analytics Service
# Aggregates data from all modules for complete farm analytics

from django.db.models import Sum, Avg, Count, Max, Min, F, Q, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import logging
from django.contrib.auth import get_user_model

User = get_user_model()
logger = logging.getLogger(__name__)


class SystemAnalyticsService:
    """Service for generating comprehensive system-wide analytics"""
    
    @staticmethod
    def get_farm_overview(user, farm_id=None):
        """Get complete farm overview with all key metrics"""
        from core.models import Farm, CropSeason, Field, Livestock, Equipment
        
        try:
            # Get farms
            if farm_id:
                farms = Farm.objects.filter(id=farm_id, owner=user)
            else:
                farms = Farm.objects.filter(owner=user)
            
            overview = {
                'total_farms': farms.count(),
                'total_fields': Field.objects.filter(farm__in=farms).count(),
                'active_crops': CropSeason.objects.filter(field__farm__in=farms, status='active').count(),
                'total_livestock': Livestock.objects.filter(farm__in=farms).count(),
                'total_equipment': Equipment.objects.filter(owner=user).count(),
                'farms': []
            }
            
            # Per-farm metrics
            for farm in farms:
                farm_data = {
                    'id': farm.id,
                    'name': farm.name,
                    'location': f"{farm.location_latitude}, {farm.location_longitude}" if farm.location_latitude else 'Not set',
                    'fields': Field.objects.filter(farm=farm).count(),
                    'active_crops': CropSeason.objects.filter(field__farm=farm, status='active').count(),
                    'livestock': Livestock.objects.filter(farm=farm).count(),
                    'total_area_hectares': Field.objects.filter(farm=farm).aggregate(
                        total=Coalesce(Sum('area_hectares'), 0)
                    )['total'] or 0
                }
                overview['farms'].append(farm_data)
            
            return overview
        except Exception as e:
            logger.error(f"Error generating farm overview: {e}")
            return {}
    
    @staticmethod
    def get_crop_analytics(user, farm_id=None, days=30):
        """Get comprehensive crop analytics"""
        from core.models import CropSeason, CropInput, Harvest
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            queryset = CropSeason.objects.filter(field__farm__owner=user)
            if farm_id:
                queryset = queryset.filter(field__farm_id=farm_id)
            
            crops = queryset.select_related('field__farm', 'crop_type')
            
            analytics = {
                'total_crops': crops.count(),
                'active_crops': crops.filter(status='active').count(),
                'harvested_crops': crops.filter(status='harvested').count(),
                'planned_crops': crops.filter(status='planned').count(),
                'crops': []
            }
            
            for crop in crops:
                crop_data = {
                    'id': crop.id,
                    'name': crop.crop_type.name if crop.crop_type else 'Unknown',
                    'variety': crop.variety,
                    'field': crop.field.name,
                    'farm': crop.field.farm.name,
                    'status': crop.status,
                    'planted_date': crop.planted_date.strftime('%Y-%m-%d') if crop.planted_date else None,
                    'expected_harvest': crop.expected_harvest_date.strftime('%Y-%m-%d') if crop.expected_harvest_date else None,
                    'area_hectares': crop.field.area_hectares,
                    'total_inputs': CropInput.objects.filter(crop_season=crop).aggregate(
                        total_cost=Coalesce(Sum('total_cost'), 0)
                    )['total_cost'] or 0,
                    'harvest_yield': None
                }
                
                # Get harvest data if available
                harvest = Harvest.objects.filter(crop_season=crop).first()
                if harvest:
                    crop_data['harvest_yield'] = float(harvest.actual_yield_kg) if harvest.actual_yield_kg else 0
                    crop_data['harvest_date'] = harvest.harvest_date.strftime('%Y-%m-%d') if harvest.harvest_date else None
                
                analytics['crops'].append(crop_data)
            
            return analytics
        except Exception as e:
            logger.error(f"Error generating crop analytics: {e}")
            return {}
    
    @staticmethod
    def get_livestock_analytics(user, farm_id=None, days=30):
        """Get comprehensive livestock analytics"""
        from core.models import Livestock, HealthRecord, BreedingRecord
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            queryset = Livestock.objects.filter(farm__owner=user)
            if farm_id:
                queryset = queryset.filter(farm_id=farm_id)
            
            livestock = queryset.select_related('farm', 'animal_type')
            
            analytics = {
                'total_animals': livestock.count(),
                'by_type': {},
                'health_status': {},
                'recent_health_records': HealthRecord.objects.filter(
                    animal__farm__owner=user,
                    next_due_date__gte=start_date
                ).count(),
                'upcoming_breedings': BreedingRecord.objects.filter(
                    animal__farm__owner=user,
                    expected_calving_date__gte=start_date
                ).count(),
                'livestock': []
            }
            
            # Group by animal type
            for animal in livestock:
                animal_type = animal.animal_type.breed if animal.animal_type else 'Unknown'
                analytics['by_type'][animal_type] = analytics['by_type'].get(animal_type, 0) + 1
                
                # Health status
                latest_health = HealthRecord.objects.filter(animal=animal).order_by('-check_date').first()
                status = 'Unknown'
                if latest_health:
                    if latest_health.status == 'completed':
                        status = 'Healthy'
                    elif latest_health.status == 'overdue':
                        status = 'Needs Attention'
                    else:
                        status = 'Pending'
                analytics['health_status'][status] = analytics['health_status'].get(status, 0) + 1
                
                animal_data = {
                    'id': animal.id,
                    'tag_number': animal.tag_number,
                    'name': animal.name,
                    'type': animal_type,
                    'farm': animal.farm.name,
                    'gender': animal.gender,
                    'birth_date': animal.birth_date.strftime('%Y-%m-%d') if animal.birth_date else None,
                    'status': status
                }
                analytics['livestock'].append(animal_data)
            
            return analytics
        except Exception as e:
            logger.error(f"Error generating livestock analytics: {e}")
            return {}
    
    @staticmethod
    def get_financial_analytics(user, farm_id=None, days=30):
        """Get comprehensive financial analytics"""
        from core.models import CropInput, MarketplaceListing, MarketplaceOrder, EquipmentBooking, Payroll
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            # Crop inputs (expenses)
            crop_inputs = CropInput.objects.filter(
                crop_season__field__farm__owner=user,
                application_date__gte=start_date
            )
            total_expenses = crop_inputs.aggregate(total=Coalesce(Sum('total_cost'), 0))['total'] or 0
            
            # Marketplace sales (revenue)
            orders = MarketplaceOrder.objects.filter(
                listing__seller=user,
                created_at__gte=start_date,
                status='completed'
            )
            total_revenue = orders.aggregate(
                total=Coalesce(Sum(F('quantity') * F('unit_price')), 0, output_field=DecimalField())
            )['total'] or 0
            
            # Equipment bookings
            bookings = EquipmentBooking.objects.filter(
                equipment__owner=user,
                start_date__gte=start_date,
                status='completed'
            )
            equipment_revenue = bookings.aggregate(
                total=Coalesce(Sum('total_cost'), 0)
            )['total'] or 0
            
            # Payroll expenses
            payroll = Payroll.objects.filter(
                worker__farm__owner=user,
                period_end__gte=start_date
            )
            payroll_expenses = payroll.aggregate(
                total=Coalesce(Sum('total_pay'), 0)
            )['total'] or 0
            
            analytics = {
                'period_days': days,
                'total_revenue': float(total_revenue + equipment_revenue),
                'total_expenses': float(total_expenses + payroll_expenses),
                'net_profit': float(total_revenue + equipment_revenue - total_expenses - payroll_expenses),
                'breakdown': {
                    'crop_inputs': float(total_expenses),
                    'marketplace_sales': float(total_revenue),
                    'equipment_rentals': float(equipment_revenue),
                    'payroll': float(payroll_expenses)
                },
                'sales_count': orders.count(),
                'bookings_count': bookings.count(),
                'transactions': []
            }
            
            # Recent transactions
            for order in orders[:10]:
                analytics['transactions'].append({
                    'type': 'Sale',
                    'description': f"Sold {order.quantity} {order.listing.unit} of {order.listing.product_name}",
                    'amount': float(order.quantity * order.unit_price),
                    'date': order.created_at.strftime('%Y-%m-%d')
                })
            
            return analytics
        except Exception as e:
            logger.error(f"Error generating financial analytics: {e}")
            return {}
    
    @staticmethod
    def get_equipment_analytics(user, farm_id=None, days=30):
        """Get comprehensive equipment analytics"""
        from core.models import Equipment, Maintenance, EquipmentBooking
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            equipment = Equipment.objects.filter(owner=user)
            
            analytics = {
                'total_equipment': equipment.count(),
                'available': equipment.filter(status='available').count(),
                'rented_out': equipment.filter(status='rented').count(),
                'maintenance_due': Maintenance.objects.filter(
                    equipment__owner=user,
                    scheduled_date__gte=start_date,
                    status__in=['pending', 'overdue']
                ).count(),
                'recent_bookings': EquipmentBooking.objects.filter(
                    equipment__owner=user,
                    start_date__gte=start_date
                ).count(),
                'equipment': []
            }
            
            for equip in equipment:
                equip_data = {
                    'id': equip.id,
                    'name': equip.name,
                    'type': equip.equipment_type,
                    'status': equip.status,
                    'hourly_rate': float(equip.hourly_rate) if equip.hourly_rate else 0,
                    'daily_rate': float(equip.daily_rate) if equip.daily_rate else 0,
                    'total_bookings': EquipmentBooking.objects.filter(equipment=equip).count(),
                    'last_maintenance': Maintenance.objects.filter(
                        equipment=equip
                    ).order_by('-scheduled_date').first()
                }
                if equip_data['last_maintenance']:
                    equip_data['last_maintenance_date'] = equip_data['last_maintenance'].scheduled_date.strftime('%Y-%m-%d')
                analytics['equipment'].append(equip_data)
            
            return analytics
        except Exception as e:
            logger.error(f"Error generating equipment analytics: {e}")
            return {}
    
    @staticmethod
    def get_pest_detection_analytics(user, farm_id=None, days=30):
        """Get pest detection analytics"""
        from core.models import PestReport
        
        try:
            start_date = timezone.now() - timedelta(days=days)
            
            reports = PestReport.objects.filter(
                farm__owner=user,
                created_at__gte=start_date
            )
            
            analytics = {
                'total_reports': reports.count(),
                'by_severity': {},
                'by_pest_type': {},
                'ai_detected': reports.filter(detected_by='ai').count(),
                'manual_detected': reports.filter(detected_by='manual').count(),
                'verified': reports.filter(is_verified=True).count(),
                'reports': []
            }
            
            for report in reports:
                # Severity breakdown
                severity = report.severity
                analytics['by_severity'][severity] = analytics['by_severity'].get(severity, 0) + 1
                
                # Pest type breakdown
                pest_type = report.ai_diagnosis if report.ai_diagnosis else 'Unknown'
                analytics['by_pest_type'][pest_type] = analytics['by_pest_type'].get(pest_type, 0) + 1
                
                report_data = {
                    'id': report.id,
                    'farm': report.farm.name,
                    'crop': report.crop.name if report.crop else 'N/A',
                    'diagnosis': report.ai_diagnosis,
                    'severity': report.severity,
                    'detected_by': report.detected_by,
                    'is_verified': report.is_verified,
                    'created_at': report.created_at.strftime('%Y-%m-%d')
                }
                analytics['reports'].append(report_data)
            
            return analytics
        except Exception as e:
            logger.error(f"Error generating pest detection analytics: {e}")
            return {}
    
    @staticmethod
    def get_complete_dashboard(user, farm_id=None, days=30):
        """Get complete dashboard with all analytics"""
        return {
            'overview': SystemAnalyticsService.get_farm_overview(user, farm_id),
            'crops': SystemAnalyticsService.get_crop_analytics(user, farm_id, days),
            'livestock': SystemAnalyticsService.get_livestock_analytics(user, farm_id, days),
            'financial': SystemAnalyticsService.get_financial_analytics(user, farm_id, days),
            'equipment': SystemAnalyticsService.get_equipment_analytics(user, farm_id, days),
            'pest_detection': SystemAnalyticsService.get_pest_detection_analytics(user, farm_id, days),
            'generated_at': timezone.now().isoformat()
        }
