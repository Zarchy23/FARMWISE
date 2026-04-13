# core/views.py
# FARMWISE - Complete Views for All Functionality
# ⚠️ PRODUCTION SAFETY: Rate limiting enabled to prevent Gemini API quota errors

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from django.http import JsonResponse
from django.urls import reverse
from django.core.paginator import Paginator
from datetime import timedelta
from decimal import Decimal
import json
import requests
import base64
import re
import openai
from PIL import Image
from io import BytesIO

from .models import *
from .forms import *
from .forms_projects import *
from .throttling import throttle_pest_detection
from .export_service import ExportService
from .services.crop_automation_service import CropAutomationService
from .services.livestock_automation_service import LivestockAutomationService
from .services.insurance_automation_service import InsuranceAutomationService
from .services.payroll_automation_service import PayrollAutomationService

# ============================================================
# HOME & DASHBOARD
# ============================================================

def home(request):
    """Landing page"""
    return render(request, 'home.html')


def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f'Welcome {user.username}! Please complete your profile.')
            return redirect('core:profile_edit')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def dashboard(request):
    """Main user dashboard - Role-based content"""
    
    # Regular user dashboard
    farms = Farm.objects.filter(owner=request.user)
    
    # Get counts based on user type
    if request.user.user_type in ['farmer', 'large_farmer']:
        active_crops = CropSeason.objects.filter(
            field__farm__owner=request.user,
            status__in=['planted', 'growing']
        ).count()
        
        total_animals = Animal.objects.filter(farm__owner=request.user, status='alive').count()
    else:
        active_crops = 0
        total_animals = 0
    
    # Monthly revenue
    monthly_revenue = Transaction.objects.filter(
        farm__owner=request.user,
        transaction_type='income',
        date__month=timezone.now().month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent activities
    recent_activities = []
    
    # Recent crops (only for farmers)
    if request.user.user_type in ['farmer', 'large_farmer']:
        recent_crops = CropSeason.objects.filter(
            field__farm__owner=request.user
        ).order_by('-planting_date')[:5]
        
        for crop in recent_crops:
            recent_activities.append({
                'message': f'Planted {crop.crop_type.name} in {crop.field.name}',
                'created_at': crop.created_at
            })
        
        # Recent harvests
        recent_harvests = Harvest.objects.filter(
            crop_season__field__farm__owner=request.user
        ).order_by('-harvest_date')[:3]
        
        for harvest in recent_harvests:
            recent_activities.append({
                'message': f'Harvested {harvest.quantity_kg}kg of {harvest.crop_season.crop_type.name}',
                'created_at': harvest.created_at
            })
    
    # Weather - fetch from real data
    weather = None
    if farms.exists():
        # Get weather from first farm (or implement farm selection)
        farm = farms.first()
        weather_data = WeatherData.objects.filter(farm=farm).first()
        if weather_data:
            weather = {
                'temp': weather_data.temperature,
                'feels_like': weather_data.feels_like,
                'condition': weather_data.condition,
                'description': weather_data.description,
                'humidity': weather_data.humidity,
                'wind_speed': weather_data.wind_speed,
                'location': weather_data.location,
                'last_updated': weather_data.last_updated,
                'forecast': weather_data.forecast_data.get('forecast', [])
            }
        else:
            weather = {
                'temp': 'N/A',
                'condition': 'No data',
                'description': 'Weather data not available. Please ensure farm coordinates are set.',
                'forecast': []
            }
    else:
        weather = {
            'temp': 'N/A',
            'condition': 'No farms',
            'description': 'Please create a farm first to see weather data.',
            'forecast': []
        }
    
    context = {
        'farms': farms,
        'active_crops': active_crops,
        'total_animals': total_animals,
        'monthly_revenue': monthly_revenue,
        'recent_activities': recent_activities[:10],
        'weather': weather,
        'user_type': request.user.get_user_type_display() if hasattr(request.user, 'get_user_type_display') else request.user.user_type,
    }
    return render(request, 'dashboard.html', context)





@login_required



@login_required
def profile(request):
    """User profile view"""
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
@login_required
def profile_edit(request):
    """Edit user profile"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('core:profile')
        else:
            # Log form errors for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Profile form errors: {form.errors}')
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def settings(request):
    """User settings page"""
    return render(request, 'settings.html')


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        # Validate old password
        if not request.user.check_password(old_password):
            messages.error(request, 'Current password is incorrect.')
            return redirect('core:settings')
        
        # Validate new passwords match
        if new_password1 != new_password2:
            messages.error(request, 'New passwords do not match.')
            return redirect('core:settings')
        
        # Validate password length
        if len(new_password1) < 8:
            messages.error(request, 'Password must be at least 8 characters long.')
            return redirect('core:settings')
        
        # Update password
        request.user.set_password(new_password1)
        request.user.save()
        
        messages.success(request, 'Password changed successfully!')
        return redirect('core:settings')
    
    return redirect('core:settings')


# ============================================================
# SYSTEM ADMIN WALLBOARD
# ============================================================

@login_required
def api_keys_debug(request):
    """DEBUG: Check if API keys are loaded (Admin only)"""
    if request.user.user_type != 'admin':
        return JsonResponse({'error': 'Admin only'}, status=403)
    
    from django.conf import settings
    
    return JsonResponse({
        'openai_api_key_loaded': bool(settings.OPENAI_API_KEY),
        'openai_api_key_preview': f"{settings.OPENAI_API_KEY[:20]}..." if settings.OPENAI_API_KEY else "NOT SET",
        'openweather_api_key_loaded': bool(settings.OPENWEATHER_API_KEY),
        'openweather_api_key_preview': f"{settings.OPENWEATHER_API_KEY[:20]}..." if settings.OPENWEATHER_API_KEY else "NOT SET",
        'weather_api_key_loaded': bool(settings.WEATHER_API_KEY),
        'weather_api_key_preview': f"{settings.WEATHER_API_KEY[:20]}..." if settings.WEATHER_API_KEY else "NOT SET",
        'debug_mode': settings.DEBUG,
    })


@login_required
def wallboard(request):
    """System admin wallboard with statistical data - Admin only"""
    
    # Check if user is system admin or superuser
    if request.user.user_type != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied. Only system administrators can view this page.')
        return redirect('core:dashboard')
    
    # Gather system-wide statistics
    
    # User statistics
    total_users = User.objects.count()
    user_types = User.objects.values('user_type').annotate(count=Count('user_type')).order_by('-count')
    active_users = User.objects.filter(last_active__gte=timezone.now() - timedelta(days=7)).count()
    new_users_this_month = User.objects.filter(created_at__month=timezone.now().month).count()
    
    # Farm statistics
    total_farms = Farm.objects.count()
    farms_by_type = Farm.objects.values('farm_type').annotate(count=Count('farm_type')).order_by('-count')
    
    # Crop statistics
    total_crops = CropSeason.objects.count()
    active_crops = CropSeason.objects.filter(status__in=['planted', 'growing']).count()
    completed_crops = CropSeason.objects.filter(status='harvested').count()
    crop_types = CropSeason.objects.values('crop_type__name').annotate(count=Count('id')).order_by('-count')[:10]
    total_harvest = Harvest.objects.aggregate(total=Sum('quantity_kg'))['total'] or 0
    
    # Livestock statistics
    total_animals = Animal.objects.count()
    alive_animals = Animal.objects.filter(status='alive').count()
    animal_types = Animal.objects.values('animal_type').annotate(count=Count('id')).order_by('-count')
    
    # Transaction statistics
    total_revenue = Transaction.objects.filter(transaction_type='income').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_expenses = Transaction.objects.filter(transaction_type='expense').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    this_month_revenue = Transaction.objects.filter(
        transaction_type='income',
        date__month=timezone.now().month,
        date__year=timezone.now().year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Payroll statistics
    total_workers = Worker.objects.count()
    pending_payroll = Payroll.objects.filter(status='pending').count()
    total_payroll_processed = Payroll.objects.filter(status='processed').aggregate(total=Sum('total_pay'))['total'] or Decimal('0.00')
    
    # Equipment statistics
    total_equipment = Equipment.objects.count()
    active_bookings = EquipmentBooking.objects.filter(status='approved').count()
    
    # Insurance statistics
    total_policies = InsurancePolicy.objects.count()
    active_policies = InsurancePolicy.objects.filter(status='active').count()
    total_claims = InsuranceClaim.objects.count()
    
    # Pest detection statistics
    total_pest_reports = PestReport.objects.count()
    pest_types = PestReport.objects.values('ai_diagnosis').annotate(count=Count('id')).order_by('-count')[:5]
    
    # Recent activities
    recent_activities = AuditLog.objects.select_related('user').order_by('-created_at')[:20]
    
    # System health
    verification_rate = (User.objects.filter(is_verified=True).count() / max(total_users, 1)) * 100 if total_users > 0 else 0
    email_verified_rate = (User.objects.filter(email_verified=True).count() / max(total_users, 1)) * 100 if total_users > 0 else 0
    
    # Top farms by activity
    top_farms = Farm.objects.annotate(
        crop_count=Count('fields__crops', distinct=True),
        animal_count=Count('animals', distinct=True),
        activity_count=Count('activities', distinct=True)
    ).order_by('-activity_count')[:10]
    
    context = {
        'total_users': total_users,
        'user_types': list(user_types),
        'active_users': active_users,
        'new_users_this_month': new_users_this_month,
        'total_farms': total_farms,
        'farms_by_type': list(farms_by_type),
        'total_crops': total_crops,
        'active_crops': active_crops,
        'completed_crops': completed_crops,
        'crop_types': list(crop_types),
        'total_harvest': total_harvest,
        'total_animals': total_animals,
        'alive_animals': alive_animals,
        'animal_types': list(animal_types),
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'this_month_revenue': this_month_revenue,
        'total_workers': total_workers,
        'pending_payroll': pending_payroll,
        'total_payroll_processed': total_payroll_processed,
        'total_equipment': total_equipment,
        'active_bookings': active_bookings,
        'total_policies': total_policies,
        'active_policies': active_policies,
        'total_claims': total_claims,
        'total_pest_reports': total_pest_reports,
        'pest_types': list(pest_types),
        'recent_activities': recent_activities,
        'verification_rate': verification_rate,
        'email_verified_rate': email_verified_rate,
        'top_farms': top_farms,
    }
    
    return render(request, 'admin/wallboard.html', context)


# ============================================================
# FARM MANAGEMENT
# ============================================================

@login_required
def farm_list(request):
    """List all farms for current user"""
    farms = Farm.objects.filter(owner=request.user)
    return render(request, 'farms/list.html', {'farms': farms})


@login_required
def farm_create(request):
    """Create a new farm"""
    if request.method == 'POST':
        form = FarmForm(request.POST)
        if form.is_valid():
            farm = form.save(commit=False)
            farm.owner = request.user
            farm.save()
            messages.success(request, f'Farm "{farm.name}" created successfully!')
            return redirect('core:farm_detail', pk=farm.pk)
    else:
        form = FarmForm()
    return render(request, 'farms/create.html', {'form': form})


@login_required
def farm_detail(request, pk):
    """Farm details view"""
    farm = get_object_or_404(Farm, pk=pk, owner=request.user)
    fields = Field.objects.filter(farm=farm)
    active_crops = CropSeason.objects.filter(
        field__farm=farm,
        status__in=['planted', 'growing']
    )
    return render(request, 'farms/detail.html', {
        'farm': farm,
        'fields': fields,
        'active_crops': active_crops
    })


@login_required
def farm_edit(request, pk):
    """Edit farm details"""
    farm = get_object_or_404(Farm, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = FarmForm(request.POST, instance=farm)
        if form.is_valid():
            form.save()
            messages.success(request, 'Farm updated successfully!')
            return redirect('core:farm_detail', pk=farm.pk)
    else:
        form = FarmForm(instance=farm)
    return render(request, 'farms/edit.html', {'form': form, 'farm': farm})


@login_required
def farm_delete(request, pk):
    """Delete a farm"""
    farm = get_object_or_404(Farm, pk=pk, owner=request.user)
    if request.method == 'POST':
        farm_name = farm.name
        farm.delete()
        messages.success(request, f'Farm "{farm_name}" deleted successfully!')
        return redirect('core:farm_list')
    return render(request, 'farms/delete.html', {'farm': farm})


@login_required
def field_create(request, farm_id):
    """Add a field to a farm"""
    farm = get_object_or_404(Farm, pk=farm_id, owner=request.user)
    if request.method == 'POST':
        form = FieldForm(request.POST)
        if form.is_valid():
            field = form.save(commit=False)
            field.farm = farm
            field.save()
            messages.success(request, f'Field "{field.name}" added successfully!')
            return redirect('core:farm_detail', pk=farm.pk)
    else:
        form = FieldForm()
    return render(request, 'farms/fields.html', {'form': form, 'farm': farm})


@login_required
def field_edit(request, pk):
    """Edit field details"""
    field = get_object_or_404(Field, pk=pk, farm__owner=request.user)
    if request.method == 'POST':
        form = FieldForm(request.POST, instance=field)
        if form.is_valid():
            form.save()
            messages.success(request, 'Field updated successfully!')
            return redirect('core:farm_detail', pk=field.farm.pk)
    else:
        form = FieldForm(instance=field)
    return render(request, 'farms/fields.html', {'form': form, 'field': field})


@login_required
def field_delete(request, pk):
    """Delete a field"""
    field = get_object_or_404(Field, pk=pk, farm__owner=request.user)
    farm_pk = field.farm.pk
    if request.method == 'POST':
        field.delete()
        messages.success(request, 'Field deleted successfully!')
        return redirect('core:farm_detail', pk=farm_pk)
    return render(request, 'farms/delete.html', {'object': field, 'type': 'Field'})


# ============================================================
# CROP MANAGEMENT
# ============================================================

@login_required
def crop_list(request):
    """List all crops"""
    from .services.crop_automation_service import CropAutomationService
    
    # Run automation checks (status updates + reminders)
    try:
        CropAutomationService.run_automation_checks(user=request.user)
    except Exception as e:
        import logging
        logging.error(f"Error running crop automation: {str(e)}")
    
    crops = CropSeason.objects.filter(field__farm__owner=request.user)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        crops = crops.filter(status=status_filter)
    
    paginator = Paginator(crops, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'crops/list.html', {
        'crops': page_obj,
        'export_url': reverse('core:export_crops'),
    })


@login_required
def crop_plant(request):
    """Plant a new crop"""
    if request.method == 'POST':
        form = CropSeasonForm(request.POST, request.FILES)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.created_by = request.user
            crop.save()
            
            # Create notification
            Notification.objects.create(
                user=request.user,
                notification_type='success',
                title=f'{crop.crop_type.name} Planted',
                message=f'You have successfully planted {crop.crop_type.name} in {crop.field.name}.',
                link=f'/crops/{crop.id}/'
            )
            
            messages.success(request, f'{crop.crop_type.name} planted successfully!')
            return redirect('core:crop_detail', pk=crop.pk)
    else:
        form = CropSeasonForm()
        form.fields['field'].queryset = Field.objects.filter(farm__owner=request.user)
    
    return render(request, 'crops/create.html', {'form': form})


@login_required
def crop_detail(request, pk):
    """Crop details view"""
    from .services.crop_automation_service import CropAutomationService
    
    # Run automation checks when viewing a specific crop
    try:
        CropAutomationService.run_automation_checks(user=request.user)
    except Exception as e:
        import logging
        logging.error(f"Error running crop automation: {str(e)}")
    
    crop = get_object_or_404(CropSeason, pk=pk, field__farm__owner=request.user)
    inputs = InputApplication.objects.filter(crop_season=crop)
    harvests = Harvest.objects.filter(crop_season=crop)
    
    return render(request, 'crops/detail.html', {
        'crop': crop,
        'inputs': inputs,
        'harvests': harvests
    })


@login_required
def crop_edit(request, pk):
    """Edit crop details"""
    crop = get_object_or_404(CropSeason, pk=pk, field__farm__owner=request.user)
    if request.method == 'POST':
        form = CropSeasonForm(request.POST, request.FILES, instance=crop)
        if form.is_valid():
            form.save()
            messages.success(request, 'Crop updated successfully!')
            return redirect('core:crop_detail', pk=crop.pk)
    else:
        form = CropSeasonForm(instance=crop)
    return render(request, 'crops/edit.html', {'form': form, 'crop': crop})


@login_required
def crop_delete(request, pk):
    """Delete a crop record"""
    crop = get_object_or_404(CropSeason, pk=pk, field__farm__owner=request.user)
    if request.method == 'POST':
        crop.delete()
        messages.success(request, 'Crop record deleted successfully!')
        return redirect('core:crop_list')
    return render(request, 'crops/delete.html', {'crop': crop})


@login_required
def crop_harvest(request, crop_id):
    """Record harvest for a crop"""
    crop = get_object_or_404(CropSeason, pk=crop_id, field__farm__owner=request.user)
    
    if request.method == 'POST':
        form = HarvestForm(request.POST)
        if form.is_valid():
            harvest = form.save(commit=False)
            harvest.crop_season = crop
            harvest.save()
            
            # Update crop status if fully harvested
            total_harvested = Harvest.objects.filter(crop_season=crop).aggregate(Sum('quantity_kg'))['quantity_kg__sum'] or 0
            if total_harvested >= (crop.estimated_yield_kg or 0):
                crop.status = 'harvested'
                crop.actual_harvest_date = timezone.now().date()
                crop.save()
            
            messages.success(request, f'Harvest recorded: {harvest.quantity_kg}kg')
            return redirect('core:crop_detail', pk=crop.pk)
    else:
        form = HarvestForm(initial={'harvest_date': timezone.now().date()})
    
    return render(request, 'crops/harvest.html', {'form': form, 'crop': crop})


@login_required
def input_add(request, crop_id):
    """Add input application (fertilizer, pesticide)"""
    crop = get_object_or_404(CropSeason, pk=crop_id, field__farm__owner=request.user)
    
    if request.method == 'POST':
        form = InputForm(request.POST)
        if form.is_valid():
            input_app = form.save(commit=False)
            input_app.crop_season = crop
            input_app.applied_by = request.user
            input_app.save()
            messages.success(request, f'{input_app.product_name} applied successfully!')
            return redirect('core:crop_detail', pk=crop.pk)
    else:
        form = InputForm(initial={'application_date': timezone.now().date()})
    
    return render(request, 'crops/inputs.html', {'form': form, 'crop': crop})


# ============================================================
# LIVESTOCK MANAGEMENT
# ============================================================

@login_required
def animal_list(request):
    """List all animals"""
    # Run livestock automation checks
    LivestockAutomationService.run_automation_checks(user=request.user)
    
    animals = Animal.objects.filter(farm__owner=request.user)
    
    # Filter by species
    species_filter = request.GET.get('species')
    if species_filter:
        animals = animals.filter(animal_type__species=species_filter)
    
    return render(request, 'livestock/list.html', {
        'animals': animals,
        'export_url': reverse('core:export_livestock'),
    })


@login_required
def animal_add(request):
    """Add a new animal"""
    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES)
        if form.is_valid():
            animal = form.save(commit=False)
            animal.save()
            messages.success(request, f'Animal {animal.tag_number} added successfully!')
            return redirect('core:animal_detail', pk=animal.pk)
    else:
        form = AnimalForm()
        form.fields['farm'].queryset = Farm.objects.filter(owner=request.user)
        form.fields['animal_type'].queryset = AnimalType.objects.filter(is_active=True)
    
    # Get farms and animal types for initial form context
    farms = Farm.objects.filter(owner=request.user)
    animal_types = AnimalType.objects.filter(is_active=True)
    
    # Check if there's a farm_id in the request to pre-select farm
    farm_id = request.GET.get('farm_id')
    initial = {}
    if farm_id:
        try:
            farm = farms.get(id=farm_id)
            initial['farm'] = farm
        except Farm.DoesNotExist:
            pass
    
    return render(request, 'livestock/add.html', {
        'form': form,
        'farms': farms,
        'animal_types': animal_types,
        'initial_farm_id': farm_id
    })


@login_required
def animal_detail(request, pk):
    """Animal details view"""
    # Run livestock automation checks
    LivestockAutomationService.run_automation_checks(user=request.user)
    
    animal = get_object_or_404(Animal, pk=pk, farm__owner=request.user)
    health_records = HealthRecord.objects.filter(animal=animal).order_by('-record_date')[:10]
    breeding_records = BreedingRecord.objects.filter(animal=animal).order_by('-breeding_date')[:5]
    milk_records = MilkProduction.objects.filter(animal=animal).order_by('-production_date')[:30]
    
    return render(request, 'livestock/detail.html', {
        'animal': animal,
        'health_records': health_records,
        'breeding_records': breeding_records,
        'milk_records': milk_records
    })


@login_required
def animal_edit(request, pk):
    """Edit animal details"""
    animal = get_object_or_404(Animal, pk=pk, farm__owner=request.user)
    if request.method == 'POST':
        form = AnimalForm(request.POST, request.FILES, instance=animal)
        if form.is_valid():
            form.save()
            messages.success(request, 'Animal updated successfully!')
            return redirect('core:animal_detail', pk=animal.pk)
    else:
        form = AnimalForm(instance=animal)
    return render(request, 'livestock/edit.html', {'form': form, 'animal': animal})


@login_required
def animal_delete(request, pk):
    """Delete an animal record"""
    animal = get_object_or_404(Animal, pk=pk, farm__owner=request.user)
    if request.method == 'POST':
        animal.delete()
        messages.success(request, 'Animal record deleted successfully!')
        return redirect('core:animal_list')
    return render(request, 'livestock/delete.html', {'animal': animal})


@login_required
def health_record_add(request, animal_id):
    """Add health record for an animal"""
    animal = get_object_or_404(Animal, pk=animal_id, farm__owner=request.user)
    
    if request.method == 'POST':
        form = HealthRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.animal = animal
            record.save()
            messages.success(request, 'Health record added successfully!')
            return redirect('core:animal_detail', pk=animal.pk)
    else:
        form = HealthRecordForm(initial={'record_date': timezone.now().date()})
    
    return render(request, 'livestock/health.html', {'form': form, 'animal': animal})


@login_required
def breeding_record_add(request, animal_id):
    """Add breeding record for an animal"""
    animal = get_object_or_404(Animal, pk=animal_id, farm__owner=request.user)
    
    if request.method == 'POST':
        form = BreedingRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.animal = animal
            record.save()
            messages.success(request, 'Breeding record added successfully!')
            return redirect('core:animal_detail', pk=animal.pk)
    else:
        form = BreedingRecordForm(initial={'breeding_date': timezone.now().date()})
    
    return render(request, 'livestock/breeding.html', {'form': form, 'animal': animal})


@login_required
def milk_production_add(request, animal_id):
    """Add daily milk production record"""
    animal = get_object_or_404(Animal, pk=animal_id, farm__owner=request.user)
    
    if request.method == 'POST':
        form = MilkProductionForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.animal = animal
            record.save()
            messages.success(request, f'Milk production recorded: {record.total_kg}kg')
            return redirect('core:animal_detail', pk=animal.pk)
    else:
        form = MilkProductionForm(initial={'production_date': timezone.now().date()})
    
    return render(request, 'livestock/milk.html', {'form': form, 'animal': animal})


# ============================================================
# EQUIPMENT RENTAL
# ============================================================

@login_required
def equipment_list(request):
    """List all available equipment"""
    equipment = Equipment.objects.filter(is_verified=True, status='available')
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter:
        equipment = equipment.filter(category=category_filter)
    
    context = {
        'equipment': equipment,
        'export_url': reverse('core:export_equipment'),
    }
    return render(request, 'equipment/list.html', context)


@login_required
@login_required
def equipment_add(request):
    """Add equipment for rent"""
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.owner = request.user
            equipment.save()
            messages.success(request, 'Equipment listed for rent successfully!')
            return redirect('core:equipment_detail', pk=equipment.pk)
        else:
            # Log form errors for debugging
            for field, errors in form.errors.items():
                messages.error(request, f'{field}: {", ".join(errors)}')
    else:
        form = EquipmentForm()
    
    return render(request, 'equipment/add.html', {'form': form})


@login_required
def equipment_detail(request, pk):
    """Equipment details view"""
    equipment = get_object_or_404(Equipment, pk=pk)
    return render(request, 'equipment/detail.html', {'equipment': equipment})


@login_required
def equipment_edit(request, pk):
    """Edit equipment listing"""
    equipment = get_object_or_404(Equipment, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=equipment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Equipment updated successfully!')
            return redirect('core:equipment_detail', pk=equipment.pk)
    else:
        form = EquipmentForm(instance=equipment)
    return render(request, 'equipment/edit.html', {'form': form, 'equipment': equipment})


@login_required
def equipment_book(request, pk):
    """Book equipment for rent"""
    equipment = get_object_or_404(Equipment, pk=pk, status='available')
    
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.equipment = equipment
            booking.renter = request.user
            booking.save()
            
            # Update equipment status
            equipment.status = 'rented'
            equipment.save()
            
            # Create notifications
            Notification.objects.create(
                user=request.user,
                notification_type='success',
                title=f'Equipment Booked: {equipment.name}',
                message=f'You have successfully booked {equipment.name} from {equipment.owner.get_full_name or equipment.owner.username}. Total cost: ${booking.total_cost}',
                link=f'/equipment/bookings/{booking.id}/'
            )
            
            # Notify equipment owner
            Notification.objects.create(
                user=equipment.owner,
                notification_type='info',
                title=f'Equipment Booked: {equipment.name}',
                message=f'{request.user.get_full_name or request.user.username} has booked your {equipment.name}. Booking ID: {booking.id}',
                link=f'/equipment/{equipment.id}/'
            )
            
            messages.success(request, f'Equipment booked successfully! Total: ${booking.total_cost}')
            return redirect('core:my_bookings')
    else:
        form = BookingForm()
    
    return render(request, 'equipment/book.html', {'form': form, 'equipment': equipment})


@login_required
def my_bookings(request):
    """View user's equipment bookings"""
    bookings = EquipmentBooking.objects.filter(renter=request.user).order_by('-created_at')
    return render(request, 'equipment/my_bookings.html', {'bookings': bookings})


@login_required
def cancel_booking(request, pk):
    """Cancel a booking"""
    booking = get_object_or_404(EquipmentBooking, pk=pk, renter=request.user, status='pending')
    if request.method == 'POST':
        equipment = booking.equipment
        booking.status = 'cancelled'
        booking.save()
        
        # Make equipment available again
        equipment.status = 'available'
        equipment.save()
        
        messages.success(request, 'Booking cancelled successfully!')
        return redirect('core:my_bookings')
    
    return render(request, 'equipment/cancel_booking.html', {'booking': booking})


# ============================================================
# MARKETPLACE
# ============================================================

@login_required
def marketplace_list(request):
    """List all products for sale with search and filters - EXCLUDES OUT OF STOCK items"""
    # Filter for active listings that are NOT marked as out of stock
    listings = ProductListing.objects.filter(status='active', is_out_of_stock=False).order_by('-created_at')
    
    # Search - search by product name, description, or category
    search_query = request.GET.get('q', '').strip()
    if search_query:
        listings = listings.filter(
            Q(product_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__icontains=search_query) |
            Q(seller__farm_name__icontains=search_query)
        )
    
    # Filter by category
    category = request.GET.get('category', '').strip()
    if category:
        listings = listings.filter(category__icontains=category)
    
    # Filter by organic
    organic = request.GET.get('organic')
    if organic == 'true':
        listings = listings.filter(is_organic=True)
    
    # Filter by delivery available
    delivery = request.GET.get('delivery')
    if delivery == 'true':
        listings = listings.filter(delivery_available=True)
    
    # Get unique categories for filter dropdown
    all_categories = ProductListing.objects.filter(status='active', is_out_of_stock=False).values_list('category', flat=True).distinct().order_by('category')
    
    # Pagination
    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Build query string for pagination
    query_params = ''
    if search_query:
        query_params += f'&q={search_query}'
    if category:
        query_params += f'&category={category}'
    if organic == 'true':
        query_params += '&organic=true'
    if delivery == 'true':
        query_params += '&delivery=true'
    
    
    context = {
        'listings': page_obj,
        'search_query': search_query,
        'categories': all_categories,
        'selected_category': category,
        'selected_organic': organic == 'true',
        'selected_delivery': delivery == 'true',
        'query_params': query_params,
        'export_url': reverse('core:export_marketplace_products'),
    }
    
    return render(request, 'marketplace/list.html', context)


@login_required
def create_listing(request):
    """Create a new product listing"""
    # Check if user has any farms
    user_farms = Farm.objects.filter(owner=request.user)
    if not user_farms.exists():
        messages.error(request, 'You must create a farm profile before listing products. Please create a farm first.')
        return redirect('core:farm_create')
    
    if request.method == 'POST':
        form = ProductListingForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            listing = form.save()
            messages.success(request, 'Product listed for sale successfully!')
            return redirect('core:listing_detail', pk=listing.pk)
    else:
        form = ProductListingForm(user=request.user)
    
    return render(request, 'marketplace/create.html', {'form': form})


@login_required
def listing_detail(request, pk):
    """Product listing details"""
    listing = get_object_or_404(ProductListing, pk=pk)
    
    # Check if product is out of stock and user is not the seller
    if listing.is_out_of_stock and listing.seller.owner != request.user:
        messages.error(request, 'This product is no longer available.')
        return redirect('core:marketplace')
    
    return render(request, 'marketplace/detail.html', {'listing': listing})


@login_required
def edit_listing(request, pk):
    """Edit a product listing"""
    listing = get_object_or_404(ProductListing, pk=pk)
    
    # Check if user is the seller
    if listing.seller.owner != request.user:
        messages.error(request, 'You can only edit your own listings.')
        return redirect('core:listing_detail', pk=pk)
    
    old_quantity = listing.quantity
    
    if request.method == 'POST':
        form = ProductListingForm(request.POST, request.FILES, instance=listing, user=request.user)
        if form.is_valid():
            listing = form.save()
            
            # Check if quantity was updated and handle out of stock/low stock
            if old_quantity != listing.quantity:
                from .models import Reminder, Notification
                
                if listing.quantity <= 0:
                    listing.status = 'sold'
                    listing.is_out_of_stock = True
                    listing.quantity = 0
                    listing.save()
                    
                    # Create notification
                    Notification.objects.create(
                        user=listing.seller.owner,
                        notification_type='warning',
                        title=f'Out of Stock: {listing.product_name}',
                        message=f'Your product "{listing.product_name}" is now out of stock.',
                        link=f'/marketplace/'
                    )
                
                elif listing.quantity < 5:
                    # Check if we already notified recently
                    existing = Notification.objects.filter(
                        user=listing.seller.owner,
                        notification_type='warning',
                        title=f'Low Stock: {listing.product_name}'
                    ).filter(created_at__gte=timezone.now() - timedelta(hours=6)).exists()
                    
                    if not existing:
                        Notification.objects.create(
                            user=listing.seller.owner,
                            notification_type='warning',
                            title=f'Low Stock: {listing.product_name}',
                            message=f'Only {listing.quantity} units of "{listing.product_name}" left in stock!',
                            link=f'/marketplace/{listing.id}/'
                        )
            
            messages.success(request, 'Product listing updated successfully!')
            return redirect('core:listing_detail', pk=listing.pk)
    else:
        form = ProductListingForm(instance=listing, user=request.user)
    
    return render(request, 'marketplace/edit.html', {'form': form, 'listing': listing})


@login_required
def delete_listing(request, pk):
    """Delete a product listing"""
    listing = get_object_or_404(ProductListing, pk=pk)
    
    # Check if user is the seller
    if listing.seller.owner != request.user:
        messages.error(request, 'You can only delete your own listings.')
        return redirect('core:listing_detail', pk=pk)
    
    if request.method == 'POST':
        listing.delete()
        messages.success(request, 'Product listing deleted successfully!')
        return redirect('core:my_listings')
    
    # If not POST, redirect back (shouldn't happen with normal flow)
    return redirect('core:listing_detail', pk=pk)


@login_required
def toggle_out_of_stock(request, pk):
    """Toggle product listing out of stock status"""
    listing = get_object_or_404(ProductListing, pk=pk)
    
    # Check if user is the seller
    if listing.seller.owner != request.user:
        messages.error(request, 'You can only manage your own listings.')
        return redirect('core:listing_detail', pk=pk)
    
    # Toggle out of stock status
    listing.is_out_of_stock = not listing.is_out_of_stock
    
    if listing.is_out_of_stock:
        listing.status = 'sold'
        listing.quantity = 0
        messages.success(request, f'"{listing.product_name}" marked as OUT OF STOCK and removed from marketplace!')
        
        # Create notification for seller
        from .models import Notification
        Notification.objects.create(
            user=listing.seller.owner,
            notification_type='warning',
            title=f'Out of Stock: {listing.product_name}',
            message=f'Product "{listing.product_name}" has been marked as out of stock and is no longer visible to buyers.',
            link=f'/marketplace/{listing.id}/'
        )
    else:
        listing.status = 'active'
        messages.success(request, f'"{listing.product_name}" marked as BACK IN STOCK!')
        
        # Create notification for seller
        from .models import Notification
        Notification.objects.create(
            user=listing.seller.owner,
            notification_type='success',
            title=f'Back in Stock: {listing.product_name}',
            message=f'Product "{listing.product_name}" is now live on the marketplace!',
            link=f'/marketplace/{listing.id}/'
        )
    
    listing.save()
    return redirect('core:my_listings')


@login_required
def buy_product(request, pk):
    """Purchase a product"""
    listing = get_object_or_404(ProductListing, pk=pk, status='active', is_out_of_stock=False)
    
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.buyer = request.user
            order.listing = listing
            order.unit_price = listing.price_per_unit
            order.save()
            
            # Reduce quantity
            listing.quantity -= order.quantity
            
            # Handle out of stock
            if listing.quantity <= 0:
                listing.status = 'sold'
                listing.is_out_of_stock = True
                listing.quantity = 0
                
                # Create notification and reminder for seller
                from .models import Reminder, Notification
                
                Notification.objects.create(
                    user=listing.seller.owner,
                    notification_type='success',
                    title=f'Sold Out: {listing.product_name}',
                    message=f'Your product "{listing.product_name}" has sold out! Create a new listing to restock.',
                    link=f'/marketplace/'
                )
                
                # Create reminder to restock
                today = timezone.now().date()
                Reminder.objects.get_or_create(
                    farm=listing.seller,
                    user=listing.seller.owner,
                    title=f'Restock: {listing.product_name}',
                    reminder_type='general',
                    due_date=today,
                    defaults={
                        'is_active': True,
                        'description': f'Product "{listing.product_name}" sold out on marketplace. Consider harvesting more or sourcing additional stock.'
                    }
                )
            elif listing.quantity < 5:
                # Low stock warning
                existing = Notification.objects.filter(
                    user=listing.seller.owner,
                    notification_type='warning',
                    title=f'Low Stock: {listing.product_name}'
                ).filter(created_at__gte=timezone.now() - timedelta(hours=6)).exists()
                
                if not existing:
                    Notification.objects.create(
                        user=listing.seller.owner,
                        notification_type='warning',
                        title=f'Low Stock: {listing.product_name}',
                        message=f'Only {listing.quantity} units of "{listing.product_name}" left in stock!',
                        link=f'/marketplace/{listing.id}/'
                    )
            
            listing.save()
            
            messages.success(request, f'Order placed! Total: ${order.total_amount}')
            return redirect('core:my_orders')
    else:
        form = OrderForm(initial={'quantity': 1})
    
    return render(request, 'marketplace/buy.html', {'form': form, 'listing': listing})


@login_required
def my_listings(request):
    """View user's product listings"""
    listings = ProductListing.objects.filter(seller__owner=request.user).order_by('-created_at')
    return render(request, 'marketplace/my_listings.html', {'listings': listings})


@login_required
def my_orders(request):
    """View user's orders"""
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'marketplace/orders.html', {'orders': orders})


