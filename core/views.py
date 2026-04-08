# core/views.py
# FARMWISE - Complete Views for All Functionality

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login
from django.db.models import Sum, Count, Q, Avg
from django.utils import timezone
from django.http import JsonResponse
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
def wallboard(request):
    """System admin wallboard with statistical data - Admin only"""
    
    # Check if user is system admin
    if request.user.user_type != 'admin':
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
    crops = CropSeason.objects.filter(field__farm__owner=request.user)
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        crops = crops.filter(status=status_filter)
    
    paginator = Paginator(crops, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'crops/list.html', {'crops': page_obj})


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
    animals = Animal.objects.filter(farm__owner=request.user)
    
    # Filter by species
    species_filter = request.GET.get('species')
    if species_filter:
        animals = animals.filter(animal_type__species=species_filter)
    
    return render(request, 'livestock/list.html', {'animals': animals})


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
    
    return render(request, 'equipment/list.html', {'equipment': equipment})


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
    """List all products for sale with search and filters"""
    listings = ProductListing.objects.filter(status='active').order_by('-created_at')
    
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
    all_categories = ProductListing.objects.filter(status='active').values_list('category', flat=True).distinct().order_by('category')
    
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
        'query_params': query_params
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
    return render(request, 'marketplace/detail.html', {'listing': listing})


@login_required
def edit_listing(request, pk):
    """Edit a product listing"""
    listing = get_object_or_404(ProductListing, pk=pk)
    
    # Check if user is the seller
    if listing.seller.owner != request.user:
        messages.error(request, 'You can only edit your own listings.')
        return redirect('core:listing_detail', pk=pk)
    
    if request.method == 'POST':
        form = ProductListingForm(request.POST, request.FILES, instance=listing, user=request.user)
        if form.is_valid():
            listing = form.save()
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
def buy_product(request, pk):
    """Purchase a product"""
    listing = get_object_or_404(ProductListing, pk=pk, status='active')
    
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
            if listing.quantity <= 0:
                listing.status = 'sold'
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
    """Use OpenAI Vision API to analyze pest image"""
    try:
        # Get API key from settings
        from django.conf import settings
        api_key = settings.OPENAI_API_KEY
        
        # Check if API key is available
        if not api_key or api_key.strip() == '':
            return {
                'pest_detected': False,
                'pest_name': 'API Key Not Configured',
                'confidence': 0,
                'severity': 'low',
                'affected_area': 0,
                'explanation': 'OpenAI API key is not configured. Please add OPENAI_API_KEY to your .env file.',
                'identification_details': 'API configuration required',
                'immediate_action': 'Configure your API key first',
                'treatment': 'API configuration required',
                'organic_treatment': '',
                'prevention': '',
                'disease_cycle': '',
                'environmental_factors': '',
                'error': 'OpenAI API key not configured'
            }
        
        # Encode image to base64
        base64_image = encode_image_to_base64(image_file)
        
        # Get image format from filename
        image_format = image_name.lower().split('.')[-1] if '.' in image_name else 'jpeg'
        if image_format == 'jpg':
            image_format = 'jpeg'
        
        media_type = f'image/{image_format}'
        
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
        # General error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f'Pest analysis error: {str(e)}', exc_info=True)
        
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
                    location='Default Location',
                    size_hectares=0,
                    soil_type='loamy'
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
                confidence=Decimal(str(result.get('confidence', 0))),
                severity=result.get('severity', 'low'),
                affected_area_percentage=Decimal(str(result.get('affected_area', 0))),
                treatment_recommended=result.get('treatment', ''),
                prevention_tips=result.get('prevention', ''),
                organic_options=result.get('organic_treatment', ''),
                status='pending' if result.get('pest_detected') else 'healthy'
            )
            
            # Create notification for pest detection
            if result.get('pest_detected'):
                Notification.objects.create(
                    user=request.user,
                    notification_type='alert',
                    title=f'Pest Detected: {result.get("pest_name")}',
                    message=f'A {result.get("severity", "unknown")} severity {result.get("pest_name")} was detected in your crop with {result.get("confidence")}% confidence.',
                    link=f'/pest-detection/{report.id}/'
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
    
    return render(request, 'pest/history.html', {'page_obj': page_obj, 'stats': stats})


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
    policies = InsurancePolicy.objects.filter(farmer=request.user).order_by('-created_at')
    return render(request, 'insurance/dashboard.html', {'policies': policies})


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
    farms = Farm.objects.filter(owner=request.user)
    payrolls = Payroll.objects.filter(worker__farm__in=farms).order_by('-period_start')
    return render(request, 'labor/payroll.html', {'payrolls': payrolls})


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