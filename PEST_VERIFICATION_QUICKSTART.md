# Quick Start: Pest Detection Verification Workflow

## What Was Built

A complete pest detection verification system where:
1. **Farmers** submit pest photos for AI analysis
2. **System** automatically notifies assigned agronomists
3. **Agronomists** review in a professional dashboard
4. **Agronomists** approve/reject/request revision with comments
5. **Farmers** receive decision notifications with expert assessment

## Testing the Feature

### Step 1: Setup Test Accounts

```bash
# Access Django shell
python manage.py shell

from core.models import User, Farm

# Create test agronomist (if not exists)
agronomist = User.objects.create_user(
    username='agronomist_test',
    email='agronomist@test.com',
    first_name='John',
    last_name='Agronomist',
    phone_number='+254712345678',
    user_type='agronomist',
    password='testpass123'
)

# Create test farmer (if not exists)
farmer = User.objects.create_user(
    username='farmer_test',
    email='farmer@test.com',
    first_name='Jane',
    last_name='Farmer',
    phone_number='+254712345679',
    user_type='farmer',
    password='testpass123'
)

# Create test farm owned by farmer
farm = Farm.objects.create(
    owner=farmer,
    name='Test Farm',
    location='Test Location',
    size_hectares=5,
    soil_type='loamy'
)

# Assign farm to agronomist
agronomist.assigned_farms.add(farm)

exit()
```

### Step 2: Login as Farmer and Submit Pest Report

1. Go to `http://localhost:8000/`
2. Login as farmer (username: `farmer_test`, password: `testpass123`)
3. Navigate to `/pest-detection/`
4. Upload a crop image (any image works for testing)
5. Wait for AI analysis to complete
6. See the report created with status "pending"

### Step 3: Verify Farmer Received Notification

1. While logged in as farmer, go to `/notifications/`
2. Should see notification: "Pest Detection Review Needed - [pest name]"

### Step 4: Login as Agronomist and View Dashboard

1. Logout or open incognito window
2. Login as agronomist (username: `agronomist_test`, password: `testpass123`)
3. Go to `/pest-verification/dashboard/`
4. Should see:
   - Dashboard with stats (1 pending report)
   - Filter form
   - Table showing farmer's pest report

### Step 5: Review and Approve Report

1. Click "Review" button on the report
2. See full details:
   - Farmer info
   - Farm location
   - Pest image
   - AI diagnosis
   - Severity & confidence

### Step 6: Take Action

Choose one of three actions:

#### Option A: Approve Report
1. Scroll to "Approve Report" section
2. Select "✓ Approve - Diagnosis is correct"
3. Add professional assessment notes
4. Optionally adjust severity
5. Click "Approve Report" button

#### Option B: Reject Report
1. Scroll to "Reject Report" section
2. Enter reason (e.g., "Image quality too low")
3. Suggest action (e.g., "Please provide clearer photo")
4. Click "Reject Report" button

#### Option C: Request Revision
1. Scroll to "Request Revision" section
2. Specify what's needed (e.g., "Show diseased leaves from different angles")
3. Add helpful resource links (optional)
4. Click "Request Revision" button

### Step 7: Verify Farmer Received Decision

1. Logout and login as farmer
2. Go to `/pest-detection/` or `/pest-detection/history/`
3. View the pest report
4. See:
   - Status badge (Approved/Rejected/Needs Revision)
   - Agronomist's professional assessment/notes
   - Recommended actions

## URL Reference

### For Farmers:
- `/pest-detection/` - Upload pest image
- `/pest-detection/history/` - View all past reports
- `/pest-detection/<id>/` - View single report with status
- `/notifications/` - Check notifications

### For Agronomists:
- `/pest-verification/dashboard/` - Main verification dashboard
- `/pest-verification/<id>/` - Review individual report
- `/api/pest-reports/statistics/` - Dashboard statistics (JSON)

### API Endpoints (for AJAX):
- `POST /api/pest-reports/<id>/approve/` - Approve report
- `POST /api/pest-reports/<id>/reject/` - Reject report
- `GET /api/pest-reports/statistics/` - Get agronomist stats

## Expected Notification Messages

### Farmer Receives:

**On Submission:**
```
✓ Notification received
Your pest detection report has been submitted for verification.
An assigned agronomist will review this shortly.
```

