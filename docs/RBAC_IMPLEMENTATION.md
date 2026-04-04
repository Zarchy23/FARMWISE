# FARMWISE - RBAC IMPLEMENTATION GUIDE

## Overview

FarmWise implements a comprehensive Role-Based Access Control (RBAC) system for 10 different user types:
1. Smallholder Farmer
2. Large Scale Farmer
3. Cooperative Administrator
4. Agronomist / Extension Officer
5. Equipment Owner
6. Insurance Agent
7. Market Trader
8. Veterinarian
9. Soil Lab Technician
10. System Administrator

---

## QUICK START

### 1. Using Permissions in Views

#### Decorator-based approach
```python
from core.permissions import require_permission
from django.views import View

@require_permission('crops', 'create')
def create_crop(request):
    # Only users with crop creation permission can access
    pass
```

#### Mixin-based approach (Class-based views)
```python
from core.mixins import RoleRequiredMixin, FarmAccessMixin
from django.views.generic import CreateView

class CreateCropView(RoleRequiredMixin, CreateView):
    required_roles = ['farmer', 'large_farmer', 'agronomist']
    permission_module = 'crops'
    permission_action = 'create'
    model = Crop
    fields = ['name', 'variety']

class FarmDetailView(FarmAccessMixin, DetailView):
    model = Farm
    
    def get_farm(self):
        return self.get_object()
```

### 2. Using Permissions in Templates

Load the permission tags:
```django
{% load permissions %}
```

Check user role:
```django
{% if user|is_farmer %}
    <p>You are a farmer</p>
{% endif %}

{% if user|is_coop_admin %}
    <p>You are a cooperative admin</p>
{% endif %}
```

Check specific permission:
```django
{% if user|has_module_permission:"crops.create" %}
    <a href="{% url 'core:crop_create' %}">Create Crop</a>
{% endif %}
```

Conditional rendering:
```django
{% if user|can_edit:farm %}
    <a href="{% url 'core:farm_edit' farm.id %}">Edit Farm</a>
{% endif %}
```

Show content for specific roles:
```django
{% if "farmer,large_farmer"|show_if_role_in:user.user_type %}
    <div class="farmer-only-section">
        <!-- Content for farmers only -->
    </div>
{% endif %}
```

---

## PERMISSION MODULES & ACTIONS

### Farms Module
- `view_own` - View own farms
- `create` - Create new farm
- `edit_own` - Edit own farm
- `delete_own` - Delete own farm
- `view_coop` - View farms in cooperative (coop admin)
- `view_only` - Read-only view of farms

### Crops Module
- `view_own` - View own crops
- `create` - Create new crop
- `edit_own` - Edit own crop
- `delete_own` - Delete own crop
- `harvest` - Harvest crop (record harvest)
- `bulk_plant` - Plant multiple fields at once (large farmers)
- `view_only` - Read-only view
- `add_notes` - Add advisory notes (agronomist)

### Livestock Module
- `view_own` - View own animals
- `create` - Add new animal
- `edit_own` - Edit own animal
- `delete_own` - Delete own animal
- `health_record` - Add health records
- `view_only` - Read-only view

### Equipment Module
- `view_all` - View all equipment
- `view_own` - View own equipment
- `create` - List equipment for rental
- `edit_own` - Edit own equipment listing
- `delete_own` - Remove equipment listing
- `book` - Book equipment
- `manage_bookings` - Manage booking requests (owner)

### Marketplace Module
- `view_all` - View all listings
- `create_listing` - Create product listing
- `edit_own` - Edit own listing
- `delete_own` - Delete own listing
- `buy` - Purchase products
- `sell` - Sell products
- `bulk_listing` - Create bulk listings (market traders)
- `bulk_coordination` - Coordinate bulk operations (coop admin)
- `create_buy_orders` - Create buy orders (market traders)
- `price_analytics` - View price data (market traders)

### Pest Detection Module
- `view_own` - View own reports
- `view_all_pending` - View all pending reports (agronomist)
- `upload` - Upload pest photos
- `view_analysis` - View AI analysis
- `verify` - Verify pest reports (agronomist)
- `add_treatment` - Add treatment recommendations (agronomist)
- `send_alerts` - Send pest alerts (agronomist)