# ============================================================
# PEST DETECTION
# ============================================================

import base64
import openai
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

@login_required
def pest_detection(request):
    """Pest detection page"""
    recent_reports = PestReport.objects.filter(farmer=request.user).order_by('-created_at')[:5]
    context = {'recent_reports': recent_reports}
    return render(request, 'pest/detection.html', context)


def encode_image_to_base64(image_file):
    """Convert image file to base64 string"""
    image_file.seek(0)
    return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_pest_with_ai(image_file, image_name):
    """
    Use AI Vision API to analyze pest image - NEW VERSION
    
    Priority Order (all FREE for Render):
    1. Google Gemini (free tier - 60 req/min) - RECOMMENDED
    2. Groq (free tier) - fast alternative
    3. Together.ai (free tier) - another alternative
    4. Rule-based detection (completely free) - fallback
    5. OpenAI (DEPRECATED - too expensive for Render free tier)
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        from django.conf import settings
        from core.services.pest_detection import PestDetectionService
        
        # Use new unified pest detection service with 3-AI fallback
        gemini_api_key = getattr(settings, 'GEMINI_API_KEY', None)
        groq_api_key = getattr(settings, 'GROQ_API_KEY', None)
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        
        # Debug logging
        logger.info(f'GEMINI_API_KEY present: {bool(gemini_api_key) and len(str(gemini_api_key)) > 0}')
        logger.info(f'GROQ_API_KEY present: {bool(groq_api_key) and len(str(groq_api_key)) > 0}')
        logger.info(f'OPENAI_API_KEY present: {bool(openai_api_key) and len(str(openai_api_key)) > 0}')
        
        pest_service = PestDetectionService(gemini_api_key, groq_api_key, openai_api_key)
        
        logger.info(f'Starting pest detection analysis for {image_name}')
        
        # Analyze image using service
        logger.info(f'[VIEWS] Calling pest_service.detect_from_image() for {image_name}')
        result = pest_service.detect_from_image(image_file)
        logger.info(f'[VIEWS] Result received: {result}')
        logger.info(f'[VIEWS] Result has error_fallback: {result.get("error_fallback")}')
        
        # Normalize result to match expected format
        normalized = {
            'pest_detected': result.get('detected_issue', '').lower() != 'healthy crop' and not result.get('error_fallback'),
            'pest_name': result.get('detected_issue', 'Unable to analyze'),
            'confidence': result.get('confidence', 0),
            'severity': result.get('severity', 'low'),
            'affected_area': 0,
            'explanation': result.get('description', 'Analysis attempted'),
            'identification_details': result.get('description', ''),
            'immediate_action': 'Monitor closely' if result.get('severity') in ['high', 'severe'] else 'Continue normal care',
            'treatment': result.get('treatment', 'Consult local expert'),
            'organic_treatment': result.get('organic_options', 'Contact extension office'),
            'prevention': result.get('prevention', 'Regular field scouting'),
            'disease_cycle': '',
            'environmental_factors': ''
        }
        
        logger.info(f'[VIEWS] Normalized: pest_detected={normalized["pest_detected"]}, pest_name={normalized["pest_name"]}, confidence={normalized["confidence"]}')
        logger.info(f'Pest analysis completed: {normalized["pest_name"]}')
        return normalized
    
    except Exception as e:
        logger.error(f'Pest analysis error: {str(e)}')
        logger.error(f'Error type: {type(e).__name__}')
        logger.error(f'Full error: {repr(e)}', exc_info=True)
        
        return {
            'pest_detected': False,
            'pest_name': 'Error',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': f'Error analyzing image: {str(e)}',
            'identification_details': 'Error occurred',
            'immediate_action': 'Please try again or use rule-based detection',
            'treatment': f'Error: {str(e)}',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': f'System error: {str(e)}'
        }


def analyze_pest_with_together(base64_image, media_type, api_key, logger):
    """Analyze pest using Together.ai API (works with Render)"""
    try:
        url = "https://api.together.xyz/v1/chat/completions"
        
        # Log API key status (first 10 chars only)
        logger.info(f'Together.ai API key status: SET')
        logger.info(f'Together.ai API key preview: {api_key[:10]}...')
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "meta-llama/Llama-Vision-Free",  # Free vision model
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """You are an agricultural disease and pest expert. Analyze this crop image in detail for pests, diseases, or other issues. Provide a comprehensive JSON response with these exact keys:

