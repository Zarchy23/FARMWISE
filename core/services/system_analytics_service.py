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

    # CropSeason statuses considered "active" (no single 'active' status exists)
    ACTIVE_CROP_STATUSES = ['planting', 'planted', 'growing', 'ready_for_harvest']

    @staticmethod
    def get_farm_overview(user, farm_id=None):
        """Get complete farm overview with all key metrics"""
        from core.models import Farm, CropSeason, Field, Animal, Equipment

        try:
            farms = Farm.objects.filter(owner=user)
            if farm_id:
                farms = farms.filter(id=farm_id)

            active_statuses = SystemAnalyticsService.ACTIVE_CROP_STATUSES
            overview = {
                'total_farms': farms.count(),
                'total_fields': Field.objects.filter(farm__in=farms).count(),
                'active_crops': CropSeason.objects.filter(field__farm__in=farms, status__in=active_statuses).count(),
                'total_livestock': Animal.objects.filter(farm__in=farms).count(),
                'total_equipment': Equipment.objects.filter(owner=user).count(),
                'farms': []
            }

            # Per-farm metrics
            for farm in farms:
                farm_data = {
                    'id': farm.id,
                    'name': farm.name,
                    'location': f"{farm.latitude}, {farm.longitude}" if farm.latitude else 'Not set',
                    'fields': Field.objects.filter(farm=farm).count(),
                    'active_crops': CropSeason.objects.filter(field__farm=farm, status__in=active_statuses).count(),
                    'livestock': Animal.objects.filter(farm=farm).count(),
                    'total_area_hectares': float(farm.total_area_hectares or 0),
                }
                overview['farms'].append(farm_data)

            return overview
        except Exception as e:
            logger.error(f"Error generating farm overview: {e}")
            return {}
    
    @staticmethod
    def get_crop_analytics(user, farm_id=None, days=30):
        """Get comprehensive crop analytics"""
        from core.models import CropSeason, InputApplication, Harvest

        try:
            queryset = CropSeason.objects.filter(field__farm__owner=user)
            if farm_id:
                queryset = queryset.filter(field__farm_id=farm_id)

            crops = queryset.select_related('field__farm', 'crop_type')
            active_statuses = SystemAnalyticsService.ACTIVE_CROP_STATUSES

            analytics = {
                'total_crops': crops.count(),
                'active_crops': crops.filter(status__in=active_statuses).count(),
                'harvested_crops': crops.filter(status='harvested').count(),
                'planned_crops': crops.filter(status='planned').count(),
                'crops': []
            }

            for crop in crops:
                inputs_total = InputApplication.objects.filter(crop_season=crop).aggregate(
                    total=Coalesce(Sum(F('quantity') * F('cost_per_unit')), 0, output_field=DecimalField())
                )['total'] or 0

                crop_data = {
                    'id': crop.id,
                    'name': crop.crop_type.name if crop.crop_type else 'Unknown',
                    'variety': crop.variety,
                    'field': crop.field.name,
                    'farm': crop.field.farm.name,
                    'status': crop.status,
                    'planted_date': crop.planting_date.strftime('%Y-%m-%d') if crop.planting_date else None,
                    'expected_harvest': crop.expected_harvest_date.strftime('%Y-%m-%d') if crop.expected_harvest_date else None,
                    'area_hectares': float(crop.field.area_hectares or 0),
                    'total_inputs': float(inputs_total),
                    'harvest_yield': None
                }

                harvest = Harvest.objects.filter(crop_season=crop).first()
                if harvest:
                    crop_data['harvest_yield'] = float(harvest.quantity_kg) if harvest.quantity_kg else 0
                    crop_data['harvest_date'] = harvest.harvest_date.strftime('%Y-%m-%d') if harvest.harvest_date else None

                analytics['crops'].append(crop_data)

            return analytics
        except Exception as e:
            logger.error(f"Error generating crop analytics: {e}")
            return {}
    
    @staticmethod
    def get_livestock_analytics(user, farm_id=None, days=30):
        """Get comprehensive livestock analytics"""
        from core.models import Animal, HealthRecord, BreedingRecord

        try:
            start_date = (timezone.now() - timedelta(days=days)).date()
            today = timezone.now().date()

            queryset = Animal.objects.filter(farm__owner=user)
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

            for animal in livestock:
                animal_type = animal.animal_type.breed if animal.animal_type else 'Unknown'
                analytics['by_type'][animal_type] = analytics['by_type'].get(animal_type, 0) + 1

                # Derive health status from the latest health record's next due date
                latest_health = HealthRecord.objects.filter(animal=animal).order_by('-record_date').first()
                if not latest_health:
                    status = 'Unknown'
                elif latest_health.next_due_date and latest_health.next_due_date < today:
                    status = 'Needs Attention'
                else:
                    status = 'Healthy'
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
        from core.models import InputApplication, Order, EquipmentBooking, Payroll

        try:
            start_dt = timezone.now() - timedelta(days=days)
            start_date = start_dt.date()

            # Crop inputs (expenses)
            crop_inputs = InputApplication.objects.filter(
                crop_season__field__farm__owner=user,
                application_date__gte=start_date
            )
            if farm_id:
                crop_inputs = crop_inputs.filter(crop_season__field__farm_id=farm_id)
            total_expenses = crop_inputs.aggregate(
                total=Coalesce(Sum(F('quantity') * F('cost_per_unit')), 0, output_field=DecimalField())
            )['total'] or 0

            # Marketplace sales (revenue) - listing.seller is a Farm owned by the user
            orders = Order.objects.filter(
                listing__seller__owner=user,
                created_at__gte=start_dt,
                status='completed'
            ).select_related('listing')
            if farm_id:
                orders = orders.filter(listing__seller_id=farm_id)
            total_revenue = orders.aggregate(
                total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField())
            )['total'] or 0

            # Equipment bookings
            bookings = EquipmentBooking.objects.filter(
                equipment__owner=user,
                start_date__gte=start_date,
                status='completed'
            )
            equipment_revenue = bookings.aggregate(
                total=Coalesce(Sum('total_cost'), 0, output_field=DecimalField())
            )['total'] or 0

            # Payroll expenses
            payroll = Payroll.objects.filter(
                worker__farm__owner=user,
                period_end__gte=start_date
            )
            if farm_id:
                payroll = payroll.filter(worker__farm_id=farm_id)
            payroll_expenses = payroll.aggregate(
                total=Coalesce(Sum('total_pay'), 0, output_field=DecimalField())
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
                    'amount': float(order.total_amount or 0),
                    'date': order.created_at.strftime('%Y-%m-%d')
                })

            return analytics
        except Exception as e:
            logger.error(f"Error generating financial analytics: {e}")
            return {}
    
    @staticmethod
    def get_equipment_analytics(user, farm_id=None, days=30):
        """Get comprehensive equipment analytics"""
        from core.models import Equipment, EquipmentBooking

        try:
            start_date = (timezone.now() - timedelta(days=days)).date()

            equipment = Equipment.objects.filter(owner=user)

            analytics = {
                'total_equipment': equipment.count(),
                'available': equipment.filter(status='available').count(),
                'rented_out': equipment.filter(status='rented').count(),
                'maintenance_due': equipment.filter(status='maintenance').count(),
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
                    'type': equip.get_category_display(),
                    'status': equip.status,
                    'hourly_rate': float(equip.hourly_rate) if equip.hourly_rate else 0,
                    'daily_rate': float(equip.daily_rate) if equip.daily_rate else 0,
                    'total_bookings': EquipmentBooking.objects.filter(equipment=equip).count(),
                }
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
            ).select_related('farm', 'crop__crop_type')
            if farm_id:
                reports = reports.filter(farm_id=farm_id)

            analytics = {
                'total_reports': reports.count(),
                'by_severity': {},
                'by_pest_type': {},
                'ai_detected': reports.count(),
                'manual_detected': 0,
                'verified': reports.filter(agronomist_verified=True).count(),
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
                    'crop': report.crop.crop_type.name if report.crop and report.crop.crop_type else 'N/A',
                    'diagnosis': report.ai_diagnosis,
                    'severity': report.severity,
                    'detected_by': 'AI',
                    'is_verified': report.agronomist_verified,
                    'created_at': report.created_at.strftime('%Y-%m-%d')
                }
                analytics['reports'].append(report_data)
            
            return analytics
        except Exception as e:
            logger.error(f"Error generating pest detection analytics: {e}")
            return {}
    
    @staticmethod
    def get_financial_trends(user, farm_id=None, days=30):
        """Daily revenue vs expenses time-series for trend charts."""
        from core.models import InputApplication, Order
        from django.db.models.functions import TruncDate

        try:
            start_date = (timezone.now() - timedelta(days=days)).date()

            # Daily revenue from completed marketplace orders
            orders = Order.objects.filter(
                listing__seller__owner=user,
                created_at__date__gte=start_date,
                status='completed',
            )
            if farm_id:
                orders = orders.filter(listing__seller_id=farm_id)
            revenue_qs = (
                orders.annotate(day=TruncDate('created_at'))
                .values('day')
                .annotate(total=Coalesce(Sum('total_amount'), 0, output_field=DecimalField()))
            )
            revenue_by_day = {r['day']: float(r['total'] or 0) for r in revenue_qs}

            # Daily expenses from crop inputs (application_date is a DateField)
            inputs = InputApplication.objects.filter(
                crop_season__field__farm__owner=user,
                application_date__gte=start_date,
            )
            if farm_id:
                inputs = inputs.filter(crop_season__field__farm_id=farm_id)
            expense_qs = (
                inputs.annotate(day=TruncDate('application_date'))
                .values('day')
                .annotate(total=Coalesce(Sum(F('quantity') * F('cost_per_unit')), 0, output_field=DecimalField()))
            )
            expense_by_day = {e['day']: float(e['total'] or 0) for e in expense_qs}

            # Build a continuous date axis
            labels, revenue, expenses = [], [], []
            today = timezone.now().date()
            for offset in range(days + 1):
                d = start_date + timedelta(days=offset)
                if d > today:
                    break
                labels.append(d.strftime('%b %d'))
                revenue.append(revenue_by_day.get(d, 0))
                expenses.append(expense_by_day.get(d, 0))

            return {'labels': labels, 'revenue': revenue, 'expenses': expenses}
        except Exception as e:
            logger.error(f"Error generating financial trends: {e}")
            return {'labels': [], 'revenue': [], 'expenses': []}

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
            'trends': SystemAnalyticsService.get_financial_trends(user, farm_id, days),
            'generated_at': timezone.now().isoformat()
        }
