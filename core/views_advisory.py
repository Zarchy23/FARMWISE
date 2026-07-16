"""
Farmer Advisory System Views
Provides comprehensive guidance for land preparation, pest management, and livestock care
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib import messages
from .models_advisory import (
    FarmProfile, LandPreparationGuide, PestManagementGuide,
    PesticideInfo, PesticideDosageCalculator, VeterinaryDrug,
    AdvisoryRequest, AdvisoryKnowledgeBase
)
from .models import User
import json


@login_required
def advisory_dashboard(request):
    """Main advisory dashboard"""
    try:
        farm_profile = request.user.farm_profile
    except FarmProfile.DoesNotExist:
        return redirect('advisory:setup_farm_profile')
    
    # Get recent advisory requests
    recent_requests = AdvisoryRequest.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Get relevant guides based on farm profile
    land_guides = LandPreparationGuide.objects.filter(
        agro_ecological_zone=farm_profile.agro_ecological_zone,
        is_active=True
    )[:5]
    
    pest_guides = PestManagementGuide.objects.filter(is_active=True)[:5]
    
    context = {
        'farm_profile': farm_profile,
        'recent_requests': recent_requests,
        'land_guides': land_guides,
        'pest_guides': pest_guides,
    }
    
    return render(request, 'advisory/dashboard.html', context)


@login_required
def setup_farm_profile(request):
    """Setup or edit farm profile"""
    try:
        profile = request.user.farm_profile
    except FarmProfile.DoesNotExist:
        profile = None
    
    if request.method == 'POST':
        if profile:
            # Update existing profile
            for field in FarmProfile._meta.get_fields():
                if field.name not in ['id', 'user', 'created_at', 'updated_at']:
                    setattr(profile, field.name, request.POST.get(field.name))
            profile.save()
            messages.success(request, 'Farm profile updated successfully!')
        else:
            # Create new profile
            profile = FarmProfile.objects.create(
                user=request.user,
                farm_name=request.POST.get('farm_name'),
                farm_type=request.POST.get('farm_type'),
                location=request.POST.get('location'),
                agro_ecological_zone=request.POST.get('agro_ecological_zone'),
                total_land_area_hectares=request.POST.get('total_land_area_hectares'),
                arable_land_hectares=request.POST.get('arable_land_hectares'),
                primary_land_preparation_method=request.POST.get('primary_land_preparation_method'),
                labor_availability=request.POST.get('labor_availability'),
                equipment_inventory=request.POST.get('equipment_inventory'),
                soil_type=request.POST.get('soil_type'),
                water_source=request.POST.get('water_source'),
                irrigation_access=request.POST.get('irrigation_access') == 'on',
                farming_experience_years=request.POST.get('farming_experience_years'),
                primary_crops=request.POST.get('primary_crops'),
                livestock_types=request.POST.get('livestock_types'),
            )
            messages.success(request, 'Farm profile created successfully!')
        
        return redirect('advisory:dashboard')
    
    context = {
        'profile': profile,
        'farm_types': FarmProfile.FARM_TYPES,
        'agro_zones': FarmProfile.AGRO_ECOLOGICAL_ZONES,
        'land_methods': FarmProfile.LAND_PREPARATION_METHODS,
    }
    
    return render(request, 'advisory/setup_profile.html', context)


@login_required
def land_preparation_guides(request):
    """Browse land preparation guides"""
    farm_profile = getattr(request.user, 'farm_profile', None)
    
    guides = LandPreparationGuide.objects.filter(is_active=True)
    
    # Filter by farm profile if available
    if farm_profile:
        guides = guides.filter(agro_ecological_zone=farm_profile.agro_ecological_zone)
    
    # Filter by crop type
    crop_filter = request.GET.get('crop')
    if crop_filter:
        guides = guides.filter(crop_type=crop_filter)
    
    paginator = Paginator(guides, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'crop_types': LandPreparationGuide.CROP_TYPES,
        'current_filter': crop_filter,
    }
    
    return render(request, 'advisory/land_guides.html', context)


@login_required
def land_preparation_detail(request, guide_id):
    """Detailed land preparation guide"""
    guide = get_object_or_404(LandPreparationGuide, id=guide_id, is_active=True)
    
    context = {
        'guide': guide,
    }
    
    return render(request, 'advisory/land_detail.html', context)


@login_required
def pest_management_guides(request):
    """Browse pest management guides"""
    guides = PestManagementGuide.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        guides = guides.filter(
            Q(pest_name__icontains=search_query) |
            Q(affected_crops__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by crop
    crop_filter = request.GET.get('crop')
    if crop_filter:
        guides = guides.filter(affected_crops__icontains=crop_filter)
    
    paginator = Paginator(guides, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_search': search_query,
        'current_filter': crop_filter,
    }
    
    return render(request, 'advisory/pest_guides.html', context)


@login_required
def pest_management_detail(request, guide_id):
    """Detailed pest management guide"""
    guide = get_object_or_404(PestManagementGuide, id=guide_id, is_active=True)
    
    context = {
        'guide': guide,
    }
    
    return render(request, 'advisory/pest_detail.html', context)


@login_required
def pesticide_database(request):
    """Browse pesticide information database"""
    pesticides = PesticideInfo.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        pesticides = pesticides.filter(
            Q(product_name__icontains=search_query) |
            Q(active_ingredient__icontains=search_query) |
            Q(target_pests__icontains=search_query)
        )
    
    paginator = Paginator(pesticides, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_search': search_query,
    }
    
    return render(request, 'advisory/pesticide_database.html', context)


@login_required
def pesticide_detail(request, pesticide_id):
    """Detailed pesticide information"""
    pesticide = get_object_or_404(PesticideInfo, id=pesticide_id, is_active=True)
    
    context = {
        'pesticide': pesticide,
    }
    
    return render(request, 'advisory/pesticide_detail.html', context)


@login_required
def dosage_calculator(request):
    """Pesticide dosage calculator"""
    calculators = PesticideDosageCalculator.objects.all()
    pesticides = PesticideInfo.objects.filter(is_active=True)
    
    if request.method == 'POST':
        sprayer_id = request.POST.get('sprayer_type')
        pesticide_id = request.POST.get('pesticide')
        field_area = float(request.POST.get('field_area'))
        pesticide_rate = request.POST.get('pesticide_rate')
        
        sprayer = get_object_or_404(PesticideDosageCalculator, id=sprayer_id)
        pesticide = get_object_or_404(PesticideInfo, id=pesticide_id)
        
        # Calculate dosage
        calculation = sprayer.calculate_dosage(pesticide_rate, field_area)
        
        context = {
            'calculators': calculators,
            'pesticides': pesticides,
            'calculation': calculation,
            'sprayer': sprayer,
            'pesticide': pesticide,
            'field_area': field_area,
            'pesticide_rate': pesticide_rate,
        }
        
        return render(request, 'advisory/dosage_calculator.html', context)
    
    context = {
        'calculators': calculators,
        'pesticides': pesticides,
    }
    
    return render(request, 'advisory/dosage_calculator.html', context)


@login_required
def veterinary_drug_database(request):
    """Browse veterinary drug database"""
    drugs = VeterinaryDrug.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        drugs = drugs.filter(
            Q(drug_name__icontains=search_query) |
            Q(generic_name__icontains=search_query) |
            Q(drug_class__icontains=search_query)
        )
    
    # Filter by species
    species_filter = request.GET.get('species')
    if species_filter:
        drugs = drugs.filter(species=species_filter)
    
    paginator = Paginator(drugs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_search': search_query,
        'current_filter': species_filter,
        'species_choices': VeterinaryDrug.ANIMAL_SPECIES,
    }
    
    return render(request, 'advisory/veterinary_database.html', context)


@login_required
def veterinary_drug_detail(request, drug_id):
    """Detailed veterinary drug information"""
    drug = get_object_or_404(VeterinaryDrug, id=drug_id, is_active=True)
    
    context = {
        'drug': drug,
    }
    
    return render(request, 'advisory/veterinary_detail.html', context)


@login_required
def animal_dosage_calculator(request):
    """Animal dosage calculator"""
    drugs = VeterinaryDrug.objects.filter(is_active=True)
    
    if request.method == 'POST':
        drug_id = request.POST.get('drug')
        animal_weight = float(request.POST.get('animal_weight'))
        
        drug = get_object_or_404(VeterinaryDrug, id=drug_id)
        calculation = drug.calculate_dose(animal_weight)
        
        context = {
            'drugs': drugs,
            'calculation': calculation,
            'drug': drug,
            'animal_weight': animal_weight,
        }
        
        return render(request, 'advisory/animal_dosage_calculator.html', context)
    
    context = {
        'drugs': drugs,
    }
    
    return render(request, 'advisory/animal_dosage_calculator.html', context)


@login_required
def submit_advisory_request(request):
    """Submit a new advisory request"""
    if request.method == 'POST':
        advisory_request = AdvisoryRequest.objects.create(
            user=request.user,
            request_type=request.POST.get('request_type'),
            subject=request.POST.get('subject'),
            description=request.POST.get('description'),
            crop_type=request.POST.get('crop_type', ''),
            animal_species=request.POST.get('animal_species', ''),
            field_area_hectares=request.POST.get('field_area_hectares') or None,
            animal_weight_kg=request.POST.get('animal_weight_kg') or None,
        )
        
        messages.success(request, 'Your advisory request has been submitted successfully!')
        return redirect('advisory:dashboard')
    
    context = {
        'request_types': AdvisoryRequest.REQUEST_TYPES,
    }
    
    return render(request, 'advisory/submit_request.html', context)


@login_required
def advisory_request_detail(request, request_id):
    """View advisory request details"""
    advisory_request = get_object_or_404(AdvisoryRequest, id=request_id, user=request.user)
    
    if request.method == 'POST':
        # Add feedback
        advisory_request.user_satisfaction = request.POST.get('satisfaction')
        advisory_request.user_feedback = request.POST.get('feedback')
        advisory_request.save()
        
        messages.success(request, 'Thank you for your feedback!')
        return redirect('advisory:dashboard')
    
    context = {
        'request': advisory_request,
    }
    
    return render(request, 'advisory/request_detail.html', context)


@login_required
def my_advisory_requests(request):
    """View user's advisory requests"""
    requests = AdvisoryRequest.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        requests = requests.filter(status=status_filter)
    
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_filter': status_filter,
        'status_choices': AdvisoryRequest.STATUS_CHOICES,
    }
    
    return render(request, 'advisory/my_requests.html', context)