{
    "pest_detected": true or false,
    "pest_name": "Specific pest/disease name or 'Healthy Crop' if no issues found",
    "confidence": 0-100 (your confidence level),
    "severity": "none, low, medium, high, or severe",
    "affected_area": 0-100 (percentage of crop affected),
    "explanation": "Detailed 2-3 sentence explanation of what you observe",
    "identification_details": "Specific visual indicators that led to diagnosis",
    "immediate_action": "What the farmer should do immediately",
    "treatment": "Detailed treatment options",
    "organic_treatment": "Organic alternatives",
    "prevention": "Long-term prevention strategies",
    "disease_cycle": "Brief explanation of disease lifecycle",
    "environmental_factors": "Conditions that favor this pest/disease"
}

Be thorough, professional, and educational."""
                        }
                    ]
                }
            ],
            "max_tokens": 1024,
            "temperature": 0.7
        }
        
        logger.info('Sending request to Together.ai...')
        logger.info(f'URL: {url}')
        logger.info(f'Model: {payload["model"]}')
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        logger.info(f'Response status: {response.status_code}')
        logger.info(f'Response headers: {response.headers}')
        
        if response.status_code != 200:
            logger.error(f'Response text: {response.text}')
        
        response.raise_for_status()
        
        result_data = response.json()
        result_text = result_data['choices'][0]['message']['content'].strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(result_text)
        
        logger.info(f'Together.ai analysis completed: {result.get("pest_name")}')
        return result
    
    except requests.exceptions.HTTPError as e:
        logger.error(f'Together.ai HTTP error: {e.response.status_code}')
        logger.error(f'Response text: {e.response.text}')
        logger.error(f'Error details: {str(e)}')
        
        return {
            'pest_detected': False,
            'pest_name': 'API Error',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': f'Together.ai service error: {e.response.status_code} - {e.response.text[:200]}',
            'identification_details': 'API error occurred',
            'immediate_action': 'Please try again later or check API key',
            'treatment': f'API Error: {e.response.status_code}',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': f'Together.ai API error: {e.response.status_code}'
        }
    
    except requests.exceptions.RequestException as e:
        logger.error(f'Together.ai request error: {str(e)}')
        logger.error(f'Error type: {type(e).__name__}')
        return {
            'pest_detected': False,
            'pest_name': 'API Error',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': f'Together.ai service error: {str(e)}',
            'identification_details': 'API error occurred',
            'immediate_action': 'Please try again later',
            'treatment': f'API Error: {str(e)}',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': f'Together.ai API error: {str(e)}'
        }
    
    except Exception as e:
        logger.error(f'Together.ai error: {str(e)}')
        logger.error(f'Error type: {type(e).__name__}', exc_info=True)
        return {
            'pest_detected': False,
            'pest_name': 'Error',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': f'Error: {str(e)}',
            'identification_details': 'Error occurred',
            'immediate_action': 'Please try again',
            'treatment': f'Error: {str(e)}',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': f'Error: {str(e)}'
        }


def analyze_pest_with_groq(base64_image, media_type, api_key, logger):
    """Analyze pest using Groq API (very fast, free tier available)"""
    try:
        from groq import Groq
        
        logger.info('Using Groq for pest detection')
        
        client = Groq(api_key=api_key)
        
        # Groq doesn't support direct image input like OpenAI, so we use text analysis
        # You would need to use OCR or describe the image
        # For now, we'll use Groq for quick text-based analysis
        
        prompt = """You are an agricultural disease and pest expert. Based on this image analysis, provide a comprehensive pest detection report.

Analyze for pests, diseases, or crop health issues. Provide a JSON response with these exact keys:

{
    "pest_detected": true or false,
    "pest_name": "Specific pest/disease name or 'Healthy Crop' if no issues found",
    "confidence": 0-100 (your confidence level),
    "severity": "none, low, medium, high, or severe",
    "affected_area": 0-100 (percentage of crop affected),
    "explanation": "Detailed 2-3 sentence explanation of what you observe",
    "identification_details": "Specific visual indicators that led to diagnosis",
    "immediate_action": "What the farmer should do immediately",
    "treatment": "Detailed treatment options",
    "organic_treatment": "Organic alternatives",
    "prevention": "Long-term prevention strategies",
    "disease_cycle": "Brief explanation of disease lifecycle",
    "environmental_factors": "Conditions that favor this pest/disease"
}

Be thorough, professional, and educational."""
        
        message = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Available and fast
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        
        result_text = message.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(result_text)
        
        logger.info(f'Groq analysis completed: {result.get("pest_name")}')
        return result
    
    except Exception as e:
        logger.error(f'Groq error: {str(e)}')
        logger.error(f'Error type: {type(e).__name__}', exc_info=True)
        return {
            'pest_detected': False,
            'pest_name': 'Error',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': f'Error: {str(e)}',
            'identification_details': 'Error occurred',
            'immediate_action': 'Please try again',
            'treatment': f'Error: {str(e)}',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': f'Groq API error: {str(e)}'
        }


def analyze_pest_with_openai(base64_image, media_type, api_key, logger):
    """Analyze pest using OpenAI API (fallback)"""
    try:
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """You are an agricultural disease and pest expert. Analyze this crop image in detail for pests, diseases, or other issues. Provide a comprehensive JSON response with these exact keys:

{
    "pest_detected": true or false,
    "pest_name": "Specific pest/disease name or 'Healthy Crop' if no issues found",
    "confidence": 0-100,
    "severity": "none, low, medium, high, or severe",
    "affected_area": 0-100,
    "explanation": "Detailed explanation",
    "identification_details": "Visual indicators",
    "immediate_action": "What the farmer should do",
    "treatment": "Treatment options",
    "organic_treatment": "Organic alternatives",
    "prevention": "Prevention strategies",
    "disease_cycle": "Disease lifecycle",
    "environmental_factors": "Conditions that favor this"
}"""
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        result_text = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(result_text)
        
        logger.info(f'OpenAI analysis completed: {result.get("pest_name")}')
        return result
    
    except openai.APIError as e:
        logger.error(f'OpenAI API error: {str(e)}')
        logger.error(f'Error type: {type(e).__name__}')
        return {
            'pest_detected': False,
            'pest_name': 'API Error',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': f'OpenAI service error: {str(e)}',
            'identification_details': 'API error occurred',
            'immediate_action': 'Please try again later',
            'treatment': f'API Error: {str(e)}',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': f'OpenAI API error: {str(e)}'
        }
    
    except Exception as e:
        logger.error(f'OpenAI error: {str(e)}')
        logger.error(f'Error type: {type(e).__name__}', exc_info=True)
        return {
            'pest_detected': False,
            'pest_name': 'Error',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': f'Error: {str(e)}',
            'identification_details': 'Error occurred',
            'immediate_action': 'Please try again',
            'treatment': f'Error: {str(e)}',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': f'Error: {str(e)}'
        }
        
        # Call OpenAI Vision API
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o",  # Current vision model (gpt-4-vision-preview is deprecated)
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{media_type};base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": """You are an agricultural disease and pest expert. Analyze this crop image in detail for pests, diseases, or other issues. Provide a comprehensive JSON response with these exact keys:

