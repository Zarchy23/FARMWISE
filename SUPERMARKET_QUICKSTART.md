# SUPERMARKET FEATURE - QUICK START GUIDE

## What Was Added

### For Users:
- **Supermarket Registration**: New user type "Supermarket/Agricultural Shop" in registration
- **Shop Profile**: Complete shop management with location, operating hours, and product categories
- **Product Listing**: List agricultural products/supplies for sale
- **Stock Management**: Mark products as out-of-stock without deletion
- **Dashboard**: Private dashboard showing ALL products including out-of-stock items

### For System:
- **Admin-Only Access**: System administrators can ONLY be created via `createsuperuser` command, NOT through registration
- **Marketplace Privacy**: Out-of-stock products hidden from public marketplace, visible in user dashboards
- **Database**: New Supermarket table + is_out_of_stock field on products table

---

## USER FLOW

### Step 1: Registration
```
User visits registration page
↓
Selects "Supermarket/Agricultural Shop" as user type
↓
System creates User with user_type = 'supermarket'
(Note: 'admin' is NOT available in dropdown - only via createsuperuser)
```

### Step 2: Complete Shop Profile
```
Supermarket user logged in
↓
Redirected to create shop profile if not exists
↓
Fill in: Shop name, address, phone, categories, operating hours, etc.
↓
Profile saved to Supermarket table
```

### Step 3: Add Products
```
Go to "Manage Products" section
↓
Create new product listing
↓
Enter: Product name, category, price, quantity, image, etc.
↓
Product appears in public marketplace (visible to all buyers)
```

### Step 4: Stock Management
```
User views their products list
↓
Clicks "Mark Out of Stock" on a product
↓
Product is REMOVED from public marketplace
↓
Product STAYS in user's private dashboard
↓
User can restore it to "In Stock" anytime
```

### Step 5: Admin Creation
```
# For system administrators, use command line:
python manage.py createsuperuser

# Answer prompts:
# - Username: admin
# - Email: admin@example.com
# - Password: (secure password)

# Result: User created with user_type = 'admin'
# This user can access Django admin and system settings
```

---

## DATABASE SCHEMA

### Supermarket Model
```
supermarkets table:
├── id (Primary Key)
├── owner_id (Foreign Key to User)
├── shop_name
├── business_type (retail, wholesale, coop, agro-dealer, hardware, other)
├── registration_number (optional, unique)
├── phone_number
├── physical_address
├── location_lat, location_lng (GPS coordinates)
├── shop_image
├── description
├── website
├── operating_hours (JSON: {"monday": "08:00-18:00", ...})
├── products_categories (JSON: ["Seeds", "Fertilizers", ...])
├── is_verified (default: False)
├── is_active (default: True)
├── created_at, updated_at
```

### ProductListing Changes
```
product_listings table:
├── ... (existing fields)
├── is_out_of_stock (new field, default: False)  ← OUT OF STOCK FLAG
├── ... (rest of fields)
```

---

## KEY FEATURES EXPLAINED

### 1. Admin User Creation
**Why not in registration?**
- Security: Prevents accidental admin creation
- Control: Only trusted setup process can create admins
- Intentional: Use `python manage.py createsuperuser` command

**Command:**
```bash
python manage.py createsuperuser
# Creates user with special admin privileges
```

### 2. Out-of-Stock Products
**How it works:**
```
When product is marked "out of stock":
✅ Stays in seller's dashboard
✅ Preserves all product information
✅ Hidden from public marketplace
✅ Can be restored with one click
❌ Does NOT appear in buyer searches
❌ Does NOT block other products from showing
```

**Why not delete?**
- Preserves history and statistics
- Avoids accidental data loss
- Easy to restore if needed
- Good for seasonal products

### 3. Marketplace Filtering
**Public Marketplace shows:**
- Active products
- With is_out_of_stock = False
- Buyers can search & browse freely

**Supermarket Dashboard shows:**
- All products (active + out of stock)
- Statistics on public vs. private
- Easy stock toggle

---

## IMPLEMENTATION CHECKLIST

### Backend Implementation ✅
- [x] Supermarket model created
- [x] is_out_of_stock field added to ProductListing
- [x] Forms created for supermarket management
- [x] Views created for all supermarket functions
- [x] URLs configured for supermarket routes
- [x] Marketplace view updated to exclude out-of-stock
- [x] Admin user filtering in registration

