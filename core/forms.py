# core/forms.py
# FARMWISE - Complete Forms for All Models

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .models import *

# ============================================================
# SECTION 1: USER FORMS
# ============================================================

class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    
    email = forms.EmailField(
        required=True,
        help_text='We\'ll use this for account recovery and notifications',
        widget=forms.EmailInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'your@email.com'
        })
    )
    
    phone_number = forms.CharField(
        required=True,
        help_text='International format: +254712345678 or local: 0712345678',
        widget=forms.TextInput(attrs={
            'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': '+254712345678 or 0712345678'
        })
    )
    
    user_type = forms.ChoiceField(
        choices=[choice for choice in User.USER_TYPES if choice[0] != 'admin'],
        required=True,
        label='User Type',
        help_text='Select your role on FarmWise',
        widget=forms.Select(attrs={
            'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'phone_number', 'user_type', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Choose a username',
                'autocomplete': 'username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Update password fields with consistent styling
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Enter password',
            'autocomplete': 'new-password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password'
        })
        
        # Add help text styling
        for field_name, field in self.fields.items():
            if field.help_text:
                field.help_text = f'<small class="text-gray-600">{field.help_text}</small>'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data['phone_number']
        user.user_type = self.cleaned_data['user_type']
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile_picture', 
                  'preferred_language', 'accepts_sms', 'accepts_email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2'
            }),
            'preferred_language': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'accepts_sms': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 focus:ring-green-500'
            }),
            'accepts_email': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 focus:ring-green-500'
            }),
        }


# ============================================================
# SECTION 2: FARM & FIELD FORMS
# ============================================================

class FarmForm(forms.ModelForm):
    """Form for creating and editing farms"""
    location_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
            'placeholder': 'Search for your location (address, city, coordinates)',
            'id': 'location-search-input'
        }),
        label='Find Location',
        help_text='Search by address or enter latitude,longitude'
    )
    
    class Meta:
        model = Farm
        fields = ['name', 'location_search', 'location', 'address', 'total_area_hectares', 'farm_type']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Enter farm name'
            }),
            'location': forms.HiddenInput(),
            'address': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Physical address'
            }),
            'total_area_hectares': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Total area in hectares'
            }),
            'farm_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
        }
    
    def clean_total_area_hectares(self):
        area = self.cleaned_data.get('total_area_hectares')
        if area <= 0:
            raise forms.ValidationError('Area must be greater than 0')
        return area
    
    def clean(self):
        cleaned_data = super().clean()
        location = cleaned_data.get('location')
        location_search = cleaned_data.get('location_search')
        
        # If location is not set from the hidden field, try to parse location_search
        if not location and location_search:
            # Try to parse as latitude,longitude
            try:
                lat, lng = map(float, location_search.split(','))
                cleaned_data['location'] = {'lat': lat, 'lng': lng}
            except (ValueError, AttributeError):
                # If it fails, location can be empty (users will manually enter address)
                pass
        
        return cleaned_data


class FieldForm(forms.ModelForm):
    """Form for creating and editing fields"""
    
    class Meta:
        model = Field
        fields = ['name', 'area_hectares', 'soil_type', 'slope', 'irrigation_available', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Field name (e.g., North Field)'
            }),
            'area_hectares': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0'
            }),
            'soil_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'slope': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'irrigation_available': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 focus:ring-green-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Additional notes about this field'
            }),
        }


# ============================================================
# SECTION 3: CROP MANAGEMENT FORMS
# ============================================================

class CropTypeForm(forms.ModelForm):
    """Form for managing crop types"""
    
    suitable_seasons = forms.MultipleChoiceField(
        choices=CropSeason.SEASONS,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'space-y-2'
        })
    )
    
    class Meta:
        model = CropType
        fields = ['name', 'scientific_name', 'category', 'growing_days', 
                  'water_requirement_mm', 'optimal_temp_min', 'optimal_temp_max',
                  'planting_distance_cm', 'seed_rate_kg_per_ha', 'expected_yield_kg_per_ha',
                  'suitable_seasons', 'image', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Crop name (e.g., Maize, Wheat)'
            }),
            'scientific_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Scientific name (optional)'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'growing_days': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '1',
                'placeholder': 'Days to harvest'
            }),
            'water_requirement_mm': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '0',
                'placeholder': 'Water needed (mm)'
            }),
            'optimal_temp_min': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'placeholder': 'Min temp (°C)'
            }),
            'optimal_temp_max': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'placeholder': 'Max temp (°C)'
            }),
            'planting_distance_cm': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '0',
                'placeholder': 'Planting distance (cm)'
            }),
            'seed_rate_kg_per_ha': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Seed rate (kg/ha)'
            }),
            'expected_yield_kg_per_ha': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Expected yield (kg/ha)'
            }),
            'image': forms.FileInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'accept': 'image/*'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'Describe the crop characteristics...'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 rounded focus:ring-green-500'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.suitable_seasons:
            self.fields['suitable_seasons'].initial = self.instance.suitable_seasons
    
    def save(self, commit=True):
        crop_type = super().save(commit=False)
        crop_type.suitable_seasons = self.cleaned_data['suitable_seasons']
        if commit:
            crop_type.save()
        return crop_type