### Weather Module
- `view_all` - View weather data (everyone)

### Insurance Module
- `view_own` - View own policies
- `view_all` - View all policies (insurance agent)
- `buy` - Purchase insurance
- `claim` - File insurance claim
- `sell` - Sell policies (insurance agent)
- `process_claims` - Process claims (insurance agent)

### Labor Module
- `view_own` - View own workers
- `create` - Add worker
- `edit_own` - Edit own worker
- `manage_payroll` - Manage payroll (large farmers)

### Reports Module
- `view_own` - View own reports
- `view_coop` - View cooperative reports (coop admin)
- `view_assigned` - View assigned farm reports (agronomist)
- `generate_own` - Generate personal reports
- `generate_coop_reports` - Generate cooperative reports
- `sales` - View sales reports (market trader)
- `export` - Export reports
- `api_access` - API access (market trader)

### Cooperative Module (Coop Admin Only)
- `manage` - Manage cooperative
- `invite_members` - Invite members
- `view_members` - View member list
- `generate_reports` - Generate cooperative reports

---

## USING PERMISSION HELPER FUNCTIONS

### In views.py

```python
from core.permissions import (
    has_permission, can_access_farm, can_edit_farm,
    get_accessible_farms, get_accessible_animals
)

def farm_list(request):
    # Get all farms accessible to this user
    farms = get_accessible_farms(request.user)
    
    return render(request, 'farms/list.html', {'farms': farms})

def farm_detail(request, farm_id):
    farm = get_object_or_404(Farm, id=farm_id)
    
    # Check access permission
    if not can_access_farm(request.user, farm):
        raise PermissionDenied
    
    # Check edit permission
    can_edit = can_edit_farm(request.user, farm)
    
    return render(request, 'farms/detail.html', {
        'farm': farm,
        'can_edit': can_edit
    })

def create_crop(request):
    # Check permission
    if not has_permission(request.user, 'crops', 'create'):
        raise PermissionDenied
    
    # ... rest of view
```

---

## ASSIGNING FARMS TO AGRONOMISTS/VETERINARIANS

```python
# In Django shell or view
from core.models import User, Farm

agronomist = User.objects.get(username='john_agronomist')
farm = Farm.objects.get(id=1)

# Assign farm
agronomist.assigned_farms.add(farm)

# Assign multiple
agronomist.assigned_farms.add(farm1, farm2, farm3)

# Remove assignment
agronomist.assigned_farms.remove(farm)

# Get all assigned farms
assigned_farms = agronomist.assigned_farms.all()
```

---

## MANAGING COOPERATIVE MEMBERSHIP

```python
from core.models import User, Cooperative

# Create/get cooperative
coop = Cooperative.objects.create(
    name="Farmer's Union #123",
    registration_number="FU-2024-001",
    admin=User.objects.get(username='coop_admin')
)

# Add farmers to cooperative
farmer1 = User.objects.get(username='farmer1')
farmer2 = User.objects.get(username='farmer2')

farmer1.cooperative_member = coop
farmer1.save()

farmer2.cooperative_member = coop
farmer2.save()

# Get all members
members = coop.members.all()

# Deactivate member (but keep in system)
member = User.objects.get(username='farmer1')
member.is_active_member = False
member.save()
```

---

## CUSTOM PERMISSION OVERRIDES

Some permissions can be customized per user using the `permissions` JSON field:

```python
# In Django shell
user = User.objects.get(username='john')

# Give custom permission
user.permissions = {
    'crops': ['create', 'edit_all', 'delete_all'],  # Override defaults
    'marketplace': ['sell']
}
user.save()

# Check custom permission
if 'crops' in user.permissions and 'edit_all' in user.permissions['crops']:
    # User has custom crop edit permission
```

---

## SIDEBAR VISIBILITY CONTROL

The sidebar in `templates/base.html` already includes role-based visibility. Here are common patterns:

```django
<!-- Only farmers can see -->
{% if user.user_type in 'farmer,large_farmer,agronomist,admin' %}
<a href="{% url 'core:farm_list' %}">My Farms</a>
{% endif %}

<!-- Only cooperative admin -->
{% if user.user_type == 'cooperative_admin' %}
<a href="{% url 'core:coop_members' %}">Members</a>
{% endif %}

<!-- Farmers and equipment owners -->
{% if user.user_type in 'farmer,large_farmer,equipment_owner,admin' %}
<a href="{% url 'core:equipment_list' %}">Equipment</a>
{% endif %}
```