### Database Migrations (TO DO)
- [ ] `python manage.py makemigrations`
- [ ] `python manage.py migrate`

### Configuration (TO DO)
- [ ] Update `core/urls.py` to include supermarket URLs
- [ ] Register Supermarket model in `core/admin.py`
- [ ] Update base template navigation

### Templates (TO DO)
- [ ] `templates/supermarket/profile.html`
- [ ] `templates/supermarket/profile_create.html` 
- [ ] `templates/supermarket/profile_edit.html`
- [ ] `templates/supermarket/products_list.html`
- [ ] `templates/supermarket/product_add.html`
- [ ] `templates/supermarket/product_edit.html`
- [ ] `templates/supermarket/product_toggle_stock.html`
- [ ] `templates/supermarket/product_delete.html`
- [ ] `templates/supermarket/dashboard.html`

### Testing (TO DO)
- [ ] Register as supermarket user
- [ ] Create shop profile
- [ ] Add product to marketplace
- [ ] Mark product as out of stock
- [ ] Verify it's hidden from public marketplace
- [ ] Verify it's visible in user dashboard
- [ ] Restore product to in stock
- [ ] Verify admin-only registration restriction
- [ ] Test createsuperuser command

---

## API ENDPOINTS

### Supermarket Profile
- `GET /supermarket/profile/` - View profile
- `POST/GET /supermarket/profile/create/` - Create profile
- `POST/GET /supermarket/profile/edit/` - Edit profile

### Product Management
- `GET /supermarket/products/` - List all products
- `POST/GET /supermarket/products/add/` - Add product
- `POST/GET /supermarket/products/<id>/edit/` - Edit product
- `POST /supermarket/products/<id>/toggle-stock/` - Toggle out-of-stock
- `POST/GET /supermarket/products/<id>/delete/` - Delete product

### Dashboard
- `GET /supermarket/dashboard/` - Admin dashboard with all products

---

## EXAMPLE QUERIES

### Show all out-of-stock products in dashboard
```python
from core.models import ProductListing

# Get all out-of-stock products for a user
oos_products = ProductListing.objects.filter(
    seller__owner=request.user, 
    is_out_of_stock=True
)
```

### Show public marketplace (excludes out-of-stock)
```python
# Public marketplace - what buyers see
public_products = ProductListing.objects.filter(
    status='active',
    is_out_of_stock=False  # ← Key filter
)
```

### Get supermarket statistics
```python
from django.db.models import Count

stats = {
    'total': ProductListing.objects.filter(seller__owner=user).count(),
    'public': ProductListing.objects.filter(
        seller__owner=user, 
        status='active', 
        is_out_of_stock=False
    ).count(),
    'oos': ProductListing.objects.filter(
        seller__owner=user, 
        is_out_of_stock=True
    ).count(),
}
```

---

## AFTER IMPLEMENTATION

### Test the Full Workflow:
1. Visit registration page
2. Register as "Supermarket" (note: "System Administrator" not available)
3. Complete shop profile
4. Add a product
5. Visit marketplace - see product listed
6. Go to dashboard - mark product as "Out of Stock"
7. Visit marketplace again - product is GONE
8. Go to dashboard - product is still VISIBLE
9. Mark as "In Stock" - appears in marketplace again

### Admin Creation:
```bash
# In terminal:
python manage.py createsuperuser

# Then test:
# - Login with admin account
# - Should have access to /admin panel
# - Not able to register as admin through normal registration
```

---

## FILES SUMMARY

| File | Changes |
|------|---------|
| `core/models.py` | Added Supermarket model + is_out_of_stock field |
| `core/forms.py` | Filtered out 'admin' from registration |
| `core/forms_supermarket.py` | NEW: Supermarket-specific forms |
| `core/views.py` | Updated marketplace_list() filtering |
| `core/views_supermarket.py` | NEW: All supermarket views |
| `core/urls_supermarket.py` | NEW: URL routing for supermarket |

---

## SUPPORT

For issues or questions:
1. Check `SUPERMARKET_IMPLEMENTATION.md` for detailed info
2. Verify migrations ran successfully
3. Check templates are created with proper paths
4. Use Django admin to verify Supermarket model created
5. Check browser console for JavaScript errors