class CropSeasonForm(forms.ModelForm):
    """Form for planting crops"""
    
    class Meta:
        model = CropSeason
        fields = ['field', 'crop_type', 'variety', 'season', 'planting_date', 'expected_harvest_date', 
                  'area_allocated_hectares', 'estimated_yield_kg', 'photo', 'notes']
        widgets = {
            'field': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'crop_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'variety': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Specific variety name'
            }),
            'season': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'planting_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'expected_harvest_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'area_allocated_hectares': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Area in hectares'
            }),
            'estimated_yield_kg': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'placeholder': 'Estimated yield in kilograms'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'accept': 'image/*',
                'placeholder': 'Upload crop photo (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Any additional notes'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        planting_date = cleaned_data.get('planting_date')
        expected_harvest_date = cleaned_data.get('expected_harvest_date')
        
        if planting_date and expected_harvest_date:
            if expected_harvest_date <= planting_date:
                raise forms.ValidationError('Harvest date must be after planting date')
        
        return cleaned_data


class InputForm(forms.ModelForm):
    """Form for adding input applications"""
    
    class Meta:
        model = InputApplication
        fields = ['input_type', 'product_name', 'quantity', 'unit', 'cost_per_unit', 
                  'application_date', 'application_method', 'notes']
        widgets = {
            'input_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'product_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Product name'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0'
            }),
            'unit': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'cost_per_unit': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Cost per unit'
            }),
            'application_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'application_method': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'How applied (spray, broadcast, etc.)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


class HarvestForm(forms.ModelForm):
    """Form for recording harvests"""
    
    class Meta:
        model = Harvest
        fields = ['harvest_date', 'quantity_kg', 'quality_grade', 'selling_price_kg', 'buyer_name', 'notes']
        widgets = {
            'harvest_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'quantity_kg': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Quantity in kilograms'
            }),
            'quality_grade': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'selling_price_kg': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Price per kilogram'
            }),
            'buyer_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Buyer name'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


# ============================================================
# SECTION 4: LIVESTOCK FORMS
# ============================================================

class AnimalForm(forms.ModelForm):
    """Form for adding and editing animals"""
    
    class Meta:
        model = Animal
        fields = ['farm', 'animal_type', 'tag_number', 'name', 'gender', 'birth_date', 
                  'purchase_date', 'purchase_price', 'weight_kg', 'photo', 'location', 'notes']
        widgets = {
            'farm': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'animal_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'tag_number': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Ear tag number or unique ID'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Animal name (optional)'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'birth_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Purchase price'
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Weight in kilograms'
            }),
            'photo': forms.FileInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'accept': 'image/*',
                'placeholder': 'Upload animal photo (optional)'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Current pasture/shed location'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


class HealthRecordForm(forms.ModelForm):
    """Form for adding health records"""
    
    class Meta:
        model = HealthRecord
        fields = ['record_type', 'record_date', 'diagnosis', 'symptoms', 'treatment', 
                  'medication_name', 'dosage', 'administered_by', 'cost', 'next_due_date', 'notes']
        widgets = {
            'record_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'record_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'diagnosis': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Diagnosis'
            }),
            'symptoms': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Observed symptoms'
            }),
            'treatment': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Treatment given'
            }),
            'medication_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Medication name'
            }),
            'dosage': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Dosage'
            }),
            'administered_by': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Who administered'
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Cost'
            }),
            'next_due_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


