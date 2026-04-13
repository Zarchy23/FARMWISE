# core/views_supermarket.py
# Supermarket Management Views

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
from .models import Supermarket, ProductListing, User, Order, Transaction
from .forms_supermarket import SupermarketForm, ProductListingStockForm, SupermarketProductListingForm
from .export_service import ExportService
from .permissions import has_permission

# ============================================================
# SUPERMARKET PROFILE MANAGEMENT
# ============================================================

@login_required
def supermarket_profile(request):
    """View supermarket profile"""
    if request.user.user_type != 'supermarket':
        messages.error(request, 'This page is only for supermarket accounts.')
        return redirect('core:dashboard')
    
    try:
        supermarket = request.user.supermarket_profile
    except Supermarket.DoesNotExist:
        supermarket = None
    
    # Get supermarket statistics
    stats = {}
    if supermarket:
        total_products = ProductListing.objects.filter(seller__owner=request.user).count()
        active_products = ProductListing.objects.filter(seller__owner=request.user, status='active', is_out_of_stock=False).count()
        out_of_stock_products = ProductListing.objects.filter(seller__owner=request.user, is_out_of_stock=True).count()
        total_orders = 0  # Will depend on order model implementation
        
        stats = {
            'total_products': total_products,
            'active_products': active_products,
            'out_of_stock_products': out_of_stock_products,
            'total_orders': total_orders,
        }
    
    return render(request, 'supermarket/profile.html', {
        'supermarket': supermarket,
        'stats': stats
    })


@login_required
def supermarket_profile_create(request):
    """Create supermarket profile"""
    if request.user.user_type != 'supermarket':
        messages.error(request, 'This page is only for supermarket accounts.')
        return redirect('core:dashboard')
    
    # Check if profile already exists
    try:
        supermarket = request.user.supermarket_profile
        return redirect('core:supermarket_profile_edit')
    except Supermarket.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = SupermarketForm(request.POST, request.FILES)
        if form.is_valid():
            supermarket = form.save(commit=False)
            supermarket.owner = request.user
            supermarket.save()
            messages.success(request, f'Supermarket profile "{supermarket.shop_name}" created successfully!')
            return redirect('core:supermarket_profile')
    else:
        form = SupermarketForm()
    
    return render(request, 'supermarket/profile_create.html', {'form': form})


@login_required
def supermarket_profile_edit(request):
    """Edit supermarket profile"""
    if request.user.user_type != 'supermarket':
        messages.error(request, 'This page is only for supermarket accounts.')
        return redirect('core:dashboard')
    
    supermarket = get_object_or_404(Supermarket, owner=request.user)
    
    if request.method == 'POST':
        form = SupermarketForm(request.POST, request.FILES, instance=supermarket)
        if form.is_valid():
            form.save()
            messages.success(request, 'Supermarket profile updated successfully!')
            return redirect('core:supermarket_profile')
    else:
        form = SupermarketForm(instance=supermarket)
    
    return render(request, 'supermarket/profile_edit.html', {'form': form, 'supermarket': supermarket})


# ============================================================
# SUPERMARKET PRODUCT LISTING MANAGEMENT
# ============================================================

@login_required
def supermarket_products_list(request):
    """List all products for a supermarket"""
    if request.user.user_type != 'supermarket':
        messages.error(request, 'This page is only for supermarket accounts.')
        return redirect('core:dashboard')
    
    try:
        supermarket = request.user.supermarket_profile
    except Supermarket.DoesNotExist:
        messages.error(request, 'Please complete your supermarket profile first.')
        return redirect('core:supermarket_profile_create')
    
    # Get all products listed by this supermarket
    products = ProductListing.objects.filter(seller__owner=request.user).order_by('-created_at')
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        products = products.filter(status=status_filter)
    
    # Filter by stock status
    stock_filter = request.GET.get('stock', '')
    if stock_filter == 'in_stock':
        products = products.filter(is_out_of_stock=False)
    elif stock_filter == 'out_of_stock':
        products = products.filter(is_out_of_stock=True)
    
    # Get statistics
    total_products = products.count()
    active_products = products.filter(status='active', is_out_of_stock=False).count()
    out_of_stock_products = products.filter(is_out_of_stock=True).count()
    unpublished_products = products.exclude(status='active').count()
    
    context = {
        'products': products,
        'supermarket': supermarket,
        'total_products': total_products,
        'active_products': active_products,
        'out_of_stock_products': out_of_stock_products,
        'unpublished_products': unpublished_products,
        'status_filter': status_filter,
        'stock_filter': stock_filter,
    }
    
    return render(request, 'supermarket/products_list.html', context)