@login_required
def knowledge_base(request):
    """Browse advisory knowledge base"""
    articles = AdvisoryKnowledgeBase.objects.filter(is_active=True)
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(question__icontains=search_query) |
            Q(answer__icontains=search_query)
        )
    
    # Filter by type
    type_filter = request.GET.get('type')
    if type_filter:
        articles = articles.filter(knowledge_type=type_filter)
    
    paginator = Paginator(articles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_search': search_query,
        'current_filter': type_filter,
        'knowledge_types': AdvisoryKnowledgeBase.KNOWLEDGE_TYPES,
    }
    
    return render(request, 'advisory/knowledge_base.html', context)


@login_required
def knowledge_article_detail(request, article_id):
    """View knowledge base article"""
    article = get_object_or_404(AdvisoryKnowledgeBase, id=article_id, is_active=True)
    
    # Increment access count
    article.access_count += 1
    article.save()
    
    context = {
        'article': article,
    }
    
    return render(request, 'advisory/knowledge_article.html', context)


# API Endpoints for mobile app integration
@login_required
def api_land_guides(request):
    """API endpoint for land preparation guides"""
    guides = LandPreparationGuide.objects.filter(is_active=True)
    
    # Filter by agro-ecological zone from user profile
    try:
        farm_profile = request.user.farm_profile
        guides = guides.filter(agro_ecological_zone=farm_profile.agro_ecological_zone)
    except FarmProfile.DoesNotExist:
        pass
    
    data = [{
        'id': guide.id,
        'title': guide.title,
        'crop_type': guide.crop_type,
        'soil_type': guide.soil_type,
        'preparation_method': guide.preparation_method,
        'rainfall_requirement': guide.rainfall_requirement_mm,
        'step_by_step_guide': guide.step_by_step_guide,
    } for guide in guides]
    
    return JsonResponse({'guides': data})