class BreedingRecordForm(forms.ModelForm):
    """Form for adding breeding records"""
    
    class Meta:
        model = BreedingRecord
        fields = ['breeding_date', 'mate_animal', 'method', 'result', 'expected_calving_date', 'notes']
        widgets = {
            'breeding_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'mate_animal': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'method': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Natural, AI, etc.'
            }),
            'result': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'expected_calving_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


class MilkProductionForm(forms.ModelForm):
    """Form for recording milk production"""
    
    class Meta:
        model = MilkProduction
        fields = ['production_date', 'morning_kg', 'evening_kg', 'fat_content', 'protein_content', 'notes']
        widgets = {
            'production_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'morning_kg': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Morning milking (kg)'
            }),
            'evening_kg': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Evening milking (kg)'
            }),
            'fat_content': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Fat content (%)'
            }),
            'protein_content': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Protein content (%)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }


# ============================================================
# SECTION 5: EQUIPMENT RENTAL FORMS
# ============================================================

class EquipmentForm(forms.ModelForm):
    """Form for listing equipment for rent"""

    images = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
            'accept': 'image/*'
        }),
        help_text='Upload at least one image of the equipment (required)'
    )

    class Meta:
        model = Equipment
        fields = ['name', 'category', 'description', 'hourly_rate', 'daily_rate',
                  'weekly_rate', 'monthly_rate', 'deposit_amount', 'location', 'specifications']


class AssetForm(forms.ModelForm):
    """Form for managing personal assets"""

    images = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
            'accept': 'image/*'
        }),
        help_text='Upload images of the asset (optional)'
    )

    class Meta:
        model = Asset
        fields = ['name', 'asset_type', 'description', 'serial_number', 'purchase_date',
                  'purchase_price', 'current_value', 'condition', 'status', 'location',
                  'last_maintenance_date', 'next_maintenance_date', 'maintenance_notes', 'specifications']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Asset name'
            }),
            'asset_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Describe the asset, its condition, features...'
            }),
            'serial_number': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Serial number (optional)'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'purchase_price': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Purchase price'
            }),
            'current_value': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Current value'
            }),
            'condition': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Location where asset is stored'
            }),
            'last_maintenance_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'next_maintenance_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'maintenance_notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Maintenance notes or history'
            }),
        }


class BookingForm(forms.ModelForm):
    """Form for booking equipment"""
    
    class Meta:
        model = EquipmentBooking
        fields = ['start_date', 'end_date', 'pickup_location', 'renter_notes']
        widgets = {
            'start_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'pickup_location': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Where will you pick up?'
            }),
            'renter_notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Special requests or notes for owner'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError('End date must be after start date')
            
            if start_date < timezone.now().date():
                raise forms.ValidationError('Start date cannot be in the past')
        
        return cleaned_data


# ============================================================
# SECTION 6: MARKETPLACE FORMS
# ============================================================

class ProductListingForm(forms.ModelForm):
    """Form for creating product listings"""
    seller = forms.ModelChoiceField(
        queryset=Farm.objects.none(),
        widget=forms.Select(attrs={
            'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
        }),
        label='Sell from which farm?',
        help_text='Select the farm this product is from'
    )
    
    class Meta:
        model = ProductListing
        fields = ['seller', 'product_name', 'category', 'description', 'quantity', 'unit', 
                  'price_per_unit', 'images', 'harvest_date', 'expiry_date', 
                  'is_organic', 'delivery_available', 'delivery_fee']
        widgets = {
            'product_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Product name'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Describe your product in detail...'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Available quantity'
            }),
            'unit': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'price_per_unit': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Price per unit'
            }),
            'images': forms.ClearableFileInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2',
                'accept': 'image/*',
                'help_text': 'Upload an image for your product'
            }),
            'harvest_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'is_organic': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 focus:ring-green-500'
            }),
            'delivery_available': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 focus:ring-green-500'
            }),
            'delivery_fee': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Delivery fee'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['seller'].queryset = Farm.objects.filter(owner=user)
        
        # Set category as a dropdown with predefined options
        PRODUCT_CATEGORIES = [
            ('Vegetables', 'Vegetables'),
            ('Fruits', 'Fruits'),
            ('Grains & Cereals', 'Grains & Cereals'),
            ('Legumes', 'Legumes'),
            ('Dairy Products', 'Dairy Products'),
            ('Meat & Poultry', 'Meat & Poultry'),
            ('Eggs', 'Eggs'),
            ('Honey & Bee Products', 'Honey & Bee Products'),
            ('Herbs & Spices', 'Herbs & Spices'),
            ('Organic Products', 'Organic Products'),
            ('Other', 'Other'),
        ]
        self.fields['category'].widget = forms.Select(attrs={
            'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
        }, choices=PRODUCT_CATEGORIES)