@login_required
def supermarket_product_add(request):
    """Add a new product to supermarket"""
    if request.user.user_type != 'supermarket':
        messages.error(request, 'This page is only for supermarket accounts.')
        return redirect('core:dashboard')
    
    try:
        supermarket = request.user.supermarket_profile
    except Supermarket.DoesNotExist:
        messages.error(request, 'Please complete your supermarket profile first.')
        return redirect('core:supermarket_profile_create')
    
    # Supermarkets need a farm to create listings - create a default farm
    from .models import Farm
    try:
        farm = Farm.objects.get(owner=request.user, name=f"{supermarket.shop_name} Products")
    except Farm.DoesNotExist:
        farm = Farm.objects.create(
            owner=request.user,
            name=f"{supermarket.shop_name} Products",
            farm_type='other',
            total_area_hectares=0,
        )
    
    if request.method == 'POST':
        form = SupermarketProductListingForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = farm
            product.save()
            
            messages.success(request, f'Product "{product.product_name}" added to marketplace!')
            return redirect('core:supermarket_products_list')
    else:
        form = SupermarketProductListingForm()
    
    return render(request, 'supermarket/product_add.html', {'form': form, 'supermarket': supermarket})


@login_required
def supermarket_product_edit(request, pk):
    """Edit product listing"""
    if request.user.user_type != 'supermarket':
        messages.error(request, 'This page is only for supermarket accounts.')
        return redirect('core:dashboard')
    
    product = get_object_or_404(ProductListing, pk=pk, seller__owner=request.user)
    
    if request.method == 'POST':
        form = SupermarketProductListingForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('core:supermarket_products_list')
    else:
        form = SupermarketProductListingForm(instance=product)
    
    return render(request, 'supermarket/product_edit.html', {'form': form, 'product': product})


@login_required
def supermarket_product_toggle_stock(request, pk):
    """Toggle product out of stock status"""
    if request.user.user_type != 'supermarket':
        messages.error(request, 'This page is only for supermarket accounts.')
        return redirect('core:dashboard')
    
    product = get_object_or_404(ProductListing, pk=pk, seller__owner=request.user)
    
    if request.method == 'POST':
        form = ProductListingStockForm(request.POST, instance=product)
        if form.is_valid():
            old_status = product.is_out_of_stock
            form.save()
            new_status = product.is_out_of_stock
            
            if old_status != new_status:
                if new_status:
                    # Creating out of stock - generate notification and reminder
                    from .models import Reminder, Notification
                    
                    # Create notification
                    Notification.objects.create(
                        user=request.user,
                        notification_type='warning',
                        title=f'Out of Stock: {product.product_name}',
                        message=f'Product "{product.product_name}" is now out of stock. Set a reminder to restock!',
                        link=f'/supermarket/products/{product.pk}/edit/'
                    )
                    
                    # Create reminder for restocking
                    from django.utils import timezone
                    today = timezone.now().date()
                    Reminder.objects.get_or_create(
                        farm=product.seller,
                        user=request.user,
                        title=f'Restock: {product.product_name}',
                        reminder_type='general',
                        due_date=today,
                        defaults={
                            'is_active': True,
                            'description': f'Product "{product.product_name}" is out of stock. Please arrange restocking soon to maintain customer satisfaction.'
                        }
                    )
                    
                    messages.success(request, f'"{product.product_name}" marked as OUT OF STOCK. A reminder has been created for restocking.')
                else:
                    messages.success(request, f'"{product.product_name}" marked as IN STOCK. It is now visible in the public marketplace.')
            
            return redirect('core:supermarket_products_list')
    else:
        form = ProductListingStockForm(instance=product)
    
    return render(request, 'supermarket/product_toggle_stock.html', {'form': form, 'product': product})


@login_required
def supermarket_product_delete(request, pk):
    """Delete a product listing"""
    if request.user.user_type != 'supermarket':
        messages.error(request, 'This page is only for supermarket accounts.')
        return redirect('core:dashboard')
    
    product = get_object_or_404(ProductListing, pk=pk, seller__owner=request.user)
    
    if request.method == 'POST':
        product_name = product.product_name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('core:supermarket_products_list')
    
    return render(request, 'supermarket/product_delete.html', {'product': product})