**On Approval:**
```
✓ Success notification
Pest Report Approved - Your diagnosed pest

Your pest detection report for "Farm Name" has been APPROVED 
by agronomist John Agronomist.

Diagnosis: [Pest name]
Severity: High
Confidence: 87%

Professional Assessment: [Agronomist's notes]
Recommended Treatment: [Treatment details]
```

**On Rejection:**
```
⚠ Warning notification
Pest Report Needs Resubmission

Your pest report could not be verified.

Reason: Image quality too low to distinguish symptoms clearly
Please resubmit with a clearer photo focusing on affected leaf.
```

**On Revision Request:**
```
↻ Info notification
Pest Report - Revision Needed

Current AI Diagnosis: Leaf Spot Disease

Required Information:
Please show the diseased leaves from multiple angles,
especially the undersides where the fungus clearly shows.

Helpful Resources:
See attached guide on proper leaf sampling technique.
```

## Database Queries to Check

### See all pending reports:
```bash
python manage.py shell
from core.models import PestReport
pending = PestReport.objects.filter(status='pending')
for p in pending:
    print(f"{p.ai_diagnosis} - {p.farmer.get_full_name()} - Farm: {p.farm.name}")
```

### See all notifications:
```bash
from core.models import Notification
notifs = Notification.objects.all().order_by('-created_at')[:10]
for n in notifs:
    print(f"{n.user.username}: {n.title}")
```

### Check agronomist's assigned farms:
```bash
from core.models import User
agro = User.objects.get(username='agronomist_test')
print(agro.assigned_farms.all())
```

## Customization Examples

### Change notification message format:

In `views_pest_verification.py`, look for `send_notification()` calls:

```python
send_notification(
    user=report.farmer,
    title=f'✓ Pest Report Approved - {report.ai_diagnosis}',
    message="Your custom message here",  # ← Edit this
    notification_type='success',
    link=f'/pest-detection/{report.id}/'
)
```

### Change dashboard columns:

In `templates/pest/agronomist_dashboard.html`:

```html
<!-- Add columns to the table header -->
<thead class="table-light">
    <tr>
        <th>Farmer</th>
        <th>Farm</th>
        <th>Detected Issue</th>
        <th>Your Custom Column</th>  <!-- ← Add here -->
        <!-- ... -->
    </tr>
</thead>
```

### Restrict which agronomists see which reports:

In `views_pest_verification.py`, modify the query:

```python
# Current: Shows all farms assigned to agronomist
reports_query = PestReport.objects.filter(
    farm__in=assigned_farms
)

# Modified: Only show severe cases to some agronomists
if request.user.username == 'senior_agronomist':
    reports_query = reports_query.filter(severity='severe')
```

## Troubleshooting

### Issue: "Only agronomists can access this dashboard"
**Fix:** User account needs `user_type='agronomist'`
```bash
python manage.py shell
from core.models import User
u = User.objects.get(username='yourname')
u.user_type = 'agronomist'
u.save()
```

### Issue: Agronomist sees no reports
**Fix:** Assign farm to agronomist
```bash
python manage.py shell
from core.models import User, Farm
agronomist = User.objects.get(username='agronomist_test')
farm = Farm.objects.get(name='Test Farm')
agronomist.assigned_farms.add(farm)
```

### Issue: Notification not appearing
**Fix:** Check user notification preferences
```bash
python manage.py shell
from core.models import User
user = User.objects.get(username='farmer_test')
user.accepts_email = True
user.accepts_sms = True
user.save()
```

## Next Steps

1. **Test the complete workflow** following the steps above
2. **Check the documentation** at `PEST_VERIFICATION_WORKFLOW.md`
3. **Deploy to Render** with test accounts
4. **Collect user feedback** on the UI/workflow
5. **Consider enhancements:**
   - Email notifications for agronomists
   - SMS notifications for urgent cases
   - Batch approval for multiple reports
   - Analytics dashboard for pest trends
   - Integration with weather data for pest prediction

## Support Resources

- Full implementation docs: `PEST_VERIFICATION_WORKFLOW.md`
- Code files:
  - Forms: `core/forms_pest_verification.py`
  - Views: `core/views_pest_verification.py`
  - Templates: `templates/pest/agronomist_dashboard.html` & `verification_detail.html`
- Database: `core/models.py` (PestReport model)
