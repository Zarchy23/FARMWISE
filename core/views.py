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
from decimal import Decimal
import json
import requests

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
    
    # Admin dashboard redirect
    if request.user.is_superuser or request.user.user_type == 'admin':
        return redirect('core:admin_dashboard')
    
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
    
    # Weather (mock - integrate with real API)
    weather = {
        'temp': 28,
        'condition': 'Sunny',
        'forecast': 'Clear skies expected for next 3 days'
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
def admin_dashboard(request):
    """Admin dashboard - System overview and management"""
    if not (request.user.is_superuser or request.user.user_type == 'admin'):
        messages.error(request, 'You do not have permission to access the admin dashboard.')
        return redirect('core:dashboard')
    
    # System statistics
    total_users = User.objects.count()
    total_farms = Farm.objects.count()
    total_crops = CropSeason.objects.count()
    total_animals = Animal.objects.count()
    total_transactions = Transaction.objects.count()
    
    # User breakdown by type with percentages
    user_breakdown = []
    for user_type_code, user_type_name in User.USER_TYPES:
        count = User.objects.filter(user_type=user_type_code).count()
        percentage = (count * 100 // total_users) if total_users > 0 else 0
        user_breakdown.append({
            'name': user_type_name,
            'count': count,
            'percentage': percentage
        })
    
    # Recent users
    recent_users = User.objects.all().order_by('-date_joined')[:10]
    
    # Monthly transaction total
    monthly_transactions = Transaction.objects.filter(
        date__month=timezone.now().month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'total_users': total_users,
        'total_farms': total_farms,
        'total_crops': total_crops,
        'total_animals': total_animals,
        'total_transactions': total_transactions,
        'monthly_transactions': monthly_transactions,
        'user_breakdown': user_breakdown,
        'recent_users': recent_users,
    }
    
    return render(request, 'admin/dashboard.html', context)


@login_required
def user_management(request):
    """Admin user management - View all users and their types"""
    if not (request.user.is_superuser or request.user.user_type == 'admin'):
        messages.error(request, 'You do not have permission to access user management.')
        return redirect('core:dashboard')
    
    # Get all users with pagination
    users = User.objects.all().order_by('-date_joined')
    
    # Filter by user type if specified
    user_type_filter = request.GET.get('user_type', '')
    if user_type_filter:
        users = users.filter(user_type=user_type_filter)
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj,
        'user_types': User.USER_TYPES,
        'selected_type': user_type_filter,
    }
    
    return render(request, 'admin/user_management.html', context)


@login_required
def profile(request):
    """User profile view"""
    return render(request, 'accounts/profile.html', {'user': request.user})


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
        form = CropSeasonForm(request.POST)
        if form.is_valid():
            crop = form.save(commit=False)
            crop.created_by = request.user
            crop.save()
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
        form = CropSeasonForm(request.POST, instance=crop)
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
        form = AnimalForm(request.POST)
        if form.is_valid():
            animal = form.save(commit=False)
            animal.save()
            messages.success(request, f'Animal {animal.tag_number} added successfully!')
            return redirect('core:animal_detail', pk=animal.pk)
    else:
        form = AnimalForm()
        form.fields['farm'].queryset = Farm.objects.filter(owner=request.user)
    
    return render(request, 'livestock/add.html', {'form': form})


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
        form = AnimalForm(request.POST, instance=animal)
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
    """List all products for sale"""
    listings = ProductListing.objects.filter(status='active').order_by('-created_at')
    
    # Search
    search_query = request.GET.get('q')
    if search_query:
        listings = listings.filter(product_name__icontains=search_query)
    
    paginator = Paginator(listings, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'marketplace/list.html', {'listings': page_obj})


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

@login_required
def pest_detection(request):
    """Pest detection page"""
    return render(request, 'pest/detection.html')


@login_required
def pest_upload(request):
    """Upload and analyze pest image"""
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        
        # Mock AI detection (integrate with actual AI service)
        # In production, call OpenAI Vision API or custom model
        
        # Simulate detection result
        result = {
            'pest_name': 'Fall Armyworm',
            'confidence': 94,
            'treatment': 'Apply Emamectin benzoate at recommended dosage. Remove affected leaves.',
            'severity': 'high'
        }
        
        # Save report
        report = PestReport.objects.create(
            farmer=request.user,
            farm=request.user.farms.first(),
            image=image,
            ai_diagnosis=result['pest_name'],
            confidence=result['confidence'],
            severity=result['severity'],
            treatment_recommended=result['treatment']
        )
        
        return render(request, 'pest/results.html', {'result': result, 'report': report})
    
    return redirect('core:pest_detection')


@login_required
def pest_history(request):
    """View pest detection history"""
    reports = PestReport.objects.filter(farmer=request.user).order_by('-created_at')
    return render(request, 'pest/history.html', {'reports': reports})


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
    """Weather forecast page"""
    # Mock weather data (integrate with OpenWeatherMap API)
    forecast = [
        {'day': timezone.now().date(), 'temp_high': 28, 'temp_low': 18, 'condition': 'Sunny', 'icon': 'sun'},
        {'day': timezone.now().date() + timezone.timedelta(days=1), 'temp_high': 27, 'temp_low': 17, 'condition': 'Partly Cloudy', 'icon': 'cloud-sun'},
        {'day': timezone.now().date() + timezone.timedelta(days=2), 'temp_high': 25, 'temp_low': 16, 'condition': 'Rain', 'icon': 'rainy'},
        {'day': timezone.now().date() + timezone.timedelta(days=3), 'temp_high': 26, 'temp_low': 17, 'condition': 'Cloudy', 'icon': 'cloudy'},
        {'day': timezone.now().date() + timezone.timedelta(days=4), 'temp_high': 29, 'temp_low': 19, 'condition': 'Sunny', 'icon': 'sun'},
    ]
    
    return render(request, 'weather/forecast.html', {'forecast': forecast})


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
    schedules = IrrigationSchedule.objects.filter(
        field__farm__in=farms,
        scheduled_date__gte=timezone.now().date()
    ).order_by('scheduled_date')[:10]
    
    return render(request, 'irrigation/dashboard.html', {'schedules': schedules})


@login_required
def irrigation_schedule(request):
    """Schedule irrigation"""
    if request.method == 'POST':
        form = IrrigationForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, f'Irrigation scheduled for {schedule.field.name} on {schedule.scheduled_date}')
            return redirect('core:irrigation')
    else:
        form = IrrigationForm()
        form.fields['field'].queryset = Field.objects.filter(farm__owner=request.user)
    
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
            policy.save()
            messages.success(request, f'Insurance policy {policy.policy_number} purchased!')
            return redirect('core:insurance')
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
            worker = form.save()
            messages.success(request, f'Worker {worker.worker.get_full_name()} added!')
            return redirect('core:labor')
    else:
        form = WorkerForm()
        form.fields['farm'].queryset = Farm.objects.filter(owner=request.user)
    
    return render(request, 'labor/add.html', {'form': form})


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
    
    return render(request, 'labor/hours.html', {'form': form, 'worker': worker})


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
    """API endpoint for weather"""
    # Mock weather data
    weather_data = {
        'temperature': 28,
        'condition': 'Sunny',
        'humidity': 65,
        'wind_speed': 12,
        'forecast': 'Clear skies for next 3 days'
    }
    return JsonResponse(weather_data)


@login_required
def api_notifications(request):
    """API endpoint for notifications"""
    notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).values('id', 'title', 'message', 'created_at')[:10]
    
    return JsonResponse(list(notifications), safe=False)