# ============================================================
# USER DASHBOARD VIEW FOR SUPERMARKET
# ============================================================

@login_required
def supermarket_dashboard(request):
    """Supermarket user dashboard with out-of-stock products visible"""
    if request.user.user_type != 'supermarket':
        messages.error(request, 'This page is only for supermarket accounts.')
        return redirect('core:dashboard')
    
    try:
        supermarket = request.user.supermarket_profile
    except Supermarket.DoesNotExist:
        return redirect('core:supermarket_profile_create')
    
    # Get ALL products (including out of stock)
    all_products = ProductListing.objects.filter(seller__owner=request.user).order_by('-created_at')
    
    # Statistics
    total_products = all_products.count()
    public_products = all_products.filter(status='active', is_out_of_stock=False).count()
    out_of_stock_products = all_products.filter(is_out_of_stock=True).count()
    inactive_products = all_products.exclude(status='active').count()
    
    # Recent products
    recent_products = all_products[:10]
    
    # Recent out-of-stock updates
    recent_oos = all_products.filter(is_out_of_stock=True).order_by('-updated_at')[:5]
    
    context = {
        'supermarket': supermarket,
        'total_products': total_products,
        'public_products': public_products,
        'out_of_stock_products': out_of_stock_products,
        'inactive_products': inactive_products,
        'recent_products': recent_products,
        'recent_out_of_stock': recent_oos,
    }
    
    return render(request, 'supermarket/dashboard.html', context)


# ============================================================
# EXPORT FUNCTIONALITY - FOR REPORTS & ANALYTICS
# ============================================================

@login_required
def export_products(request):
    """Export supermarket products with applied filters"""
    if not has_permission(request.user, 'reports', 'export_all'):
        messages.error(request, 'You do not have permission to export reports.')
        return redirect('core:supermarket_dashboard')
    
    # Get filter parameters
    format_choice = request.GET.get('format', 'csv')
    status_filter = request.GET.get('status', 'all')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Parse dates
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except:
            start_date = None
    else:
        start_date = timezone.now().date() - timedelta(days=365)
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except:
            end_date = None
    else:
        end_date = timezone.now().date()
    
    # Get products with filters
    try:
        response, filename = ExportService.export_marketplace_products(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            format=format_choice,
            status_filter=status_filter
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('core:supermarket_products_list')


@login_required
def export_sales(request):
    """Export supermarket sales/orders with filters"""
    if not has_permission(request.user, 'reports', 'export_all'):
        messages.error(request, 'You do not have permission to export reports.')
        return redirect('core:supermarket_dashboard')
    
    # Get filter parameters
    format_choice = request.GET.get('format', 'csv')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Parse dates
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except:
            start_date = None
    else:
        start_date = timezone.now().date() - timedelta(days=90)
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except:
            end_date = None
    else:
        end_date = timezone.now().date()
    
    try:
        response, filename = ExportService.export_marketplace_sales(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('core:supermarket_products_list')


@login_required
def export_inventory(request):
    """Export current inventory report"""
    if not has_permission(request.user, 'reports', 'export_all'):
        messages.error(request, 'You do not have permission to export reports.')
        return redirect('core:supermarket_dashboard')
    
    format_choice = request.GET.get('format', 'csv')
    
    try:
        response, filename = ExportService.export_marketplace_inventory_report(
            user=request.user,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('core:supermarket_dashboard')


@login_required
def export_transactions(request):
    """Export financial transactions"""
    if not has_permission(request.user, 'reports', 'export_all'):
        messages.error(request, 'You do not have permission to export reports.')
        return redirect('core:supermarket_dashboard')
    
    format_choice = request.GET.get('format', 'csv')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Parse dates
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except:
            start_date = None
    else:
        start_date = timezone.now().date() - timedelta(days=365)
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except:
            end_date = None
    else:
        end_date = timezone.now().date()
    
    try:
        response, filename = ExportService.export_supermarket_transactions(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            format=format_choice
        )
        messages.success(request, f'Successfully exported {filename}')
        return response
    except Exception as e:
        messages.error(request, f'Error exporting data: {str(e)}')
        return redirect('core:supermarket_dashboard')
