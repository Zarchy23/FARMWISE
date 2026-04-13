# core/urls_supermarket.py
# Supermarket Management URLs

from django.urls import path
from . import views_supermarket

app_name = 'supermarket'

urlpatterns = [
    # Supermarket Profile
    path('profile/', views_supermarket.supermarket_profile, name='profile'),
    path('profile/create/', views_supermarket.supermarket_profile_create, name='profile_create'),
    path('profile/edit/', views_supermarket.supermarket_profile_edit, name='profile_edit'),
    
    # Supermarket Dashboard
    path('dashboard/', views_supermarket.supermarket_dashboard, name='dashboard'),
    
    # Product Management
    path('products/', views_supermarket.supermarket_products_list, name='products_list'),
    path('products/add/', views_supermarket.supermarket_product_add, name='product_add'),
    path('products/<int:pk>/edit/', views_supermarket.supermarket_product_edit, name='product_edit'),
    path('products/<int:pk>/toggle-stock/', views_supermarket.supermarket_product_toggle_stock, name='product_toggle_stock'),
    path('products/<int:pk>/delete/', views_supermarket.supermarket_product_delete, name='product_delete'),
    
    # Export & Reports
    path('export/products/', views_supermarket.export_products, name='export_products'),
    path('export/sales/', views_supermarket.export_sales, name='export_sales'),
    path('export/inventory/', views_supermarket.export_inventory, name='export_inventory'),
    path('export/transactions/', views_supermarket.export_transactions, name='export_transactions'),
]
