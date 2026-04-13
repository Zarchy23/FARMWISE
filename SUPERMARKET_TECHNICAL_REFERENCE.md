# SUPERMARKET FEATURE - TECHNICAL REFERENCE

## Code Changes Summary

### 1. Model Changes

#### `core/models.py` - Added Supermarket Model
```python
class Supermarket(models.Model):
    """Supermarket/Agricultural Shop Profile"""
    
    BUSINESS_TYPES = [
        ('retail', 'Retail Shop'),
        ('wholesale', 'Wholesale Distributor'),
        ('cooperative_shop', 'Cooperative Shop'),
        ('agro_dealer', 'Agro-Dealer'),
        ('hardware', 'Agricultural Hardware'),
        ('other', 'Other'),
    ]
    
    owner = OneToOneField(User, on_delete=CASCADE, related_name='supermarket_profile')
    shop_name = CharField(max_length=255)
    business_type = CharField(max_length=20, choices=BUSINESS_TYPES)
    registration_number = CharField(max_length=100, blank=True, unique=True, null=True)
    phone_number = CharField(max_length=20)
    physical_address = TextField()
    location_lat = DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_lng = DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    shop_image = ImageField(upload_to='supermarket/logos/', null=True, blank=True)
    description = TextField(blank=True)
    website = URLField(blank=True)
    operating_hours = JSONField(default=dict, blank=True)
    products_categories = JSONField(default=list, blank=True)
    is_verified = BooleanField(default=False)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

#### `core/models.py` - ProductListing Field Addition
```python
class ProductListing(models.Model):
    # ... existing fields ...
    is_out_of_stock = BooleanField(
        default=False,
        help_text='When marked out of stock: hidden from public marketplace but visible in seller dashboard'
    )
    
    # Updated indexes:
    class Meta:
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['seller', 'is_out_of_stock']),  # ← NEW
            models.Index(fields=['category']),
            models.Index(fields=['created_at']),
        ]
```

#### `core/models.py` - User Model Update
```python
class User(AbstractUser):
    USER_TYPES = [
        # ... existing types ...
        ('supermarket', 'Supermarket/Agricultural Shop'),  # ← NEW
        ('admin', 'System Administrator'),  # Kept but filtered in forms
    ]
```

---

### 2. Form Changes

#### `core/forms.py` - Registration Form Update
```python
class UserRegistrationForm(UserCreationForm):
    user_type = forms.ChoiceField(
        # Filter out 'admin' during form instantiation
        choices=[choice for choice in User.USER_TYPES if choice[0] != 'admin'],
        required=True,
        label='User Type',
        help_text='Select your role on FarmWise',
        widget=forms.Select(attrs={...})
    )
```

#### `core/forms_supermarket.py` - New Supermarket Forms
```python
class SupermarketForm(forms.ModelForm):
    """Complete profile management"""
    # Handles all shop profile fields

class ProductListingStockForm(forms.ModelForm):
    """Simple stock toggle form"""
    class Meta:
        fields = ['is_out_of_stock']

class SupermarketProductListingForm(forms.ModelForm):
    """Specialized product form for supermarkets"""
    # Agriculture-focused categories
```

---

### 3. View Changes

#### `core/views.py` - Marketplace View Update
```python
@login_required
def marketplace_list(request):
    """List all products for sale with search and filters - EXCLUDES OUT OF STOCK items"""
    # Filter for active listings that are NOT marked as out of stock
    listings = ProductListing.objects.filter(
        status='active', 
        is_out_of_stock=False  # ← KEY CHANGE
    ).order_by('-created_at')
    
    # ... rest of filtering logic ...
```

#### `core/views_supermarket.py` - Supermarket Views (NEW)

**Profile Management:**
```python
@login_required
def supermarket_profile(request):
    # Check user_type == 'supermarket'
    # Get Supermarket profile
    # Show statistics

@login_required
def supermarket_profile_create(request):
    # Check if profile exists
    # Create new supermarket profile
    
@login_required
def supermarket_profile_edit(request):
    # Edit supermarket profile
```

**Product Management:**
```python
@login_required
def supermarket_products_list(request):
    # List ALL products (including out-of-stock)
    # Filter by status and stock status
    # Show statistics

@login_required
def supermarket_product_add(request):
    # Create product listing
    # Auto-create farm if needed

@login_required
def supermarket_product_toggle_stock(request, pk):
    # Toggle is_out_of_stock status
    # Product removed from public, stays in dashboard

@login_required
def supermarket_product_delete(request, pk):
    # Delete product completely
```

**Dashboard:**
```python
@login_required
def supermarket_dashboard(request):
    # Show ALL products (public + private)
    # Statistics on stock status
    # Recent updates
```

---

### 4. URL Routes

#### `core/urls_supermarket.py` - New URL Namespace
```python
app_name = 'supermarket'