---

## QUERYSET FILTERING FOR ROLE-BASED DATA

For API views or list views, always filter querysets by user role:

```python
from core.permissions import get_accessible_farms

class FarmListView(ListAPIView):
    serializer_class = FarmSerializer
    
    def get_queryset(self):
        return get_accessible_farms(self.request.user)
```

---

## AUDIT LOGGING WITH RBAC

All major actions are logged in `AuditLog`:

```python
from core.models import AuditLog

# Automatically logged on create/update/delete through models
# Or manually:

AuditLog.objects.create(
    user=request.user,
    action='create',
    model_name='Farm',
    object_id=farm.id,
    details={'name': farm.name},
    ip_address=get_client_ip(request),
    user_agent=request.META.get('HTTP_USER_AGENT', '')
)
```

View audit logs:
```python
# Get user's actions
user_logs = request.user.audit_logs.all()

# Filter by action
create_logs = AuditLog.objects.filter(action='create')
```

---

## TESTING RBAC

```python
from django.test import TestCase
from core.models import User, Farm
from core.permissions import can_access_farm, can_edit_farm

class RBACTestCase(TestCase):
    def setUp(self):
        self.farmer = User.objects.create_user(
            username='farmer1',
            user_type='farmer'
        )
        self.other_farmer = User.objects.create_user(
            username='farmer2',
            user_type='farmer'
        )
        self.farm = Farm.objects.create(
            owner=self.farmer,
            name="Test Farm",
            farm_type='crop'
        )
    
    def test_owner_can_access_farm(self):
        self.assertTrue(can_access_farm(self.farmer, self.farm))
    
    def test_other_farmer_cannot_access_farm(self):
        self.assertFalse(can_access_farm(self.other_farmer, self.farm))
    
    def test_owner_can_edit_farm(self):
        self.assertTrue(can_edit_farm(self.farmer, self.farm))
    
    def test_other_farmer_cannot_edit_farm(self):
        self.assertFalse(can_edit_farm(self.other_farmer, self.farm))
```

---

## COMMON PATTERNS

### Pattern 1: Role-Required View
```python
@require_permission('crops', 'create')
@login_required
def create_crop(request):
    # Only users with crop creation permission
    pass
```

### Pattern 2: Owner-Only View
```python
@require_farm_edit()
def edit_farm(request, farm_id):
    farm = Farm.objects.get(id=farm_id)
    # User is verified to be owner
    pass
```

### Pattern 3: Cooperative-Wide View
```python
def coop_dashboard(request):
    if request.user.user_type != 'cooperative_admin':
        raise PermissionDenied
    
    farms = get_accessible_farms(request.user)  # Returns only coop farms
    # ...
```

### Pattern 4: Template Conditional Rendering
```django
{% load permissions %}

{% if user|is_farmer %}
    <a href="{% url 'core:crop_create' %}">Plant Crop</a>
{% elif user|is_veterinarian %}
    <a href="{% url 'core:health_record_add' %}">Add Health Record</a>
{% elif user|is_market_trader %}
    <a href="{% url 'core:marketplace_create_buy_order' %}">Create Buy Order</a>
{% endif %}
```

---

## TROUBLESHOOTING

### User sees everything (no RBAC working)
1. Check that user is not superuser (`user.is_superuser`)
2. Verify user's `user_type` is set correctly
3. Check that `permission_module` and `permission_action` match ROLE_PERMISSIONS

### Cooperatives not showing members
1. Verify members have `cooperative_member` ForeignKey set
2. Check `is_active_member` is True
3. Ensure cooperative admin's related farmer is looking at correct coop

### Database error on migration
1. Run `python manage.py makemigrations`
2. Run `python manage.py migrate`
3. Ensure models.py changes are saved before migrating

---

## NEXT STEPS

1. ✅ Implement the permission decorator/mixin usage in all views
2. ✅ Add template permission tags to navigation/actions
3. ✅ Test each role in development
4. ✅ Set up audit logging for compliance
5. ✅ Create role-specific dashboards
6. ✅ Document API endpoints with required roles