class OrderForm(forms.ModelForm):
    """Form for placing orders"""
    
    class Meta:
        model = Order
        fields = ['quantity', 'delivery_address', 'buyer_notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0.01',
                'placeholder': 'Quantity to purchase'
            }),
            'delivery_address': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Delivery address'
            }),
            'buyer_notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Special instructions for seller'
            }),
        }
    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        listing = self.instance.listing if self.instance.id else None
        
        if listing and quantity > listing.quantity:
            raise forms.ValidationError(f'Only {listing.quantity} {listing.unit} available')
        
        return quantity


# ============================================================
# SECTION 7: INSURANCE FORMS
# ============================================================

class InsuranceForm(forms.ModelForm):
    """Form for purchasing insurance"""
    
    class Meta:
        model = InsurancePolicy
        fields = ['policy_type', 'farm', 'crop_type', 'area_hectares', 'livestock_count', 
                  'sum_insured', 'start_date', 'end_date', 'provider']
        widgets = {
            'policy_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'farm': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'crop_type': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Crop type (if crop insurance)'
            }),
            'area_hectares': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Area in hectares'
            }),
            'livestock_count': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'min': '0',
                'placeholder': 'Number of livestock'
            }),
            'sum_insured': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Total sum insured'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'provider': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Insurance provider name'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date:
            if end_date <= start_date:
                raise forms.ValidationError('End date must be after start date')
        
        return cleaned_data


class ClaimForm(forms.ModelForm):
    """Form for filing insurance claims"""
    
    class Meta:
        model = InsuranceClaim
        fields = ['damage_date', 'damage_percentage', 'estimated_loss', 'description', 'photos']
        widgets = {
            'damage_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'damage_percentage': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '1',
                'min': '0',
                'max': '100',
                'placeholder': 'Percentage of damage'
            }),
            'estimated_loss': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Estimated loss amount'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 4,
                'placeholder': 'Describe the damage in detail...'
            }),
            'photos': forms.ClearableFileInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2',
            }),
        }


# ============================================================
# SECTION 8: LABOR MANAGEMENT FORMS
# ============================================================

class WorkerForm(forms.ModelForm):
    """Form for adding workers"""
    new_worker_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
            'placeholder': 'Enter name if worker is not in the system'
        })
    )
    
    new_worker_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
            'placeholder': 'Phone number (e.g., +254712345678)'
        })
    )
    
    worker = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
        }),
        empty_label="-- Select from existing users --"
    )
    
    class Meta:
        model = Worker
        fields = ['worker', 'farm', 'hourly_wage', 'skills', 'emergency_contact', 'emergency_phone', 'notes']
        widgets = {
            'farm': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'hourly_wage': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.50',
                'min': '0',
                'placeholder': 'Hourly wage in USD'
            }),
            'skills': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Comma-separated skills (e.g., Tractor driving, Harvesting, Irrigation)'
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Emergency contact name',
                'required': False
            }),
            'emergency_phone': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Emergency contact phone',
                'required': False
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Additional notes',
                'required': False
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        worker = cleaned_data.get('worker')
        new_worker_name = cleaned_data.get('new_worker_name')
        
        # Validation: Either select an existing worker OR provide a new worker name
        if not worker and not new_worker_name:
            raise forms.ValidationError(
                'Please either select an existing worker or enter a new worker name.'
            )
        
        return cleaned_data


class WorkShiftForm(forms.ModelForm):
    """Form for logging work hours"""
    
    class Meta:
        model = WorkShift
        fields = ['field', 'date', 'task', 'hours_worked', 'overtime_hours', 'wage_rate', 'overtime_rate', 'notes']
        widgets = {
            'field': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'task': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'hours_worked': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.5',
                'min': '0',
                'placeholder': 'Regular hours worked'
            }),
            'overtime_hours': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.5',
                'min': '0',
                'placeholder': 'Overtime hours'
            }),
            'wage_rate': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Hourly wage rate'
            }),
            'overtime_rate': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Overtime hourly rate (usually 1.5x)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Task details or notes'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make field optional
        self.fields['field'].required = False
        # Make overtime fields optional
        self.fields['overtime_hours'].required = False
        self.fields['wage_rate'].required = False
        self.fields['overtime_rate'].required = False


