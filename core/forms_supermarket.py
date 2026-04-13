# core/forms_supermarket.py
# Supermarket and Product Stock Management Forms

from django import forms
from .models import Supermarket, ProductListing

# ============================================================
# PRODUCT CATEGORIES - SHARED ACROSS FORMS
# ============================================================

PRODUCT_CATEGORIES = [
    ('Seeds & Seedlings', 'Seeds & Seedlings'),
    ('Fertilizers', 'Fertilizers'),
    ('Pesticides & Herbicides', 'Pesticides & Herbicides'),
    ('Farming Tools', 'Farming Tools'),
    ('Agricultural Equipment', 'Agricultural Equipment'),
    ('Feed & Supplements', 'Feed & Supplements'),
    ('Vegetables', 'Vegetables'),
    ('Fruits', 'Fruits'),
    ('Dairy Products', 'Dairy Products'),
    ('Honey & Bee Products', 'Honey & Bee Products'),
    ('Grains & Cereals', 'Grains & Cereals'),
    ('Legumes', 'Legumes'),
    ('Herbs & Spices', 'Herbs & Spices'),
    ('Aquaculture Supplies', 'Aquaculture Supplies'),
    ('Veterinary Supplies', 'Veterinary Supplies'),
    ('Irrigation Equipment', 'Irrigation Equipment'),
    ('Storage & Containers', 'Storage & Containers'),
    ('Soil Testing Kits', 'Soil Testing Kits'),
    ('Other Agricultural Supplies', 'Other Agricultural Supplies'),
]

# ============================================================
# SUPERMARKET FORMS
# ============================================================

class SupermarketForm(forms.ModelForm):
    """Form for creating and editing supermarket profiles"""
    
    class Meta:
        model = Supermarket
        fields = ['shop_name', 'business_type', 'registration_number', 'phone_number', 
                  'physical_address', 'location_lat', 'location_lng', 'shop_image', 
                  'description', 'website', 'operating_hours', 'products_categories']
        widgets = {
            'shop_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Shop name'
            }),
            'business_type': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }),
            'registration_number': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Business registration number (optional)'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': '+254712345678 or 0712345678'
            }),
            'physical_address': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Complete physical address'
            }),
            'location_lat': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.0000001',
                'placeholder': 'Latitude (optional)'
            }),
            'location_lng': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.0000001',
                'placeholder': 'Longitude (optional)'
            }),
            'shop_image': forms.FileInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2',
                'accept': 'image/*'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 4,
                'placeholder': 'Describe your shop, mission, and what products you specialize in'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'https://example.com (optional)'
            }),
            'operating_hours': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Paste JSON format: {"monday": "08:00-18:00", "tuesday": "08:00-18:00", ...}'
            }),
            'products_categories': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Comma-separated product categories you sell (e.g., Seeds, Fertilizers, Tools, Chemicals)'
            }),
        }
    
    def clean_products_categories(self):
        categories_text = self.cleaned_data.get('products_categories')
        if categories_text:
            # Convert comma-separated string to list
            categories = [cat.strip() for cat in categories_text.split(',') if cat.strip()]
            return categories
        return []


class ProductListingStockForm(forms.ModelForm):
    """Form for managing product stock status in marketplace"""
    
    class Meta:
        model = ProductListing
        fields = ['is_out_of_stock']
        widgets = {
            'is_out_of_stock': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 focus:ring-red-500'
            }),
        }
        labels = {
            'is_out_of_stock': 'Mark this product as out of stock',
        }


class SupermarketProductListingForm(forms.ModelForm):
    """Form for supermarkets to list products for sale"""
    
    class Meta:
        model = ProductListing
        fields = ['product_name', 'category', 'description', 'quantity', 'unit', 
                  'price_per_unit', 'images', 'expiry_date', 'delivery_available', 'delivery_fee']
        widgets = {
            'product_name': forms.TextInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'placeholder': 'Product name'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500'
            }, choices=PRODUCT_CATEGORIES),
            'description': forms.Textarea(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'rows': 3,
                'placeholder': 'Describe your product (quality, brand, specifications, etc.)'
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
                'accept': 'image/*'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'type': 'date'
            }),
            'delivery_available': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-green-600 focus:ring-green-500'
            }),
            'delivery_fee': forms.NumberInput(attrs={
                'class': 'w-full border rounded-lg px-3 py-2 focus:outline-none focus:border-green-500',
                'step': '0.01',
                'min': '0',
                'placeholder': 'Delivery fee (if applicable)'
            }),
        }