urlpatterns = [
    path('profile/', supermarket_profile, name='profile'),
    path('profile/create/', supermarket_profile_create, name='profile_create'),
    path('profile/edit/', supermarket_profile_edit, name='profile_edit'),
    
    path('dashboard/', supermarket_dashboard, name='dashboard'),
    
    path('products/', supermarket_products_list, name='products_list'),
    path('products/add/', supermarket_product_add, name='product_add'),
    path('products/<int:pk>/edit/', supermarket_product_edit, name='product_edit'),
    path('products/<int:pk>/toggle-stock/', supermarket_product_toggle_stock, name='product_toggle_stock'),
    path('products/<int:pk>/delete/', supermarket_product_delete, name='product_delete'),
]
```

**Then in `core/urls.py`:**
```python
urlpatterns = [
    # ... existing paths ...
    path('supermarket/', include('core.urls_supermarket')),  # ← ADD THIS
]
```

---

## Database Migrations

### Generate Migration
```bash
python manage.py makemigrations
```

This will create a migration file that:
1. Creates `supermarkets` table with all fields
2. Adds `is_out_of_stock` field to `product_listings` table
3. Creates indexes for performance

### Apply Migration
```bash
python manage.py migrate
```

### Verify Migration
```bash
python manage.py showmigrations
# Should show migration as [X] (applied)
```

---

## Admin Registration

### Using createsuperuser Command
```bash
python manage.py createsuperuser
```

**Process:**
```
Username: admin
Email address: admin@farmwise.local
Password: 
Password (again): 
Superuser created successfully.
```

**Result:**
- User created with `is_active=True` and `is_staff=True`
- User can access `/admin` panel
- User marked as 'admin' type in system

### Programmatic Admin Creation (Not Recommended)
```python
from django.contrib.auth import get_user_model
User = get_user_model()

admin_user = User.objects.create_superuser(
    username='admin',
    email='admin@farmwise.local',
    password='secure_password',
    user_type='admin'
)
```

---

## Key Implementation Details

### 1. Admin Type Filtering
```python
# In registration form
choices=[choice for choice in User.USER_TYPES if choice[0] != 'admin']

# Result: Only these types available in dropdown:
# - farmer, large_farmer, cooperative_admin
# - agronomist, equipment_owner, insurance_agent
# - market_trader, veterinarian, lab_technician
# - supermarket 

# NOT available: admin (must use createsuperuser)
```

### 2. Out-of-Stock Logic
```python
# Public marketplace
listings = ProductListing.objects.filter(
    status='active',
    is_out_of_stock=False
)

# Supermarket dashboard (ALL products)
all_listings = ProductListing.objects.filter(
    seller__owner=current_user
)
# Shows both is_out_of_stock=True and False
```

### 3. Automatic Farm Creation
```python
# When supermarket adds first product, system auto-creates farm:

from core.models import Farm

farm, created = Farm.objects.get_or_create(
    owner=request.user,
    name=f"{supermarket.shop_name} Products",
    defaults={
        'farm_type': 'other',
        'total_area_hectares': 0,
    }
)

# Then product linked to this farm
product.seller = farm
product.save()
```

### 4. Verification System
```python
# Supermarket has verification field:
supermarket.is_verified  # Boolean

# Use for future:
# - Admin approval before listed products show
# - Display verified badge in marketplace
# - Filter queries for verified only:
listings = ProductListing.objects.filter(
    seller__owner__supermarket_profile__is_verified=True
)
```

---

## Query Examples

### Get Supermarket Products
```python
from core.models import ProductListing, Supermarket

# All products by supermarket
user = request.user
products = ProductListing.objects.filter(seller__owner=user)

# Public products only (what buyers see)
public = products.filter(status='active', is_out_of_stock=False)

# Out-of-stock products
oos = products.filter(is_out_of_stock=True)
```

### Get Supermarket Stats
```python
from django.db.models import Count

user = request.user
products = ProductListing.objects.filter(seller__owner=user)

stats = {
    'total': products.count(),
    'public': products.filter(
        status='active', 
        is_out_of_stock=False
    ).count(),
    'out_of_stock': products.filter(
        is_out_of_stock=True
    ).count(),
    'by_category': products.values('category').annotate(
        count=Count('id')
    ).order_by('-count'),
}
```

### Search Out-of-Stock Products
```python
# Find all out-of-stock products in marketplace
oos_products = ProductListing.objects.filter(
    is_out_of_stock=True,
    seller__owner__user_type='supermarket'
).select_related('seller__owner')

# By category
oos_seeds = oos_products.filter(category='Seeds & Seedlings')

# Recently updated
recent_oos = oos_products.order_by('-updated_at')[:10]
```

---

## Security Considerations

### 1. URL Access Control
All supermarket views check:
```python
if request.user.user_type != 'supermarket':
    messages.error(request, 'This page is only for supermarket accounts.')
    return redirect('core:dashboard')
```

### 2. Object Access Control
```python
# Ensure user can only access their own products
product = ProductListing.objects.get(
    pk=pk,
    seller__owner=request.user  # ← Prevents unauthorized access
)
```

### 3. Admin Protection
- Admin cannot be created through registration
- Only via `createsuperuser` command
- Prevents privilege escalation attacks

---

## Testing Checklist

- [ ] Supermarket user can register
- [ ] Admin type NOT in registration dropdown
- [ ] Supermarket profile creation works
- [ ] Products added to marketplace
- [ ] Out-of-stock toggle removes from public
- [ ] Out-of-stock products visible in dashboard
- [ ] Marketplace search excludes out-of-stock
- [ ] Admin user created via createsuperuser works
- [ ] Django admin panel accessible for admin user
- [ ] Non-supermarket cannot access supermarket URLs

---

## Performance Notes

### Indexes Added
```python
models.Index(fields=['seller', 'is_out_of_stock'])
```

This speeds up queries like:
```python
ProductListing.objects.filter(
    seller=farm,
    is_out_of_stock=False  # ← Indexed
)
```

### Benefits
- Faster marketplace queries (exclude out-of-stock hundreds of times/second)
- Better dashboard load times
- Scales with large product databases

---

## Future Enhancements

1. **Verification System**: Admin approval before supermarket can list
2. **Ratings/Reviews**: Buyer feedback on supermarket
3. **Order History**: Track which products were ordered
4. **Bulk Stock Update**: Manage multiple products at once
5. **Inventory Tracking**: Monitor stock levels over time
6. **Product Variations**: Sizes, colors, quantities within one product
7. **Seasonal Products**: Auto-hide/show based on season
8. **Commission/Fees**: Track earnings per product category