@login_required
def api_pest_guides(request):
    """API endpoint for pest management guides"""
    guides = PestManagementGuide.objects.filter(is_active=True)
    
    # Search filter
    search_query = request.GET.get('search')
    if search_query:
        guides = guides.filter(
            Q(pest_name__icontains=search_query) |
            Q(affected_crops__icontains=search_query)
        )
    
    data = [{
        'id': guide.id,
        'pest_name': guide.pest_name,
        'scientific_name': guide.scientific_name,
        'affected_crops': guide.affected_crops,
        'primary_control_method': guide.primary_control_method,
        'cultural_controls': guide.cultural_controls,
        'chemical_controls': guide.chemical_controls,
    } for guide in guides]
    
    return JsonResponse({'guides': data})


@login_required
def api_calculate_dosage(request):
    """API endpoint for dosage calculation"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        sprayer_id = data.get('sprayer_id')
        pesticide_rate = data.get('pesticide_rate')
        field_area = data.get('field_area')
        
        sprayer = get_object_or_404(PesticideDosageCalculator, id=sprayer_id)
        calculation = sprayer.calculate_dosage(pesticide_rate, field_area)
        
        return JsonResponse({'calculation': calculation})
    
    return JsonResponse({'error': 'POST request required'}, status=400)


@login_required
def api_animal_dosage(request):
    """API endpoint for animal dosage calculation"""
    if request.method == 'POST':
        data = json.loads(request.body)
        
        drug_id = data.get('drug_id')
        animal_weight = data.get('animal_weight')
        
        drug = get_object_or_404(VeterinaryDrug, id=drug_id)
        calculation = drug.calculate_dose(animal_weight)
        
        return JsonResponse({'calculation': calculation})
    
    return JsonResponse({'error': 'POST request required'}, status=400)