{
    "pest_detected": true or false,
    "pest_name": "Specific pest/disease name or 'Healthy Crop' if no issues found",
    "confidence": 0-100 (your confidence level),
    "severity": "none, low, medium, high, or severe",
    "affected_area": 0-100 (percentage of crop affected),
    "explanation": "Detailed 2-3 sentence explanation of what you observe in the image, what specific symptoms or signs indicate this condition, and why you're confident about this diagnosis",
    "identification_details": "Specific visual indicators that led to this diagnosis (leaf color, spots, wilting, insects, etc.)",
    "immediate_action": "What the farmer should do immediately if pest/disease is detected, or general care tips if healthy",
    "treatment": "Detailed chemical treatment options with specific product names/dosages if applicable",
    "organic_treatment": "Detailed organic alternatives including natural pesticides, companion planting, cultural practices",
    "prevention": "Long-term prevention strategies to avoid this problem in the future",
    "disease_cycle": "Brief explanation of how this pest/disease spreads and its life cycle",
    "environmental_factors": "Conditions that favor this pest/disease development"
}

Be thorough, professional, and educational. Provide practical, actionable advice based on your observations."""
                        }
                    ]
                }
            ],
            max_tokens=2000
        )
        
        # Parse response
        result_text = response.choices[0].message.content.strip()
        
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(result_text)
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f'OpenAI analysis completed: {result.get("pest_name")}')
        
        return result
    
    except openai.APIError as e:
        # OpenAI API error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'OpenAI API error: {str(e)}')
        logger.error(f'Error type: {type(e).__name__}')
        logger.error(f'Full error: {repr(e)}')
        
        return {
            'pest_detected': False,
            'pest_name': 'API Error',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': f'OpenAI service error: {str(e)}',
            'identification_details': 'API error occurred',
            'immediate_action': 'Please try again later',
            'treatment': f'API Error: {str(e)}',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': f'OpenAI API error: {str(e)}'
        }
    
    except json.JSONDecodeError as e:
        # JSON parsing error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'JSON decode error: {str(e)}')
        
        return {
            'pest_detected': False,
            'pest_name': 'Analysis Failed',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': 'Unable to parse analysis results. Try uploading a clearer image.',
            'identification_details': 'Image quality too low for detailed analysis',
            'immediate_action': 'Try uploading another image with better lighting and focus',
            'treatment': 'Image quality may be too low. Please try with a clearer image.',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': f'Analysis parsing error: {str(e)}'
        }
    
    except Exception as e:
        # Any other error (including connection errors)
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Pest analysis error: {str(e)}')
        logger.error(f'Error type: {type(e).__name__}')
        logger.error(f'Full error: {repr(e)}')
        logger.error(f'Traceback:', exc_info=True)
        
        return {
            'pest_detected': False,
            'pest_name': 'Error',
            'confidence': 0,
            'severity': 'low',
            'affected_area': 0,
            'explanation': f'Error analyzing image: {str(e)}',
            'identification_details': 'Error occurred',
            'immediate_action': 'Please try again',
            'treatment': f'Error: {str(e)}',
            'organic_treatment': '',
            'prevention': '',
            'disease_cycle': '',
            'environmental_factors': '',
            'error': str(e)
        }


@login_required
@throttle_pest_detection
def pest_upload(request):
    """Upload and analyze pest image"""
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            image_file = request.FILES['image']
            
            # Check if file is provided
            if not image_file:
                messages.error(request, 'Please select an image file.')
                return redirect('core:pest_detection')
            
            # Validate image format
            try:
                img = Image.open(image_file)
                img.verify()
                image_file.seek(0)
            except Exception as img_err:
                messages.error(request, f'Invalid image format: {str(img_err)}')
                return redirect('core:pest_detection')
            
            # Check file size (max 10MB)
            if image_file.size > 10 * 1024 * 1024:
                messages.error(request, 'Image size too large. Maximum 10MB allowed.')
                return redirect('core:pest_detection')
            
            # Get farm and field
            farm = request.user.farms.first()
            field = None
            if farm:
                field = Field.objects.filter(farm=farm).first()
            
            if not farm:
                # Create a default farm if user doesn't have one
                from django.utils import timezone
                farm = Farm.objects.create(
                    owner=request.user,
                    name='My Farm',
                    address='Default Location',
                    total_area_hectares=0,
                    farm_type='crop'
                )
                messages.info(request, 'Created a default farm for you. Update your farm details in settings.')
            
            # Analyze image with AI
            result = analyze_pest_with_ai(image_file, image_file.name)
            
            # Ensure result has all required fields
            if not result:
                result = {}
            
            # Set defaults for missing fields
            defaults = {
                'pest_detected': False,
                'pest_name': 'Analysis Pending',
                'confidence': 0,
                'severity': 'low',
                'affected_area': 0,
                'explanation': 'Please try again.',
                'identification_details': '',
                'immediate_action': '',
                'treatment': '',
                'organic_treatment': '',
                'prevention': '',
                'disease_cycle': '',
                'environmental_factors': ''
            }
            
            for key, default_value in defaults.items():
                if key not in result:
                    result[key] = default_value
            
            # Create report
            report = PestReport.objects.create(
                farmer=request.user,
                farm=farm,
                field=field,
                image=image_file,
                ai_diagnosis=result.get('pest_name', 'Analysis Complete'),
                analysis_description=result.get('explanation', ''),
                confidence=Decimal(str(result.get('confidence', 0))),
                severity=result.get('severity', 'low'),
                affected_area_percentage=Decimal(str(result.get('affected_area', 0))),
                treatment_recommended=result.get('treatment', ''),
                prevention_tips=result.get('prevention', ''),
                organic_options=result.get('organic_treatment', ''),
                status='pending' if result.get('pest_detected') else 'healthy'
            )
            
            # Create notification for farmer about pest detection
            if result.get('pest_detected'):
                Notification.objects.create(
                    user=request.user,
                    notification_type='alert',
                    title=f'Pest Detected: {result.get("pest_name")}',
                    message=f'A {result.get("severity", "unknown")} severity {result.get("pest_name")} was detected in your crop with {result.get("confidence")}% confidence. An agronomist will review this soon.',
                    link=f'/pest-detection/{report.id}/'
                )
                
                # Send notification to assigned agronomists for VERIFICATION
                assigned_agronomists = User.objects.filter(
                    user_type='agronomist',
                    assigned_farms=farm
                )
                
                for agronomist in assigned_agronomists:
                    Notification.objects.create(
                        user=agronomist,
                        notification_type='alert',
                        title=f'Pest Detection Review Needed - {result.get("pest_name")}',
                        message=f'Farmer {request.user.get_full_name()} submitted a pest detection report from {farm.name}.\n\nDetected Issue: {result.get("pest_name")}\nSeverity: {result.get("severity", "unknown")}\nAI Confidence: {result.get("confidence")}%\n\nPlease review and verify this diagnosis.',
                        link=f'/pest-verification/{report.id}/'
                    )
            else:
                Notification.objects.create(
                    user=request.user,
                    notification_type='success',
                    title='Crop Analysis Complete',
                    message='Your crop appears healthy with no major pest or disease detected.',
                    link=f'/pest-detection/{report.id}/'
                )
            
            # Add report ID to result
            result['report_id'] = report.id
            
            # Log the analysis
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f'Pest analysis completed for user {request.user.id}: {result.get("pest_name")}')
            
            messages.success(request, 'Image analyzed successfully!')
            return render(request, 'pest/results.html', {'result': result, 'report': report})
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Error in pest_upload: {str(e)}', exc_info=True)
            
            messages.error(request, f'Error analyzing image: {str(e)}')
            return redirect('core:pest_detection')
    
    return redirect('core:pest_detection')


@login_required
def pest_history(request):
    """View pest detection history"""
    # Get all reports for current user
    reports = PestReport.objects.filter(farmer=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'total_reports': reports.count(),
        'pending': reports.filter(status='pending').count(),
        'verified': reports.filter(agronomist_verified=True).count(),
        'healthy': reports.filter(status='healthy').count(),
    }
    
    context = {
        'page_obj': page_obj, 
        'stats': stats,
        'export_url': reverse('core:export_pest_reports'),
    }
    return render(request, 'pest/history.html', context)


@login_required
def pest_detail(request, pk):
    """Pest report details"""
    report = get_object_or_404(PestReport, pk=pk, farmer=request.user)
    return render(request, 'pest/detail.html', {'report': report})


# ============================================================
# WEATHER
# ============================================================

@login_required
def weather_forecast(request):
    """Weather forecast page with real data and alerts"""
    farms = Farm.objects.filter(owner=request.user)
    
    weather = None
    forecast = []
    alerts = []
    message = None
    
    if not farms.exists():
        message = "Please create a farm first to see weather forecasts."
    else:
        # Get weather data from first farm
        farm = farms.first()
        weather_data = WeatherData.objects.filter(farm=farm).first()
        
        if weather_data:
            weather = {
                'temp': weather_data.temperature,
                'feels_like': weather_data.feels_like,
                'condition': weather_data.condition,
                'description': weather_data.description,
                'humidity': weather_data.humidity,
                'pressure': weather_data.pressure,
                'wind_speed': weather_data.wind_speed,
                'wind_direction': weather_data.wind_direction,
                'location': weather_data.location,
                'last_updated': weather_data.last_updated,
            }
            
            # Get forecast data
            if weather_data.forecast_data.get('forecast'):
                from datetime import datetime
                forecast_raw = weather_data.forecast_data.get('forecast', [])
                
                for item in forecast_raw:
                    forecast.append({
                        'day': datetime.fromtimestamp(item['date']).date(),
                        'temp_high': item.get('temp_high', 'N/A'),
                        'temp_low': item.get('temp_low', 'N/A'),
                        'condition': item.get('condition', 'Unknown'),
                        'description': item.get('description', ''),
                        'icon': item.get('icon', ''),
                        'humidity': item.get('humidity', 'N/A'),
                        'wind_speed': item.get('wind_speed', 'N/A'),
                    })
        else:
            message = "Weather forecast data not available. The system will fetch data automatically every 30 minutes."
        
        # Get active alerts for user's farms
        alerts = WeatherAlert.objects.filter(
            farm__in=farms,
            is_read=False
        ).order_by('-severity', '-created_at')[:5]  # Top 5 unread alerts
    
    return render(request, 'weather/forecast.html', {
        'weather': weather or {},
        'forecast': forecast,
        'alerts': alerts,
        'message': message
    })


@login_required
def weather_alerts(request):
    """Weather alerts for user's farms"""
    farms = Farm.objects.filter(owner=request.user)


@login_required
def api_weather_forecast_live(request, farm_id):
    """
    API endpoint for real-time weather forecast using Open-Meteo (FREE API)
    No API key required - works on Render free tier!
    """
    from core.services.weather import weather_service
    import json
    from django.http import JsonResponse
    
    try:
        farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
        
        if not farm.location_lat or not farm.location_lng:
            return JsonResponse({
                "error": "Farm location not set",
                "status": "error"
            }, status=400)
        
        # Get agricultural forecast using Open-Meteo (FREE)
        forecast = weather_service.get_agricultural_forecast(
            float(farm.location_lat), 
            float(farm.location_lng)
        )
        
        return JsonResponse(forecast)
        
    except Farm.DoesNotExist:
        return JsonResponse({
            "error": "Farm not found",
            "status": "error"
        }, status=404)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Weather API error: {str(e)}")
        
        return JsonResponse({
            "error": str(e),
            "status": "error",
            "message": "Failed to fetch weather forecast"
        }, status=500)


@login_required
def api_weather_agricultural(request, farm_id):
    """
    API endpoint for agricultural indicators (GDD, THI, frost risk, pest risk)
    Uses Open-Meteo free API - perfect for decision support
    """
    from core.services.weather import weather_service
    from django.http import JsonResponse
    
    try:
        farm = get_object_or_404(Farm, id=farm_id, owner=request.user)
        
        if not farm.location_lat or not farm.location_lng:
            return JsonResponse({
                "error": "Farm location not set",
                "message": "Please update your farm's GPS coordinates"
            }, status=400)
        
        # Get detailed agricultural indicators
        ag_data = weather_service.get_agricultural_forecast(
            float(farm.location_lat),
            float(farm.location_lng)
        )
        
        if 'error' in ag_data:
            return JsonResponse(ag_data, status=500)
        
        return JsonResponse({
            "status": "success",
            "farm": farm.name,
            "location": {
                "latitude": float(farm.location_lat),
                "longitude": float(farm.location_lng)
            },
            "indicators": ag_data.get('forecast', []),
            "alerts": ag_data.get('alerts', []),
            "generated_at": str(datetime.now())
        })
        
    except Farm.DoesNotExist:
        return JsonResponse({
            "error": "Farm not found"
        }, status=404)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Agricultural API error: {str(e)}")
        
        return JsonResponse({
            "error": "Failed to fetch agricultural indicators",
            "message": str(e)
        }, status=500)
    alerts = WeatherAlert.objects.filter(farm__in=farms, is_read=False).order_by('-created_at')
    return render(request, 'weather/alerts.html', {'alerts': alerts})


@login_required
def mark_alert_read(request, pk):
    """Mark weather alert as read"""
    alert = get_object_or_404(WeatherAlert, pk=pk)
    alert.is_read = True
    alert.save()
    return redirect('core:weather_alerts')
# ============================================================
# IRRIGATION
# ============================================================