# ============================================================
# SECTION 9: IRRIGATION FORMS
# ============================================================

class IrrigationForm(forms.ModelForm):
    """Form for scheduling irrigation"""
    
    class Meta:
        model = IrrigationSchedule
        fields = ['field', 'scheduled_date', 'duration_hours', 'notes']
        widgets = {
            'field': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'scheduled_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'duration_hours': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.5',
                'min': '0',
                'placeholder': 'Duration in hours'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 2,
                'placeholder': 'Additional notes'
            }),
        }
    
    def clean_scheduled_date(self):
        scheduled_date = self.cleaned_data.get('scheduled_date')
        if scheduled_date and scheduled_date < timezone.now().date():
            raise forms.ValidationError('Scheduled date cannot be in the past')
        return scheduled_date


# ============================================================
# SECTION 10: FINANCIAL FORMS
# ============================================================

class TransactionForm(forms.ModelForm):
    """Form for recording financial transactions"""
    
    class Meta:
        model = Transaction
        fields = ['farm', 'transaction_type', 'category', 'amount', 'date', 'description', 
                  'reference', 'receipt', 'related_crop', 'related_animal']
        widgets = {
            'farm': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'transaction_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Amount'
            }),
            'date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'description': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Transaction description'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Reference number (optional)'
            }),
            'receipt': forms.FileInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2'
            }),
            'related_crop': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'related_animal': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
        }


# ============================================================
# SECTION 11: PAYROLL FORMS
# ============================================================

class PayrollForm(forms.ModelForm):
    """Form for editing payroll records"""
    
    class Meta:
        model = Payroll
        fields = ['deductions', 'deduction_breakdown', 'status', 'payment_date', 'payment_method', 'transaction_id', 'notes']
        widgets = {
            'deductions': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Total deductions amount'
            }),
            'deduction_breakdown': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'JSON format: {"tax": 100, "insurance": 50, "other": 20}'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }, choices=[
                ('', '-- Select payment method --'),
                ('cash', 'Cash'),
                ('bank_transfer', 'Bank Transfer'),
                ('mobile_money', 'Mobile Money'),
                ('check', 'Check'),
                ('other', 'Other'),
            ]),
            'transaction_id': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Transaction ID (optional)'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Additional notes (optional)',
                'rows': 3
            }),
        }


# ============================================================
# SECTION 12: INVENTORY FORMS
# ============================================================

class InventoryForm(forms.ModelForm):
    """Form for managing farm inventory"""
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            # Filter crop seasons, animals, and fish cycles by user's farm
            self.fields['crop_seasons'].queryset = CropSeason.objects.filter(field__farm__owner=user)
            self.fields['animals'].queryset = Animal.objects.filter(farm__owner=user)
            self.fields['fish_cycles'].queryset = FishCycle.objects.filter(pond__farm__owner=user)
    
    class Meta:
        model = Inventory
        fields = ['name', 'category', 'description', 'quantity', 'unit', 
                  'minimum_stock_level', 'cost_per_unit', 'supplier', 
                  'supplier_contact', 'location', 'purchase_date', 'expiry_date', 
                  'crop_seasons', 'animals', 'fish_cycles', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Item name (e.g., Maize Seeds, NPK Fertilizer)'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'Describe the item, brand, specifications...'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Current quantity'
            }),
            'unit': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'minimum_stock_level': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Alert when below this level'
            }),
            'cost_per_unit': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Cost per unit (optional)'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Supplier name (optional)'
            }),
            'supplier_contact': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Supplier phone/email (optional)'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Storage location (e.g., Warehouse A, Shelf 3)'
            }),
            'purchase_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'crop_seasons': forms.SelectMultiple(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'size': '4'
            }),
            'animals': forms.SelectMultiple(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'size': '4'
            }),
            'fish_cycles': forms.SelectMultiple(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'size': '4'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
        }


# ============================================================
# SECTION 13: FISH FARMING FORMS
# ============================================================