@login_required
def irrigation_dashboard(request):
    """Irrigation management dashboard"""
    farms = Farm.objects.filter(owner=request.user)
    
    # Get upcoming schedules
    schedules = IrrigationSchedule.objects.filter(
        field__farm__in=farms,
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date')[:10]
    
    # Calculate statistics
    # Total water used (completed irrigations)
    completed_irrigations = IrrigationSchedule.objects.filter(
        field__farm__in=farms,
        status='completed'
    )
    # Calculate water: duration_hours * field_area_hectares * 1000 liters
    total_water = sum(
        irr.duration_hours * irr.field.area_hectares * 1000 
        for irr in completed_irrigations
    )
    
    # Hours this month (current month and year)
    current_month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month_start = (current_month_start + timedelta(days=32)).replace(day=1)
    
    month_hours = IrrigationSchedule.objects.filter(
        field__farm__in=farms,
        scheduled_date__gte=current_month_start.date(),
        scheduled_date__lt=next_month_start.date()
    ).aggregate(total=Sum('duration_hours'))['total'] or 0
    
    # Next scheduled irrigation
    next_scheduled = IrrigationSchedule.objects.filter(
        field__farm__in=farms,
        status='scheduled',
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date').first()
    
    context = {
        'schedules': schedules,
        'total_water': round(total_water, 2),
        'month_hours': month_hours,
        'next_scheduled': next_scheduled,
    }
    
    return render(request, 'irrigation/dashboard.html', context)
@login_required
@login_required
def irrigation_schedule(request):
    """Schedule irrigation"""
    # Get field_id from URL parameter if provided
    field_id = request.GET.get('field_id', None)
    
    if request.method == 'POST':
        form = IrrigationForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, f'Irrigation scheduled for {schedule.field.name} on {schedule.scheduled_date}')
            return redirect('core:irrigation')
    else:
        # Get user's fields
        user_fields = Field.objects.filter(farm__owner=request.user)
        
        form = IrrigationForm()
        form.fields['field'].queryset = user_fields
        
        # Auto-populate field if provided via URL parameter
        if field_id:
            try:
                field = Field.objects.get(id=field_id, farm__owner=request.user)
                form.fields['field'].initial = field
            except Field.DoesNotExist:
                pass
        # Auto-select if only one field exists
        elif user_fields.count() == 1:
            form.fields['field'].initial = user_fields.first()
    
    return render(request, 'irrigation/schedule.html', {'form': form})


@login_required
def complete_irrigation(request, pk):
    """Mark irrigation as completed"""
    schedule = get_object_or_404(IrrigationSchedule, pk=pk, field__farm__owner=request.user)
    schedule.status = 'completed'
    schedule.actual_date = timezone.now().date()
    schedule.save()
    messages.success(request, 'Irrigation marked as completed!')
    return redirect('core:irrigation')


# ============================================================
# INSURANCE
# ============================================================

@login_required
def insurance_dashboard(request):
    """Insurance dashboard"""
    # Run insurance automation checks
    try:
        InsuranceAutomationService.run_automation_checks(user=request.user)
    except:
        pass  # Fail silently if automation service has issues
    
    policies = InsurancePolicy.objects.filter(farmer=request.user).order_by('-created_at')
    context = {
        'policies': policies,
        'export_url': reverse('core:export_insurance_policies'),
    }
    return render(request, 'insurance/dashboard.html', context)


@login_required
def buy_insurance(request):
    """Purchase insurance policy"""
    if request.method == 'POST':
        form = InsuranceForm(request.POST)
        if form.is_valid():
            policy = form.save(commit=False)
            policy.farmer = request.user
            # Calculate premium as 5% of sum insured
            policy.premium_paid = policy.sum_insured * Decimal('0.05')
            policy.save()
            messages.success(request, f'Insurance policy {policy.policy_number} purchased successfully! Premium: ${policy.premium_paid:.2f}')
            return redirect('core:insurance')
        else:
            # Log form errors for debugging
            for field, errors in form.errors.items():
                messages.error(request, f'{field}: {", ".join(errors)}')
    else:
        form = InsuranceForm()
    
    return render(request, 'insurance/buy.html', {'form': form})


@login_required
def insurance_detail(request, pk):
    """Insurance policy details"""
    policy = get_object_or_404(InsurancePolicy, pk=pk, farmer=request.user)
    return render(request, 'insurance/detail.html', {'policy': policy})


@login_required
def file_claim(request, policy_id):
    """File an insurance claim"""
    policy = get_object_or_404(InsurancePolicy, pk=policy_id, farmer=request.user)
    
    if request.method == 'POST':
        form = ClaimForm(request.POST, request.FILES)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.policy = policy
            claim.save()
            messages.success(request, 'Claim submitted successfully!')
            return redirect('core:my_claims')
    else:
        form = ClaimForm()
    
    return render(request, 'insurance/claim.html', {'form': form, 'policy': policy})


@login_required
def my_claims(request):
    """View user's claims"""
    claims = InsuranceClaim.objects.filter(policy__farmer=request.user).order_by('-claim_date')
    return render(request, 'insurance/claims.html', {'claims': claims})


# ============================================================
# LABOR MANAGEMENT
# ============================================================

@login_required
def labor_dashboard(request):
    """Labor management dashboard"""
    farms = Farm.objects.filter(owner=request.user)
    workers = Worker.objects.filter(farm__in=farms, is_active=True)
    
    # Total hours this month
    total_hours = WorkShift.objects.filter(
        worker__farm__in=farms,
        date__month=timezone.now().month
    ).aggregate(total=Sum('hours_worked'))['total'] or 0
    
    return render(request, 'labor/dashboard.html', {
        'workers': workers,
        'total_hours': total_hours
    })


@login_required
def add_worker(request):
    """Add a worker"""
    if request.method == 'POST':
        form = WorkerForm(request.POST)
        if form.is_valid():
            # Check if new worker name was provided
            new_worker_name = form.cleaned_data.get('new_worker_name')
            worker_user = form.cleaned_data.get('worker')
            
            # If new worker name provided, create new user
            if new_worker_name and not worker_user:
                # Generate username from the name
                username = new_worker_name.lower().replace(' ', '_')
                # Ensure unique username
                base_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Generate unique placeholder phone number
                phone_number = f"+255{username[:10]}"
                counter = 1
                while User.objects.filter(phone_number=phone_number).exists():
                    phone_number = f"+255{username[:8]}{counter}"
                    counter += 1
                
                # Create the user with a placeholder phone number
                # Phone number will need to be updated later by the user
                worker_user = User.objects.create_user(
                    username=username,
                    first_name=new_worker_name.split()[0],
                    last_name=' '.join(new_worker_name.split()[1:]) if len(new_worker_name.split()) > 1 else '',
                    user_type='labor',
                    phone_number=phone_number
                )
                form.instance.worker = worker_user
            
            worker = form.save()
            messages.success(request, f'Worker {worker.worker.get_full_name()} added!')
            return redirect('core:labor')
    else:
        form = WorkerForm()
        # Filter farms to show only those owned by the logged-in user
        form.fields['farm'].queryset = Farm.objects.filter(owner=request.user)
        # Filter worker dropdown to show only users not yet assigned as workers
        form.fields['worker'].queryset = User.objects.exclude(
            worker_profiles__farm__owner=request.user
        ).filter(is_active=True)
    
    # Pass filtered querysets to template context
    farms = Farm.objects.filter(owner=request.user)
    workers = User.objects.exclude(
        worker_profiles__farm__owner=request.user
    ).filter(is_active=True)
    
    return render(request, 'labor/add.html', {'form': form, 'farms': farms, 'workers': workers})


@login_required
def edit_worker(request, pk):
    """Edit worker details"""
    worker = get_object_or_404(Worker, pk=pk, farm__owner=request.user)
    if request.method == 'POST':
        form = WorkerForm(request.POST, instance=worker)
        if form.is_valid():
            form.save()
            messages.success(request, 'Worker updated!')
            return redirect('core:labor')
    else:
        form = WorkerForm(instance=worker)
    return render(request, 'labor/edit.html', {'form': form, 'worker': worker})


@login_required
def log_hours(request, worker_id):
    """Log work hours for a worker"""
    worker = get_object_or_404(Worker, pk=worker_id, farm__owner=request.user)
    
    if request.method == 'POST':
        form = WorkShiftForm(request.POST)
        if form.is_valid():
            shift = form.save(commit=False)
            shift.worker = worker
            shift.wage_rate = worker.hourly_wage
            shift.recorded_by = request.user
            shift.save()
            messages.success(request, f'{shift.hours_worked} hours logged for {worker.worker.get_full_name()}')
            return redirect('core:labor')
    else:
        form = WorkShiftForm(initial={'date': timezone.now().date()})
        # Filter fields to show only fields on the worker's farm
        form.fields['field'].queryset = Field.objects.filter(farm=worker.farm)
        # Make field optional as not all work is tied to a specific field
        form.fields['field'].required = False
    
    # Get fields for the worker's farm to pass to template
    fields = Field.objects.filter(farm=worker.farm)
    
    return render(request, 'labor/hours.html', {'form': form, 'worker': worker, 'fields': fields})


@login_required
def payroll_list(request):
    """View payroll records"""
    # Run payroll automation checks
    try:
        PayrollAutomationService.run_automation_checks(user=request.user)
    except:
        pass  # Fail silently if automation service has issues
    
    farms = Farm.objects.filter(owner=request.user)
    payrolls = Payroll.objects.filter(worker__farm__in=farms).order_by('-period_start')
    context = {
        'payrolls': payrolls,
        'export_url': reverse('core:export_payroll'),
    }
    return render(request, 'labor/payroll.html', context)


@login_required
def process_payroll(request, pk):
    """Process payroll for a worker"""
    worker = get_object_or_404(Worker, pk=pk, farm__owner=request.user)
    
    # Get shifts for current month
    shifts = WorkShift.objects.filter(
        worker=worker,
        date__month=timezone.now().month
    )
    
    total_hours = shifts.aggregate(total=Sum('hours_worked'))['total'] or 0
    total_pay = total_hours * worker.hourly_wage
    
    payroll = Payroll.objects.create(
        worker=worker,
        period_start=timezone.now().date().replace(day=1),
        period_end=timezone.now().date(),
        total_hours=total_hours,
        total_pay=total_pay,
        net_pay=total_pay  # No deductions for simplicity
    )
    
    messages.success(request, f'Payroll processed: ${total_pay} for {total_hours} hours')
    return redirect('core:payroll_list')


@login_required
def payroll_edit(request, pk):
    """Edit a payroll record"""
    payroll = get_object_or_404(Payroll, pk=pk, worker__farm__owner=request.user)
    
    if request.method == 'POST':
        form = PayrollForm(request.POST, instance=payroll)
        if form.is_valid():
            form.save()
            # Recalculate net_pay based on deductions
            payroll.net_pay = payroll.total_pay - payroll.deductions
            payroll.save()
            messages.success(request, f'Payroll updated for {payroll.worker.worker.get_full_name()}')
            return redirect('core:payroll_list')
    else:
        form = PayrollForm(instance=payroll)
    
    return render(request, 'labor/payroll_edit.html', {
        'form': form,
        'payroll': payroll,
        'worker': payroll.worker,
    })


# ============================================================
# REPORTS
# ============================================================

@login_required
def reports_dashboard(request):
    """Reports dashboard"""
    farms = Farm.objects.filter(owner=request.user)
    
    # Financial summary
    total_revenue = Transaction.objects.filter(
        farm__in=farms,
        transaction_type='income',
        date__year=timezone.now().year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_expenses = Transaction.objects.filter(
        farm__in=farms,
        transaction_type='expense',
        date__year=timezone.now().year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    net_profit = total_revenue - total_expenses
    
    # Top selling products
    top_products = ProductListing.objects.filter(
        seller__in=farms,
        status='sold'
    ).values('product_name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_revenue')[:5]
    
    return render(request, 'reports/dashboard.html', {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
        'top_products': top_products
    })


@login_required
def financial_report(request):
    """Detailed financial report"""
    farms = Farm.objects.filter(owner=request.user)
    
    # Monthly breakdown
    monthly_data = []
    for month in range(1, 13):
        revenue = Transaction.objects.filter(
            farm__in=farms,
            transaction_type='income',
            date__year=timezone.now().year,
            date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        expenses = Transaction.objects.filter(
            farm__in=farms,
            transaction_type='expense',
            date__year=timezone.now().year,
            date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        monthly_data.append({
            'month': month,
            'revenue': revenue,
            'expenses': expenses,
            'profit': revenue - expenses
        })
    
    return render(request, 'reports/financial.html', {'monthly_data': monthly_data})


@login_required
def crop_yield_report(request):
    """Crop yield report"""
    crops = CropSeason.objects.filter(field__farm__owner=request.user)
    
    # Group by crop type
    crop_summary = crops.values('crop_type__name').annotate(
        total_planted_area=Sum('field__area_hectares'),
        total_harvested_kg=Sum('harvests__quantity_kg'),
        avg_yield_kg_per_ha=Avg('harvests__quantity_kg') / Sum('field__area_hectares')
    )
    
    return render(request, 'reports/crop_yield.html', {'crop_summary': crop_summary})


@login_required
def livestock_report(request):
    """Livestock report"""
    animals = Animal.objects.filter(farm__owner=request.user)
    
    # Summary by species
    species_summary = animals.values('animal_type__species').annotate(
        total_count=Count('id'),
        male_count=Count('id', filter=Q(gender='male')),
        female_count=Count('id', filter=Q(gender='female')),
        alive_count=Count('id', filter=Q(status='alive'))
    )
    
    return render(request, 'reports/livestock.html', {'species_summary': species_summary})


@login_required
def export_report(request, report_type):
    """Export report as CSV"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{report_type}_report.csv"'
    
    writer = csv.writer(response)
    
    if report_type == 'financial':
        writer.writerow(['Date', 'Type', 'Category', 'Amount', 'Description'])
        transactions = Transaction.objects.filter(farm__owner=request.user)
        for t in transactions:
            writer.writerow([t.date, t.transaction_type, t.category, t.amount, t.description])
    
    elif report_type == 'crop':
        writer.writerow(['Crop', 'Field', 'Planting Date', 'Harvest Date', 'Yield (kg)', 'Revenue'])
        crops = CropSeason.objects.filter(field__farm__owner=request.user)
        for c in crops:
            writer.writerow([c.crop_type.name, c.field.name, c.planting_date, c.actual_harvest_date, c.actual_yield_kg, c.actual_revenue])
    
    return response


# ============================================================
# API ENDPOINTS (AJAX)
# ============================================================

@login_required
def api_farms(request):
    """API endpoint for farms"""
    farms = Farm.objects.filter(owner=request.user).values('id', 'name')
    return JsonResponse(list(farms), safe=False)


@login_required
def api_fields(request, farm_id):
    """API endpoint for fields"""
    fields = Field.objects.filter(farm_id=farm_id, farm__owner=request.user).values('id', 'name', 'area_hectares')
    return JsonResponse(list(fields), safe=False)


@login_required
def api_weather(request, farm_id):
    """API endpoint for real weather data"""
    farm = get_object_or_404(Farm, pk=farm_id)
    
    # Check permissions
    if farm.owner != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    weather_data = WeatherData.objects.filter(farm=farm).first()
    
    if weather_data:
        weather_dict = {
            'temperature': weather_data.temperature,
            'feels_like': weather_data.feels_like,
            'condition': weather_data.condition,
            'description': weather_data.description,
            'humidity': weather_data.humidity,
            'pressure': weather_data.pressure,
            'wind_speed': weather_data.wind_speed,
            'wind_direction': weather_data.wind_direction,
            'cloudiness': weather_data.cloudiness,
            'location': weather_data.location,
            'last_updated': weather_data.last_updated.isoformat(),
            'is_stale': weather_data.is_stale(),
            'forecast': weather_data.forecast_data.get('forecast', [])
        }
    else:
        weather_dict = {
            'error': 'No weather data available',
            'message': 'Weather data is being fetched. Please ensure farm has coordinates set.'
        }
    
    return JsonResponse(weather_dict)


@login_required
def api_notifications(request):
    """API endpoint for notifications"""
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).order_by('-created_at')[:10]
    
    data = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'link': n.link,
            'created_at': n.created_at.isoformat()
        }
        for n in notifications
    ]
    
    return JsonResponse(data, safe=False)


@login_required
def notification_list(request):
    """View all notifications"""
    page = request.GET.get('page', 1)
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(notifications, 20)
    page_obj = paginator.get_page(page)
    
    # Mark page notifications as read if not already
    unread_ids = [n.id for n in page_obj if not n.is_read]
    if unread_ids:
        Notification.objects.filter(id__in=unread_ids).update(is_read=True)
    
    return render(request, 'notifications/list.html', {
        'page_obj': page_obj,
        'notifications': page_obj
    })


@login_required
def mark_notification_read(request, pk):
    """Mark a notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('core:notification_list')


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('core:notification_list')


# ============================================================
# FEATURE 10: FARMER NETWORK & KNOWLEDGE SHARING
# ============================================================

@login_required
def forum_list(request):
    """List all discussion forums"""
    forums = DiscussionForum.objects.filter(is_active=True)
    
    # Calculate statistics
    total_forums = forums.count()
    total_members = sum(f.member_count for f in forums)
    total_threads = sum(f.post_count for f in forums)
    total_posts = ForumThread.objects.filter(forum__is_active=True).count()
    
    context = {
        'forums': forums,
        'total_forums': total_forums,
        'total_members': total_members,
        'total_threads': total_threads,
        'total_posts': total_posts,
    }
    return render(request, 'community/forums.html', context)


@login_required
def forum_create(request):
    """Create new discussion forum (admin only)"""
    if not request.user.is_staff:
        return redirect('core:forum_list')
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category = request.POST.get('category')
        forum = DiscussionForum.objects.create(title=title, description=description, category=category)
        return redirect('core:forum_detail', pk=forum.id)
    return render(request, 'community/forum_form.html')


@login_required
def forum_detail(request, pk):
    """View forum details and threads"""
    forum = get_object_or_404(DiscussionForum, pk=pk)
    threads = forum.threads.all().order_by('-is_pinned', '-created_at')
    context = {'forum': forum, 'threads': threads}
    return render(request, 'community/forum_detail.html', context)


@login_required
def forum_threads(request, forum_id):
    """List forum threads"""
    forum = get_object_or_404(DiscussionForum, pk=forum_id)
    threads = forum.threads.all()
    context = {'forum': forum, 'threads': threads}
    return render(request, 'community/forum_threads.html', context)


@login_required
def thread_create(request, forum_id):
    """Create new forum thread"""
    forum = get_object_or_404(DiscussionForum, pk=forum_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        thread = ForumThread.objects.create(forum=forum, author=request.user, title=title, content=content)
        return redirect('core:thread_detail', pk=thread.id)
    return render(request, 'community/thread_form.html', {'forum': forum})


@login_required
def thread_detail(request, pk):
    """View thread and replies"""
    thread = get_object_or_404(ForumThread, pk=pk)
    replies = thread.replies.all()
    thread.view_count += 1
    thread.save()
    context = {'thread': thread, 'replies': replies}
    return render(request, 'community/thread_detail.html', context)


@login_required
def reply_create(request, thread_id):
    """Add reply to thread"""
    thread = get_object_or_404(ForumThread, pk=thread_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        reply = ForumReply.objects.create(thread=thread, author=request.user, content=content)
        thread.reply_count += 1
        thread.save()
        return redirect('core:thread_detail', pk=thread.id)
    return render(request, 'community/reply_form.html', {'thread': thread})


@login_required
def group_buying_list(request):
    """List group buying initiatives"""
    initiatives = GroupBuyingInitiative.objects.all().order_by('-start_date')
    context = {'initiatives': initiatives}
    return render(request, 'community/group_buying_list.html', context)


@login_required
def group_buying_create(request):
    """Create new group buying initiative"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        product_type = request.POST.get('product_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        initiative = GroupBuyingInitiative.objects.create(
            title=title, description=description, product_type=product_type,
            start_date=start_date, end_date=end_date, organizer=request.user.username,
            organizer_contact=request.user.email, status='open',
            minimum_order_quantity=1, quantity_unit='unit',
            unit_price_with_group=0, unit_price_without_group=0, discount_percent=0
        )
        return redirect('core:group_buying_detail', pk=initiative.id)
    return render(request, 'community/group_buying_form.html')


@login_required
def group_buying_detail(request, pk):
    """View group buying initiative details"""
    initiative = get_object_or_404(GroupBuyingInitiative, pk=pk)
    participants = initiative.participants.all()
    context = {'initiative': initiative, 'participants': participants}
    return render(request, 'community/group_buying_detail.html', context)


@login_required
def group_buying_join(request, initiative_id):
    """Join group buying initiative"""
    initiative = get_object_or_404(GroupBuyingInitiative, pk=initiative_id)
    if request.method == 'POST':
        quantity = Decimal(request.POST.get('quantity', 1))
        participant, created = GroupBuyingParticipant.objects.get_or_create(
            initiative=initiative, farmer=request.user, defaults={'quantity_pledged': quantity}
        )
        if not created:
            participant.quantity_pledged = quantity
            participant.save()
        initiative.farmers_joined += 1
        initiative.total_quantity_pledged += quantity
        initiative.save()
        messages.success(request, 'Successfully joined group buying initiative!')
        return redirect('core:group_buying_detail', pk=initiative.id)
    return render(request, 'community/group_buying_join.html', {'initiative': initiative})


# ============================================================
# FEATURE 11: CARBON FOOTPRINT TRACKER
# ============================================================

@login_required
def carbon_tracker(request):
    """View carbon footprint tracker dashboard"""
    farms = request.user.farms.all()
    records = EmissionRecord.objects.filter(farm__in=farms)
    sources = EmissionSource.objects.filter(farm__in=farms)
    context = {'farms': farms, 'records': records, 'sources': sources}
    return render(request, 'carbon/tracker.html', context)


@login_required
def emission_record_create(request):
    """Create emission record"""
    farms = request.user.farms.all()
    if request.method == 'POST':
        farm_id = request.POST.get('farm')
        source_id = request.POST.get('source')
        quantity = request.POST.get('quantity')
        description = request.POST.get('description', '')
        
        farm = get_object_or_404(Farm, pk=farm_id, owner=request.user)
        source = get_object_or_404(EmissionSource, pk=source_id, farm=farm)
        
        try:
            quantity_decimal = Decimal(quantity)
        except:
            messages.error(request, 'Invalid quantity entered.')
            return redirect('core:emission_record_create')
        
        calculations_emissions = quantity_decimal * source.emission_factor
        EmissionRecord.objects.create(
            farm=farm, 
            source=source, 
            record_date=timezone.now().date(),
            quantity_used=quantity_decimal, 
            calculated_emissions_kg_co2e=calculations_emissions,
            description=description
        )
        messages.success(request, f'Emission record added successfully! Recorded {calculations_emissions:.2f} kg CO₂e emissions.')
        return redirect('core:carbon_tracker')
    
    context = {
        'farms': farms, 
        'sources': EmissionSource.objects.filter(farm__in=farms).order_by('source_type', 'name')
    }
    return render(request, 'carbon/emission_record_form.html', context)


@login_required
def carbon_report(request):
    """View carbon footprint reports"""
    from datetime import datetime
    
    farms = request.user.farms.all()
    reports = CarbonFootprintReport.objects.filter(farm__in=farms)
    
    # Generate list of available years (from 2020 to current year)
    current_year = datetime.now().year
    available_years = list(range(2020, current_year + 1))[::-1]  # Reverse to show newest first
    
    # Get report for selected period
    period = request.GET.get('period', 'monthly')
    year = request.GET.get('year', current_year)
    
    report = None
    if period and year:
        try:
            year = int(year)
            if period == 'monthly':
                # For monthly, get the latest month of that year
                report = reports.filter(year=year, report_period='monthly').order_by('-month').first()
            elif period == 'yearly':
                report = reports.filter(year=year, report_period='yearly').first()
        except (ValueError, TypeError):
            pass
    
    context = {
        'farms': farms, 
        'reports': reports,
        'available_years': available_years,
        'report': report,
        'selected_period': period,
        'selected_year': year,
        'export_url': reverse('core:export_carbon_report'),
    }
    return render(request, 'carbon/report.html', context)


@login_required
def carbon_report_detail(request, pk):
    """View detailed carbon report"""
    report = get_object_or_404(CarbonFootprintReport, pk=pk)
    if report.farm.owner != request.user:
        return redirect('core:carbon_report')
    context = {'report': report}
    return render(request, 'carbon/report_detail.html', context)


@login_required
def emission_source_create(request):
    """Create emission source for farm"""
    farms = request.user.farms.all()
    if request.method == 'POST':
        farm_id = request.POST.get('farm')
        farm = get_object_or_404(Farm, pk=farm_id, owner=request.user)
        source_type = request.POST.get('source_type')
        name = request.POST.get('name')
        emission_factor = Decimal(request.POST.get('emission_factor', 0))
        EmissionSource.objects.create(
            farm=farm,
            source_type=source_type,
            name=name,
            emission_factor=emission_factor,
            unit=request.POST.get('unit', 'kg')
        )
        messages.success(request, 'Emission source added successfully!')
        return redirect('core:carbon_tracker')
    context = {'farms': farms}
    return render(request, 'carbon/emission_source_form.html', context)


@login_required
def sequestration_create(request):
    """Create carbon sequestration activity"""
    farms = request.user.farms.all()
    if request.method == 'POST':
        farm_id = request.POST.get('farm')
        activity_type = request.POST.get('activity_type')
        name = request.POST.get('name')
        farm = get_object_or_404(Farm, pk=farm_id, owner=request.user)
        CarbonSequestration.objects.create(
            farm=farm, activity_type=activity_type, name=name,
            description=request.POST.get('description', ''),
            annual_sequestration_kg_co2e=Decimal(request.POST.get('sequestration', 0)),
            start_date=timezone.now().date()
        )
        messages.success(request, 'Sequestration activity added!')
        return redirect('core:carbon_tracker')
    context = {'farms': farms}
    return render(request, 'carbon/sequestration_form.html', context)


# ============================================================
# FEATURE 12: FARM MAPPING & GEOFENCING
# ============================================================

@login_required
def farm_map(request):
    """Enhanced farm map view with all data"""
    
    farms = Farm.objects.filter(owner=request.user)
    
    # Prepare farms data for map
    farms_data = []
    for farm in farms:
        farms_data.append({
            'id': farm.id,
            'name': farm.name,
            'lat': float(farm.latitude) if farm.latitude else None,
            'lon': float(farm.longitude) if farm.longitude else None,
            'address': farm.address,
            'total_area_hectares': float(farm.total_area_hectares) if farm.total_area_hectares else None,
        })
    
    # Prepare fields data
    fields_data = []
    for field in Field.objects.filter(farm__owner=request.user):
        fields_data.append({
            'id': field.id,
            'name': field.name,
            'farm_name': field.farm.name,
            'area_hectares': float(field.area_hectares) if field.area_hectares else None,
            'soil_type': field.soil_type,
            'boundary': field.boundary if field.boundary else None,
        })
    
    # Prepare livestock data with real-time locations
    livestock_data = []
    for animal in Animal.objects.filter(farm__owner=request.user, status='alive'):
        # Get latest location from LivestockLocation tracking
        latest_location = animal.location_history.order_by('-recorded_at').first()
        
        livestock_data.append({
            'id': animal.id,
            'name': animal.name,
            'tag_number': animal.tag_number,
            'breed': animal.animal_type.breed if hasattr(animal, 'animal_type') else None,
            'lat': float(latest_location.latitude) if latest_location else None,
            'lon': float(latest_location.longitude) if latest_location else None,
            'last_updated': latest_location.recorded_at.strftime('%Y-%m-%d %H:%M') if latest_location else animal.updated_at.strftime('%Y-%m-%d %H:%M'),
            'accuracy_meters': latest_location.accuracy_meters if latest_location else None,
            'is_inside_geofence': latest_location.is_inside_assigned_geofence if latest_location else None,
        })
    
    # Prepare geofences data
    geofences_data = []
    for geofence in Geofence.objects.filter(farm__owner=request.user):
        geofences_data.append({
            'id': geofence.id,
            'name': geofence.name,
            'is_active': geofence.is_active,
            'enable_exit_alerts': geofence.enable_exit_alerts,
            'enable_entry_alerts': geofence.enable_entry_alerts,
            'alert_channels': geofence.alert_channels,
            'boundary': geofence.geojson_boundary if geofence.geojson_boundary else None,
        })
    
    context = {
        'farms_data': json.dumps(farms_data),
        'fields_data': json.dumps(fields_data),
        'livestock_data': json.dumps(livestock_data),
        'geofences_data': json.dumps(geofences_data),
    }
    
    return render(request, 'mapping/farm_map.html', context)


@login_required
def farm_boundary_detail(request, farm_id):
    """View farm boundary details"""
    farm = get_object_or_404(Farm, pk=farm_id, owner=request.user)
    boundary = getattr(farm, 'boundary', None)
    context = {'farm': farm, 'boundary': boundary}
    return render(request, 'mapping/boundary_detail.html', context)


@login_required
def geofence_list(request):
    """List geofences"""
    farms = request.user.farms.all()
    geofences = Geofence.objects.filter(farm__in=farms)
    context = {'geofences': geofences}
    return render(request, 'mapping/geofence_list.html', context)


@login_required
def geofence_create(request):
    """Create a new geofence"""
    
    farms = Farm.objects.filter(owner=request.user)
    
    if request.method == 'POST':
        farm = farms.first()
        geofence = Geofence.objects.create(
            farm=farm,
            name=request.POST.get('name'),
            geojson_boundary=request.POST.get('geojson_boundary'),
            enable_exit_alerts=request.POST.get('enable_exit_alerts') == 'on',
            enable_entry_alerts=request.POST.get('enable_entry_alerts') == 'on',
            alert_channels=['sms', 'email'] if request.POST.get('alert_channels') else [],
        )
        
        field_id = request.POST.get('field')
        if field_id:
            geofence.field_id = field_id
            geofence.save()
        
        livestock_ids = request.POST.getlist('livestock')
        if livestock_ids:
            geofence.assigned_livestock.set(livestock_ids)
        
        messages.success(request, f'Geofence "{geofence.name}" created successfully!')
        return redirect('farm_map')
    
    context = {
        'fields': Field.objects.filter(farm__owner=request.user),
        'livestock': Animal.objects.filter(farm__owner=request.user, status='alive'),
        'farm_lat': farms.first().latitude if farms.first() and farms.first().latitude else -1.286389,
        'farm_lon': farms.first().longitude if farms.first() and farms.first().longitude else 36.817223,
    }
    
    return render(request, 'geofence/create.html', context)


@login_required
def geofence_detail(request, pk):
    """View geofence details"""
    geofence = get_object_or_404(Geofence, pk=pk)
    if geofence.farm.owner != request.user:
        return redirect('core:geofence_list')
    context = {'geofence': geofence}
    return render(request, 'mapping/geofence_detail.html', context)


@login_required
def geofence_edit(request, pk):
    """Edit geofence"""
    geofence = get_object_or_404(Geofence, pk=pk)
    if geofence.farm.owner != request.user:
        return redirect('core:geofence_list')
    if request.method == 'POST':
        geofence.name = request.POST.get('name', geofence.name)
        geofence.enable_exit_alerts = request.POST.get('enable_exit_alerts') == 'on'
        geofence.save()
        messages.success(request, 'Geofence updated successfully!')
        return redirect('core:geofence_detail', pk=geofence.id)
    context = {'geofence': geofence}
    return render(request, 'mapping/geofence_form.html', context)


@login_required
def livestock_tracking(request):
    """Real-time livestock tracking map view"""
    
    farms = Farm.objects.filter(owner=request.user)
    farm = farms.first()
    
    livestock = Animal.objects.filter(
        farm__owner=request.user, 
        status='alive'
    ).select_related('animal_type')
    
    livestock_data = []
    active_tracking = 0
    inside_geofence = 0
    outside_geofence = 0
    
    for animal in livestock:
        last_location = None
        if hasattr(animal, 'last_location'):
            last_location = animal.last_location
        
        is_outside = False
        if last_location and hasattr(animal, 'assigned_geofence'):
            is_outside = not is_point_in_geofence(
                last_location.latitude, 
                last_location.longitude, 
                animal.assigned_geofence
            )
        
        if last_location:
            active_tracking += 1
            if is_outside:
                outside_geofence += 1
            else:
                inside_geofence += 1
        
        livestock_data.append({
            'id': animal.id,
            'name': animal.name or animal.tag_number,
            'tag_number': animal.tag_number,
            'breed': animal.animal_type.breed if animal.animal_type else None,
            'gender': animal.get_gender_display(),
            'latitude': float(last_location.latitude) if last_location else None,
            'longitude': float(last_location.longitude) if last_location else None,
            'last_updated': last_location.recorded_at.strftime('%Y-%m-%d %H:%M:%S') if last_location else None,
            'is_outside': is_outside,
        })
    
    geofences_data = []
    for geofence in Geofence.objects.filter(farm__owner=request.user, is_active=True):
        geofences_data.append({
            'id': geofence.id,
            'name': geofence.name,
            'is_active': geofence.is_active,
            'enable_exit_alerts': geofence.enable_exit_alerts,
            'enable_entry_alerts': geofence.enable_entry_alerts,
            'boundary': geofence.geojson_boundary,
        })
    
    context = {
        'total_livestock': livestock.count(),
        'active_tracking': active_tracking,
        'inside_geofence': inside_geofence,
        'outside_geofence': outside_geofence,
        'livestock': livestock,
        'livestock_data': json.dumps(livestock_data),
        'geofences_data': json.dumps(geofences_data),
        'farm_lat': float(farm.latitude) if farm and farm.latitude else -1.286389,
        'farm_lon': float(farm.longitude) if farm and farm.longitude else 36.817223,
    }
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.GET.get('ajax'):
        return JsonResponse({'livestock': livestock_data})
    
    return render(request, 'maps/livestock_tracking.html', context)


@login_required
def livestock_locations(request, livestock_id):
    """View livestock location history"""
    livestock = get_object_or_404(Animal, pk=livestock_id)
    if livestock.farm.owner != request.user:
        return redirect('core:livestock_tracking')
    locations = livestock.location_history.all().order_by('-recorded_at')[:100]
    context = {'livestock': livestock, 'locations': locations}
    return render(request, 'mapping/livestock_locations.html', context)


def is_point_in_geofence(lat, lng, geofence):
    """Check if a point is inside a geofence polygon"""
    if not geofence or not geofence.geojson_boundary:
        return True
    
    try:
        from shapely.geometry import Point, Polygon
        
        boundary = geofence.geojson_boundary if isinstance(geofence.geojson_boundary, dict) else json.loads(geofence.geojson_boundary) if isinstance(geofence.geojson_boundary, str) else geofence.geojson_boundary
        if isinstance(boundary, str):
            boundary = json.loads(boundary)
        
        coords = boundary['coordinates'][0]
        polygon = Polygon([(c[1], c[0]) for c in coords])
        point = Point(lat, lng)
        return polygon.contains(point)
    except Exception:
        return True


@login_required
def geofence_alerts(request, geofence_id=None):
    """View alerts for a specific geofence"""
    
    if geofence_id:
        geofence = get_object_or_404(Geofence, id=geofence_id, farm__owner=request.user)
        alerts = GeofenceAlert.objects.filter(geofence=geofence).order_by('-alert_time')
    else:
        farms = Farm.objects.filter(owner=request.user)
        alerts = GeofenceAlert.objects.filter(geofence__farm__in=farms).order_by('-alert_time')
        geofence = None
    
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    
    if status_filter == 'unresolved':
        alerts = alerts.filter(is_resolved=False)
    if type_filter == 'exit':
        alerts = alerts.filter(alert_type='exit')
    elif type_filter == 'entry':
        alerts = alerts.filter(alert_type='entry')
    
    paginator = Paginator(alerts, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    total_alerts = alerts.count()
    unresolved_count = alerts.filter(is_resolved=False).count()
    exit_alerts_count = alerts.filter(alert_type='exit').count()
    entry_alerts_count = alerts.filter(alert_type='entry').count()
    
    alert_timeline = []
    for alert in alerts[:10]:
        alert_timeline.append({
            'type': alert.alert_type,
            'title': f"{'Exit' if alert.alert_type == 'exit' else 'Entry'} Alert - {alert.livestock.name}",
            'description': f"Animal moved {'outside' if alert.alert_type == 'exit' else 'inside'} geofence boundary",
            'time': alert.alert_time
        })
    
    context = {
        'geofence': geofence,
        'alerts': page_obj,
        'total_alerts': total_alerts,
        'unresolved_count': unresolved_count,
        'exit_alerts_count': exit_alerts_count,
        'entry_alerts_count': entry_alerts_count,
        'alert_timeline': alert_timeline,
    }
    
    return render(request, 'geofence/alerts.html', context)


@login_required
def resolve_geofence_alert(request, alert_id):
    """Mark an alert as resolved"""
    
    alert = get_object_or_404(GeofenceAlert, id=alert_id, geofence__farm__owner=request.user)
    
    if request.method == 'POST':
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolution_notes = request.POST.get('resolution_notes', '')
        alert.save()
        
        messages.success(request, f'Alert for {alert.livestock.name} marked as resolved.')
        
        Notification.objects.create(
            user=request.user,
            notification_type='success',
            title='Alert Resolved',
            message=f'Geofence alert for {alert.livestock.name} has been resolved.',
            link=f'/geofence/alerts/{alert.geofence.id}/'
        )
    
    return redirect('geofence_alerts', geofence_id=alert.geofence.id)


@login_required
def save_map_drawing(request):
    """Save drawn polygon/marker to database (AJAX endpoint)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            draw_type = data.get('type', 'polygon')
            geometry = json.loads(data.get('geometry', '[]'))
            
            if not geometry:
                return JsonResponse({'success': False, 'error': 'No geometry provided'})
            
            # Get the first farm or prompt user to select one
            farms = request.user.farms.all()
            if not farms.exists():
                return JsonResponse({'success': False, 'error': 'No farms found'})
            
            farm = farms.first()
            
            # Save as Geofence if polygon
            if draw_type == 'polygon' and geometry:
                geofence_name = f"Drawing {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                geom = geometry[0].get('geometry', {})
                
                if geom.get('type') == 'Polygon':
                    coordinates = geom.get('coordinates', [])
                    geofence = Geofence.objects.create(
                        farm=farm,
                        name=geofence_name,
                        geojson_boundary=json.dumps(coordinates),
                        enable_exit_alerts=True
                    )
                    return JsonResponse({
                        'success': True, 
                        'message': f'Geofence "{geofence_name}" created successfully',
                        'geofence_id': geofence.id
                    })
            
            return JsonResponse({'success': False, 'error': 'Unsupported drawing type'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


@login_required
def set_geofence_alert(request, id):
    """Set alert for geofence (AJAX endpoint)"""
    if request.method == 'POST':
        try:
            geofence = get_object_or_404(Geofence, pk=id, farm__owner=request.user)
            geofence.enable_exit_alerts = True
            geofence.save()
            
            return JsonResponse({
                'success': True,
                'message': f'Exit alert enabled for "{geofence.name}"'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=400)


# ============================================================
# FEATURE 13: OFFLINE SYNC & DATA MANAGEMENT
# ============================================================

@login_required
def sync_dashboard(request):
    """Sync management dashboard"""
    sync_queue = OfflineSyncQueue.objects.filter(user=request.user).order_by('-created_at')
    conflicts = SyncConflict.objects.filter(sync_entry__user=request.user).order_by('-created_at')
    
    # Calculate statistics
    pending_count = sync_queue.filter(is_synced=False).count()
    synced_count = sync_queue.filter(is_synced=True).count()
    conflict_count = conflicts.filter(resolution_status='pending').count()
    
    # Get last sync time
    last_synced = sync_queue.filter(is_synced=True).first()
    last_sync = last_synced.sync_attempted_at if last_synced else None
    
    context = {
        'sync_queue': sync_queue,
        'conflicts': conflicts,
        'pending_count': pending_count,
        'synced_count': synced_count,
        'conflict_count': conflict_count,
        'last_sync': last_sync,
    }
    return render(request, 'sync/dashboard.html', context)


@login_required
def sync_queue(request):
    """View sync queue status"""
    queue_items = OfflineSyncQueue.objects.filter(user=request.user).order_by('-created_at')
    unsynced = queue_items.filter(is_synced=False).count()
    synced = queue_items.filter(is_synced=True).count()
    context = {
        'queue_items': queue_items,
        'unsynced_count': unsynced,
        'synced_count': synced,
        'pending_count': unsynced,
    }
    return render(request, 'sync/queue.html', context)


@login_required
def sync_conflicts(request):
    """View and manage sync conflicts"""
    conflicts = SyncConflict.objects.filter(sync_entry__user=request.user).order_by('-created_at')
    pending = conflicts.filter(resolution_status='pending').count()
    context = {
        'conflicts': conflicts,
        'pending_count': pending,
        'resolved_count': conflicts.filter(resolution_status__startswith='resolved').count(),
    }
    return render(request, 'sync/conflicts.html', context)


@login_required
def resolve_sync_conflict(request, pk):
    """Resolve individual sync conflict"""
    conflict = get_object_or_404(SyncConflict, pk=pk)
    if conflict.sync_entry.user != request.user:
        return redirect('core:sync_conflicts')
    if request.method == 'POST':
        choice = request.POST.get('resolution_choice')
        conflict.resolution_status = 'resolved_manual'
        conflict.resolved_by = request.user
        conflict.resolved_data = conflict.server_version if choice == 'server' else conflict.local_version
        conflict.save()
        messages.success(request, 'Conflict resolved!')
        return redirect('core:sync_conflicts')
    context = {'conflict': conflict}
    return render(request, 'sync/resolve_conflict.html', context)


@login_required
def retry_sync(request, pk):
    """Retry sync for queue item"""
    sync_item = get_object_or_404(OfflineSyncQueue, pk=pk)
    if sync_item.user != request.user:
        return redirect('core:sync_queue')
    sync_item.is_synced = False
    sync_item.sync_error = ''
    sync_item.sync_attempted_at = None
    sync_item.save()
    messages.success(request, 'Sync retry scheduled!')
    return redirect('core:sync_queue')


# ============================================================
# REMINDERS - FARM ACTIVITY REMINDERS
# ============================================================

@login_required
def reminder_list(request):
    """List all reminders for user's farms"""
    farms = request.user.farms.all()
    reminders = Reminder.objects.filter(
        farm__in=farms
    ).select_related('farm').order_by('-due_date')
    
    # Filter by status
    status = request.GET.get('status', 'active')
    if status == 'completed':
        reminders = reminders.filter(is_completed=True)
    elif status == 'pending':
        reminders = reminders.filter(is_completed=False, is_active=True)
    elif status == 'overdue':
        reminders = reminders.filter(
            is_completed=False, 
            is_active=True,
            due_date__lt=timezone.now().date()
        )
    else:  # 'active'
        reminders = reminders.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(reminders, 20)
    page_number = request.GET.get('page')
    reminders = paginator.get_page(page_number)
    
    context = {
        'reminders': reminders,
        'status': status,
        'farms': farms,
        'export_url': reverse('core:export_reminders'),
    }
    return render(request, 'reminders/reminder_list.html', context)


@login_required
def reminder_create(request):
    """Create a new reminder"""
    farms = request.user.farms.all()
    
    if request.method == 'POST':
        farm_id = request.POST.get('farm')
        title = request.POST.get('title')
        reminder_type = request.POST.get('reminder_type', 'general')
        due_date = request.POST.get('due_date')
        is_recurring = request.POST.get('is_recurring') == 'on'
        description = request.POST.get('description', '')
        
        # Validate farm ownership
        farm = get_object_or_404(Farm, pk=farm_id, owner=request.user)
        
        reminder = Reminder.objects.create(
            farm=farm,
            user=request.user,
            title=title,
            reminder_type=reminder_type,
            description=description,
            due_date=due_date,
            is_recurring=is_recurring,
        )
        
        messages.success(request, f'Reminder "{title}" created successfully!')
        return redirect('core:reminder_detail', pk=reminder.pk)
    
    context = {
        'farms': farms,
        'reminder_types': [
            ('vaccination', '💉 Vaccination'),
            ('medication', '💊 Medication'),
            ('breeding', '🧬 Breeding'),
            ('maintenance', '🔧 Equipment Maintenance'),
            ('breeding_check', '🐄 Breeding Check'),
            ('feed_order', '🌾 Feed Order'),
            ('pasture_rotation', '🌱 Pasture Rotation'),
            ('inspection', '📋 Farm Inspection'),
            ('general', '📝 General Task'),
        ]
    }
    return render(request, 'reminders/reminder_form.html', context)


@login_required
def reminder_detail(request, pk):
    """View reminder details"""
    reminder = get_object_or_404(Reminder, pk=pk)
    
    # Check access
    if reminder.farm.owner != request.user:
        return redirect('core:reminder_list')
    
    context = {'reminder': reminder}
    return render(request, 'reminders/reminder_detail.html', context)


@login_required
def reminder_edit(request, pk):
    """Edit a reminder"""
    reminder = get_object_or_404(Reminder, pk=pk)
    
    # Check access
    if reminder.farm.owner != request.user:
        return redirect('core:reminder_list')
    
    if request.method == 'POST':
        reminder.title = request.POST.get('title', reminder.title)
        reminder.reminder_type = request.POST.get('reminder_type', reminder.reminder_type)
        reminder.description = request.POST.get('description', reminder.description)
        reminder.due_date = request.POST.get('due_date', reminder.due_date)
        reminder.is_recurring = request.POST.get('is_recurring') == 'on'
        reminder.is_active = request.POST.get('is_active') == 'on'
        reminder.save()
        
        messages.success(request, 'Reminder updated successfully!')
        return redirect('core:reminder_detail', pk=reminder.pk)
    
    context = {
        'reminder': reminder,
        'farms': [reminder.farm],
        'reminder_types': [
            ('vaccination', '💉 Vaccination'),
            ('medication', '💊 Medication'),
            ('breeding', '🧬 Breeding'),
            ('maintenance', '🔧 Equipment Maintenance'),
            ('breeding_check', '🐄 Breeding Check'),
            ('feed_order', '🌾 Feed Order'),
            ('pasture_rotation', '🌱 Pasture Rotation'),
            ('inspection', '📋 Farm Inspection'),
            ('general', '📝 General Task'),
        ]
    }
    return render(request, 'reminders/reminder_form.html', context)


@login_required
def reminder_complete(request, pk):
    """Mark reminder as completed"""
    reminder = get_object_or_404(Reminder, pk=pk)
    
    # Check access
    if reminder.farm.owner != request.user:
        return redirect('core:reminder_list')
    
    reminder.is_completed = True
    reminder.completed_at = timezone.now()
    reminder.save()
    
    messages.success(request, f'Reminder "{reminder.title}" marked as completed!')
    return redirect('core:reminder_list')


@login_required
def reminder_delete(request, pk):
    """Delete a reminder"""
    reminder = get_object_or_404(Reminder, pk=pk)
    
    # Check access
    if reminder.farm.owner != request.user:
        return redirect('core:reminder_list')
    
    title = reminder.title
    reminder.delete()
    
    messages.success(request, f'Reminder "{title}" has been deleted!')
    return redirect('core:reminder_list')


@login_required
@login_required
def reminder_dashboard(request):
    """Dashboard showing upcoming reminders"""
    farms = request.user.farms.all()
    today = timezone.now().date()
    
    # Get upcoming reminders (next 30 days)
    upcoming = Reminder.objects.filter(
        farm__in=farms,
        is_active=True,
        is_completed=False,
        due_date__gte=today,
        due_date__lte=today + timedelta(days=30)
    ).order_by('due_date')
    
    # Get overdue reminders
    overdue = Reminder.objects.filter(
        farm__in=farms,
        is_active=True,
        is_completed=False,
        due_date__lt=today
    ).order_by('due_date')
    
    context = {
        'upcoming': upcoming[:10],
        'overdue': overdue,
        'total_farms': farms.count(),
    }
    return render(request, 'reminders/reminder_dashboard.html', context)


# ============================================================
# FARM PROJECTS VIEWS
# ============================================================

@login_required
def project_dashboard(request):
    """View all projects and their status across user's farms"""
    farms = Farm.objects.filter(owner=request.user)
    projects = FarmProject.objects.filter(farm__in=farms).order_by('-created_at')
    
    # Get statistics
    stats = {
        'total': projects.count(),
        'active': projects.filter(status__in=['planning', 'in_progress']).count(),
        'completed': projects.filter(status='completed').count(),
        'total_budget': projects.aggregate(Sum('budget'))['budget__sum'] or 0,
    }
    
    # Pagination
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'projects': page_obj.object_list,
        'stats': stats,
    }
    return render(request, 'projects/dashboard.html', context)


@login_required
def project_list(request):
    """List all projects with filters"""
    farms = Farm.objects.filter(owner=request.user)
    projects = FarmProject.objects.filter(farm__in=farms)
    
    # Filters
    farm_id = request.GET.get('farm')
    category = request.GET.get('category')
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    
    if farm_id:
        projects = projects.filter(farm_id=farm_id)
    if category:
        projects = projects.filter(category=category)
    if status:
        projects = projects.filter(status=status)
    if priority:
        projects = projects.filter(priority=priority)
    
    projects = projects.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(projects, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'projects': page_obj.object_list,
        'farms': farms,
        'categories': FarmProject.CATEGORIES,
        'statuses': FarmProject.STATUS,
        'priorities': FarmProject.PRIORITY,
    }
    return render(request, 'projects/list.html', context)


@login_required
def project_create(request):
    """Create a new project"""
    farms = Farm.objects.filter(owner=request.user)
    
    if request.method == 'POST':
        form = FarmProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            # Verify farm belongs to user
            if project.farm.owner != request.user:
                messages.error(request, 'You do not have permission to create a project for this farm.')
                return redirect('core:project_list')
            project.save()
            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('core:project_detail', pk=project.id)
    else:
        form = FarmProjectForm()
        # Filter farms to user's farms
        form.fields['farm'].queryset = farms
    
    context = {'form': form, 'title': 'Create New Project'}
    return render(request, 'projects/form.html', context)


@login_required
def project_detail(request, pk):
    """View project details with tasks, resources, and milestones"""
    project = get_object_or_404(FarmProject, pk=pk)
    
    # Permission check
    if project.farm.owner != request.user:
        messages.error(request, 'You do not have permission to view this project.')
        return redirect('core:dashboard')
    
    # Get related data
    tasks = project.tasks.all().order_by('-created_at')
    resources = project.resources.all().order_by('created_at')
    milestones = project.milestones.all().order_by('target_date')
    
    # Calculate statistics
    task_stats = {
        'total': tasks.count(),
        'completed': tasks.filter(completed=True).count(),
        'pending': tasks.filter(completed=False).count(),
    }
    
    milestone_stats = {
        'total': milestones.count(),
        'achieved': milestones.filter(achieved_date__isnull=False).count(),
    }
    
    resource_costs = resources.aggregate(total=Sum('cost'))['total'] or 0
    
    context = {
        'project': project,
        'tasks': tasks,
        'resources': resources,
        'milestones': milestones,
        'task_stats': task_stats,
        'milestone_stats': milestone_stats,
        'resource_costs': resource_costs,
    }
    return render(request, 'projects/detail.html', context)


@login_required
def project_edit(request, pk):
    """Edit an existing project"""
    project = get_object_or_404(FarmProject, pk=pk)
    
    # Permission check
    if project.farm.owner != request.user:
        messages.error(request, 'You do not have permission to edit this project.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = FarmProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.name}" updated successfully!')
            return redirect('core:project_detail', pk=project.id)
    else:
        form = FarmProjectForm(instance=project)
    
    context = {'form': form, 'project': project, 'title': f'Edit {project.name}'}
    return render(request, 'projects/form.html', context)


@login_required
def project_delete(request, pk):
    """Delete a project"""
    project = get_object_or_404(FarmProject, pk=pk)
    
    # Permission check
    if project.farm.owner != request.user:
        messages.error(request, 'You do not have permission to delete this project.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        project_name = project.name
        project.delete()
        messages.success(request, f'Project "{project_name}" deleted successfully!')
        return redirect('core:project_list')
    
    context = {'project': project}
    return render(request, 'projects/confirm_delete.html', context)


@login_required
def project_add_task(request, pk):
    """Add a task to a project"""
    project = get_object_or_404(FarmProject, pk=pk)
    
    # Permission check
    if project.farm.owner != request.user:
        messages.error(request, 'You do not have permission to modify this project.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = ProjectTaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.save()
            
            # Create automatic reminder for task if due date is set
            if task.due_date:
                Reminder.objects.get_or_create(
                    farm=project.farm,
                    user=request.user,
                    title=f'Task: {task.name}',
                    reminder_type='general',
                    due_date=task.due_date,
                    defaults={
                        'is_active': True,
                        'description': f'Task "{task.name}" is due for project "{project.name}". {task.description if task.description else ""}'
                    }
                )
            
            messages.success(request, f'Task "{task.name}" added to project!')
            return redirect('core:project_detail', pk=project.id)
    else:
        form = ProjectTaskForm()
    
    context = {'form': form, 'project': project, 'title': 'Add Task'}
    return render(request, 'projects/form.html', context)


@login_required
def project_complete_task(request, pk, task_id):
    """Mark a task as complete"""
    project = get_object_or_404(FarmProject, pk=pk)
    task = get_object_or_404(ProjectTask, pk=task_id, project=project)
    
    # Permission check
    if project.farm.owner != request.user:
        messages.error(request, 'You do not have permission to modify this project.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        task.status = 'completed'
        task.completed_date = timezone.now()
        task.save()
        messages.success(request, f'Task "{task.name}" marked as complete!')
        return redirect('core:project_detail', pk=project.id)
    
    context = {'task': task, 'project': project}
    return render(request, 'projects/confirm_complete_task.html', context)


@login_required
def project_add_resource(request, pk):
    """Add a resource allocation to a project"""
    project = get_object_or_404(FarmProject, pk=pk)
    
    # Permission check
    if project.farm.owner != request.user:
        messages.error(request, 'You do not have permission to modify this project.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = ProjectResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.project = project
            resource.save()
            messages.success(request, f'Resource "{resource.resource_type}" allocated to project!')
            return redirect('core:project_detail', pk=project.id)
    else:
        form = ProjectResourceForm()
    
    context = {'form': form, 'project': project, 'title': 'Add Resource'}
    return render(request, 'projects/form.html', context)


@login_required
def project_add_milestone(request, pk):
    """Add a milestone to a project"""
    project = get_object_or_404(FarmProject, pk=pk)
    
    # Permission check
    if project.farm.owner != request.user:
        messages.error(request, 'You do not have permission to modify this project.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        form = ProjectMilestoneForm(request.POST)
        if form.is_valid():
            milestone = form.save(commit=False)
            milestone.project = project
            milestone.save()
            
            # Create automatic reminder for milestone
            if milestone.target_date:
                Reminder.objects.get_or_create(
                    farm=project.farm,
                    user=request.user,
                    title=f'Milestone: {milestone.name}',
                    reminder_type='general',
                    due_date=milestone.target_date,
                    defaults={
                        'is_active': True,
                        'description': f'Milestone "{milestone.name}" for project "{project.name}" is due. {milestone.description if milestone.description else ""}'
                    }
                )
            
            messages.success(request, f'Milestone "{milestone.name}" added to project!')
            return redirect('core:project_detail', pk=project.id)
    else:
        form = ProjectMilestoneForm()
    
    context = {'form': form, 'project': project, 'title': 'Add Milestone'}
    return render(request, 'projects/form.html', context)


@login_required
def project_achieve_milestone(request, pk, milestone_id):
    """Mark a milestone as achieved"""
    project = get_object_or_404(FarmProject, pk=pk)
    milestone = get_object_or_404(ProjectMilestone, pk=milestone_id, project=project)
    
    # Permission check
    if project.farm.owner != request.user:
        messages.error(request, 'You do not have permission to modify this project.')
        return redirect('core:dashboard')
    
    if request.method == 'POST':
        milestone.achieved_date = timezone.now()
        milestone.save()
        messages.success(request, f'Milestone "{milestone.name}" marked as achieved!')
        return redirect('core:project_detail', pk=project.id)
    
    context = {'milestone': milestone, 'project': project}
    return render(request, 'projects/confirm_achieve_milestone.html', context)
    
    # Get overdue reminders
    overdue = Reminder.objects.filter(
        farm__in=farms,
        is_active=True,
        is_completed=False,
        due_date__lt=today
    ).order_by('due_date')
    
    # Get completed recently
    completed_recently = Reminder.objects.filter(
        farm__in=farms,
        is_completed=True,
        completed_at__gte=today - timedelta(days=7)
    ).order_by('-completed_at')[:10]
    
    context = {
        'upcoming': upcoming[:10],
        'overdue': overdue,
        'completed_recently': completed_recently,
        'upcoming_count': upcoming.count(),
        'overdue_count': overdue.count(),
    }
    return render(request, 'reminders/reminder_dashboard.html', context)


# ============================================================
# EXPORT FUNCTIONS
# ============================================================

@login_required
def export_crops(request):
    """Export crops data"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        
        format_choice = request.GET.get('format', 'csv')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        logger.info(f"Export request - format: {format_choice}, start_date: {start_date}, end_date: {end_date}")
        
        if start_date:
            try:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            except:
                start_date = None
        
        if end_date:
            try:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            except:
                end_date = None
        
        logger.info(f"Parsed dates - start: {start_date}, end: {end_date}, user: {request.user}")
        
        # Use the SAME query as crop_list to get crops
        from .models import CropSeason
        crops_check = CropSeason.objects.filter(field__farm__owner=request.user)
        
        logger.info(f"Total crops for user: {crops_check.count()}")
        
        if crops_check.count() == 0:
            messages.error(request, 'You do not have any crops to export.')
            return redirect('core:crop_list')
        
        # Apply date filters if provided
        if start_date and end_date:
            crops_check = crops_check.filter(
                planting_date__gte=start_date,
                planting_date__lte=end_date
            )
            logger.info(f"Crops after date filter: {crops_check.count()}")
        
        # Get the farm from the first crop
        if crops_check.exists():
            farm = crops_check.first().field.farm
        else:
            messages.error(request, 'No crops found for the selected date range.')
            return redirect('core:crop_list')
        
        response, filename = ExportService.export_crops(
            farm=farm,
            format=format_choice,
            start_date=start_date,
            end_date=end_date
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        import traceback
        logger.error(f'Error exporting crops: {str(e)} - {traceback.format_exc()}')
        messages.error(request, f'Error exporting crops: {str(e)}')
        return redirect('core:crop_list')


@login_required
@login_required
def export_livestock(request):
    """Export livestock data"""
    try:
        format_choice = request.GET.get('format', 'csv')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        if start_date:
            try:
                start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            except:
                start_date = None
        
        if end_date:
            try:
                end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            except:
                end_date = None
        
        from .models import Animal
        livestock_check = Animal.objects.filter(farm__owner=request.user)
        
        if livestock_check.count() == 0:
            messages.error(request, 'You do not have any livestock to export.')
            return redirect('core:animal_list')
        
        if start_date and end_date:
            livestock_check = livestock_check.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
        
        if livestock_check.exists():
            farm = livestock_check.first().farm
        else:
            messages.error(request, 'No livestock found for the selected date range.')
            return redirect('core:animal_list')
        
        response, filename = ExportService.export_livestock(
            farm=farm,
            format=format_choice,
            start_date=start_date,
            end_date=end_date
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting livestock: {str(e)}')
        return redirect('core:animal_list')


@login_required
def export_equipment(request):
    """Export equipment data"""
    try:
        format_choice = request.GET.get('format', 'csv')
        from .models import Equipment
        
        equipment_check = Equipment.objects.filter(owner=request.user)
        
        if equipment_check.count() == 0:
            messages.error(request, 'You do not have any equipment to export.')
            return redirect('core:equipment_list')
        
        response, filename = ExportService.export_equipment(
            user=request.user,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting equipment: {str(e)}')
        return redirect('core:equipment_list')


@login_required
def export_insurance_policies(request):
    """Export insurance policies"""
    try:
        format_choice = request.GET.get('format', 'csv')
        from .models import InsurancePolicy
        
        policies_check = InsurancePolicy.objects.filter(farm__owner=request.user)
        
        if policies_check.count() == 0:
            messages.error(request, 'You do not have any insurance policies to export.')
            return redirect('core:insurance')
        
        response, filename = ExportService.export_insurance(
            user=request.user,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting insurance policies: {str(e)}')
        return redirect('core:insurance')


@login_required
def export_payroll(request):
    """Export payroll records"""
    try:
        format_choice = request.GET.get('format', 'csv')
        from .models import PayrollRecord
        
        payroll_check = PayrollRecord.objects.filter(farm__owner=request.user)
        
        if payroll_check.count() == 0:
            messages.error(request, 'You do not have any payroll records to export.')
            return redirect('core:payroll_list')
        
        response, filename = ExportService.export_payroll(
            user=request.user,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting payroll: {str(e)}')
        return redirect('core:payroll_list')


@login_required
def export_pest_reports(request):
    """Export pest detection reports"""
    try:
        format_choice = request.GET.get('format', 'csv')
        from .models import PestDetectionReport
        
        pest_check = PestDetectionReport.objects.filter(farm__owner=request.user)
        
        if pest_check.count() == 0:
            messages.error(request, 'You do not have any pest reports to export.')
            return redirect('core:pest_history')
        
        response, filename = ExportService.export_pest_reports(
            user=request.user,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting pest reports: {str(e)}')
        return redirect('core:pest_history')


@login_required
def export_carbon_report(request):
    """Export carbon footprint report"""
    try:
        format_choice = request.GET.get('format', 'csv')
        from .models import CarbonFootprint
        
        carbon_check = CarbonFootprint.objects.filter(farm__owner=request.user)
        
        if carbon_check.count() == 0:
            messages.error(request, 'You do not have any carbon footprint data to export.')
            return redirect('core:carbon_report')
        
        response, filename = ExportService.export_carbon(
            user=request.user,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting carbon report: {str(e)}')
        return redirect('core:carbon_report')


@login_required
def export_reminders(request):
    """Export reminders"""
    try:
        format_choice = request.GET.get('format', 'csv')
        from .models import Reminder
        
        reminders_check = Reminder.objects.filter(farm__owner=request.user)
        
        if reminders_check.count() == 0:
            messages.error(request, 'You do not have any reminders to export.')
            return redirect('core:reminder_list')
        
        response, filename = ExportService.export_reminders(
            user=request.user,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting reminders: {str(e)}')
        return redirect('core:reminder_list')


@login_required
def export_marketplace_products(request):
    """Export marketplace products"""
    try:
        format_choice = request.GET.get('format', 'csv')
        response, filename = ExportService.export_marketplace_products(
            user=request.user,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting marketplace products: {str(e)}')
        return redirect('core:marketplace')