class FishSpeciesForm(forms.ModelForm):
    """Form for managing fish species"""
    
    class Meta:
        model = FishSpecies
        fields = ['name', 'scientific_name', 'water_type', 'description', 
                  'growth_period_days', 'ideal_temperature_min', 'ideal_temperature_max', 
                  'market_price_per_kg']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Species name (e.g., Tilapia, Catfish)'
            }),
            'scientific_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Scientific name (optional)'
            }),
            'water_type': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'Describe the species characteristics...'
            }),
            'growth_period_days': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '1',
                'placeholder': 'Days to reach market size'
            }),
            'ideal_temperature_min': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'placeholder': 'Min temperature (°C)'
            }),
            'ideal_temperature_max': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'placeholder': 'Max temperature (°C)'
            }),
            'market_price_per_kg': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Market price per kg (optional)'
            }),
        }


class FishPondForm(forms.ModelForm):
    """Form for managing fish ponds"""
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['farm'].queryset = Farm.objects.filter(owner=user)
    
    class Meta:
        model = FishPond
        fields = ['farm', 'name', 'pond_type', 'length_m', 'width_m', 'depth_m', 
                  'max_stocking_density', 'location', 'water_source', 'status', 'notes']
        widgets = {
            'farm': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Pond name (e.g., Pond A, Tank 1)'
            }),
            'pond_type': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'length_m': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Length (meters)'
            }),
            'width_m': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Width (meters)'
            }),
            'depth_m': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Depth (meters)'
            }),
            'volume_cubic_meters': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'min': '0',
                'placeholder': 'Volume (cubic meters)'
            }),
            'max_stocking_density': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '1',
                'placeholder': 'Max fish per cubic meter'
            }),
            'location': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Location on farm'
            }),
            'water_source': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Water source (borehole, river, etc.)'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
        }


class FishCycleForm(forms.ModelForm):
    """Form for managing fish farming cycles"""
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['pond'].queryset = FishPond.objects.filter(farm__owner=user)
        # Ensure fish species dropdown is populated
        if 'fish_species' in self.fields:
            self.fields['fish_species'].queryset = FishSpecies.objects.all().order_by('name')
            self.fields['fish_species'].empty_label = "Select Fish Species"
    
    class Meta:
        model = FishCycle
        fields = ['pond', 'fish_species', 'season', 'cycle_name', 
                  'stocking_date', 'stock_quantity', 'average_weight_at_stocking_g',
                  'expected_harvest_date', 'expected_weight_per_fish_g', 'expected_survival_rate',
                  'actual_harvest_date', 'actual_quantity', 'average_weight_at_harvest_g',
                  'seed_cost', 'feed_cost', 'other_costs', 'total_revenue', 'notes']
        widgets = {
            'pond': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'fish_species': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'season': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'cycle_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Optional cycle name'
            }),
            'stocking_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '1',
                'placeholder': 'Number of fish stocked'
            }),
            'average_weight_at_stocking_g': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'placeholder': 'Avg weight at stocking (grams)'
            }),
            'expected_harvest_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'expected_weight_per_fish_g': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'placeholder': 'Expected weight per fish (grams)'
            }),
            'expected_survival_rate': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'min': '0',
                'max': '100',
                'placeholder': 'Survival rate %'
            }),
            'actual_harvest_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'actual_quantity': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '0',
                'placeholder': 'Actual number harvested'
            }),
            'average_weight_at_harvest_g': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'placeholder': 'Avg weight at harvest (grams)'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'seed_cost': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Fingerling/Startup cost'
            }),
            'feed_cost': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Feed cost'
            }),
            'other_costs': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Other costs'
            }),
            'total_revenue': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Total revenue'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
        }


class FishProductionForm(forms.ModelForm):
    """Form for recording fish production/harvest"""
    
    class Meta:
        model = FishProduction
        fields = ['cycle', 'harvest_date', 'quantity', 'total_weight_kg', 
                  'average_weight_g', 'grade', 'sold_quantity', 'sold_weight_kg', 
                  'revenue', 'remaining_quantity', 'notes']
        widgets = {
            'cycle': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500'
            }),
            'harvest_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'type': 'date'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '1',
                'placeholder': 'Number of fish harvested'
            }),
            'total_weight_kg': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Total weight (kg)'
            }),
            'average_weight_g': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.1',
                'placeholder': 'Avg weight per fish (grams)'
            }),
            'grade': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'placeholder': 'Grade/quality (optional)'
            }),
            'sold_quantity': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '0',
                'placeholder': 'Number sold'
            }),
            'sold_weight_kg': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Weight sold (kg)'
            }),
            'revenue': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Revenue from sales'
            }),
            'remaining_quantity': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'min': '0',
                'placeholder': 'Fish kept for breeding'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
        }