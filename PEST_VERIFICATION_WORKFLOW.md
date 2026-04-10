# Pest Detection Verification Workflow Implementation

## Overview

A comprehensive pest detection verification system has been implemented that allows agronomists to review, approve, or reject pest detection reports submitted by farmers. The system includes automatic notifications, status tracking, and professional assessment capabilities.

## Features Implemented

### 1. **Automatic Agronomist Notification**
- When a farmer submits a pest detection report, all assigned agronomists for that farm receive an immediate notification
- Notification includes:
  - Pest/disease name detected
  - Severity level
  - AI confidence percentage
  - Link to the verification dashboard

### 2. **Agronomist Verification Dashboard**
- **Location:** `/pest-verification/dashboard/`
- **Access:** Only for users with `user_type='agronomist'`
- **Features:**
  - View all pending pest reports from assigned farms
  - Filter by:
    - Status (Pending, Approved, Rejected, Needs Revision)
    - Severity level
    - Date range
    - Specific farm
    - Search by pest name or location
  - Display statistics:
    - Pending reviews
    - Approved reports
    - Rejected reports
    - Requests for revision
    - Severe cases count
  - Clickable rows to review individual reports

### 3. **Detailed Verification View**
- **Location:** `/pest-verification/<report_id>/`
- **Access:** Only assigned agronomist can view
- **Components:**
  - Farmer information (name, contact, location)
  - Farm and field details
  - Crop information
  - AI diagnosis details (confidence, severity, affected area)
  - Uploaded pest image
  - AI's treatment recommendations
  - Three approval action forms:

#### A. **Approve Form**
- Select to approve the diagnosis
- Add professional assessment notes
- Option to adjust severity level if needed
- Add additional treatment recommendations
- Farmer receives success notification with notes

#### B. **Reject Form**
- Explain rejection reason (image quality, unclear symptoms, etc.)
- Suggest what farmer should do
- Option to request resubmission
- Farmer receives warning notification with guidance

#### C. **Request Revision Form**
- Specify exactly what information is needed
- Provide reference links to helpful resources
- Farmer receives info notification with revision requirements

### 4. **Status Tracking System**

The `PestReport` model now tracks the following statuses:

| Status | Meaning | Next Step |
|--------|---------|-----------|
| `pending` | Awaiting agronomist review | Agronomist reviews in dashboard |
| `approved` | Diagnosis verified as correct | Farmer receives approval notification |
| `rejected` | Cannot be verified | Farmer resubmits or seeks other help |
| `needs_revision` | Additional info needed | Farmer resubmits with improvements |
| `healthy` | No pest detected | No further action needed |

### 5. **Notification System**

#### Farmer Notifications:
1. **On Submission:**
   - "Your pest report has been submitted for review"
   
2. **On Approval:**
   - Title: "✓ Pest Report Approved - [pest name]"
   - Includes: Agronomist name, severity, AI confidence, professional assessment
   
3. **On Rejection:**
   - Title: "⚠ Pest Report Needs Resubmission"
   - Includes: Reason, suggested next steps
   
4. **On Revision Request:**
   - Title: "⟳ Pest Report - Revision Needed"
   - Includes: Required information, helpful resources

#### Agronomist Notifications:
- Receive alert when farmer submits pest report to their assigned farm
- Can dismiss/mark read after reviewing

### 6. **Data Models**

The existing `PestReport` model fields used:
```python
class PestReport(models.Model):
    # Existing fields:
    farmer = ForeignKey(User)                    # Who submitted
    farm = ForeignKey(Farm)                      # Which farm
    field = ForeignKey(Field)                    # Which field (optional)
    image = ImageField                           # Uploaded pest image
    ai_diagnosis = CharField                     # Detected pest name
    confidence = DecimalField                    # AI confidence %
    severity = CharField                         # low/medium/high/severe
    treatment_recommended = TextField            # AI treatment suggestions
    prevention_tips = TextField                  # AI prevention tips
    organic_options = TextField                  # Organic treatment options
    
    # Verification fields:
    status = CharField                           # pending/approved/rejected/needs_revision/healthy
    agronomist_verified = BooleanField          # Is it verified?
    verified_by = ForeignKey(User, null=True)   # Which agronomist verified?
    agronomist_notes = TextField                 # Assessment/comments from agronomist
    
    # Timestamps:
    created_at = DateTimeField                  # When submitted
    updated_at = DateTimeField                  # When last updated
```

## File Structure

### New Files Created:

1. **`core/forms_pest_verification.py`** (NEW)
   - `PestReportApprovalForm` - Approve with notes and severity adjustment
   - `PestReportRejectionForm` - Reject with reason and suggested action
   - `PestReportRevisionRequestForm` - Request specific revisions
   - `AgronomistDashboardFilterForm` - Filter reports by status, severity, date, farm

2. **`core/views_pest_verification.py`** (NEW)
   - `agronomist_pest_dashboard()` - Dashboard view for listing reports
   - `pest_verification_detail()` - Detail view for individual report review
   - `approve_pest_report()` - Process approval action
   - `reject_pest_report()` - Process rejection action
   - `request_pest_report_revision()` - Process revision request
   - `api_approve_pest_report()` - AJAX endpoint for approval
   - `api_reject_pest_report()` - AJAX endpoint for rejection
   - `agronomist_statistics()` - API endpoint for dashboard stats

3. **`templates/pest/agronomist_dashboard.html`** (NEW)
   - Responsive dashboard with statistics cards
   - Advanced filtering interface
   - Paginated table of pest reports
   - Status badges and priority indicators

4. **`templates/pest/verification_detail.html`** (NEW)
   - Side-by-side layout: farmer info + report details on left, verification forms on right
   - Image preview of pest
   - AI diagnosis summary with confidence/severity/affected area
   - Three forms for: approve, reject, request revision
   - Current status display

### Modified Files:

1. **`core/views.py`**
   - Updated `pest_upload()` function to:
     - Send notification to farmer on submission
     - Send notification to ALL assigned agronomists for that farm
     - Include notification link to verification page

2. **`core/urls.py`**
   - Added import: `from . import views_pest_verification`
   - Added URL routes:
     ```python
     path('pest-verification/dashboard/', ...)
     path('pest-verification/<int:pk>/', ...)
     path('api/pest-reports/<int:pk>/approve/', ...)
     path('api/pest-reports/<int:pk>/reject/', ...)
     path('api/pest-reports/statistics/', ...)
     ```

3. **`templates/pest/detail.html`**
   - Enhanced verification status section showing:
     - Approved/Rejected/Needs Revision status with colored badges
     - Agronomist name and assessment notes
     - Resubmit button for rejected/revision reports
     - Pending status with "awaiting review" message

## How to Use

### For Farmers:

1. **Submit Pest Report:**
   - Go to `/pest-detection/`
   - Upload image
   - AI analyzes and creates report with status "pending"
   - Farmer receives notification: "Report submitted for review"

2. **Wait for Approval:**
   - Agronomist reviews the report
   - Farmer receives notification when decision is made

3. **Check Results:**
   - Go to `/pest-detection/history/`
   - View report details including:
     - Approval status
     - Agronomist's professional assessment
     - Any additional treatment recommendations or revision requests

4. **If Rejected or Revision Needed:**
   - Farmer can resubmit from the detail view
   - New submission also goes to agronomists for review

### For Agronomists:

1. **View Dashboard:**
   - Go to `/pest-verification/dashboard/`
   - See pending reports requiring review

2. **Filter Reports:**
   - Use filter form to prioritize by:
     - Severity (focus on severe cases first)
     - Date (recent first)
     - Status (pending vs already reviewed)
     - Specific farms

3. **Review Individual Report:**
   - Click "Review" button
   - View farmer info, farm location, AI diagnosis, and image

4. **Make Decision:**
   - **Approve:** Verify diagnosis is correct, add professional notes, adjust severity if needed
   - **Reject:** Explain why (unclear image, symptoms not visible, etc.), suggest action
   - **Request Revision:** Ask for specific info (better angle, describe symptoms, etc.), provide resources

5. **Check Statistics:**
   - Dashboard shows counts of:
     - Total reports reviewed
     - Approved vs rejected
     - Revision requests
     - Severe cases requiring urgent attention

## API Endpoints

### For AJAX/JavaScript Integration:

1. **Approve Report (POST)**
   ```
   /api/pest-reports/<report_id>/approve/
   
   Body: {
     "notes": "Professional assessment here",
     "severity": "high"  // optional, defaults to original
   }
   ```

2. **Reject Report (POST)**
   ```
   /api/pest-reports/<report_id>/reject/
   
   Body: {
     "reason": "Why cannot verify",
     "action": "What farmer should do"
   }
   ```

3. **Get Statistics (GET)**
   ```
   /api/pest-reports/statistics/
   
   Returns: {
     "total_reviewed": 45,
     "pending": 3,
     "approved": 35,
     "rejected": 7,
     "needs_revision": 4,
     "farms_assigned": 8,
     "recent_activity": 12
   }
   ```

## Workflow Diagram

```
Farmer Submits Image
        ↓
  AI Analyzes Pest
        ↓
Create PestReport (status='pending')
        ↓
Send Notifications:
  - Farmer: "Report submitted"
  - All Assigned Agronomists: "Review needed"
        ↓
Agronomist Reviews in Dashboard
        ↓
    Agronomist Decision:
   ↙        ↓        ↘
Approve   Reject   Request Revision
   ↓         ↓          ↓
Update   Update      Update
Status   Status    Status
   ↓         ↓          ↓
Send     Send       Send
Approval Rejection  Revision
Notif.   Notif.     Notif.
   ↓         ↓          ↓
Farmer Receives Decision + Comments
   ↓         ↓          ↓
Act on   Resubmit   Improve &
Advice   Different  Resubmit
         Farm
```

## Security & Permissions

- Only agronomists (user_type='agronomist') can access `/pest-verification/`
- Agronomists can only review reports from farms assigned to them
- Farmers can only see their own reports
- All actions logged with timestamps and actor information

## Future Enhancements

1. **Email & SMS Notifications** - Allow farmers/agronomists to receive notifications via email/SMS
2. **Batch Processing** - Allow agronomists to approve multiple reports at once
3. **Analytics Dashboard** - Show trends:
   - Most common pests detected
   - Approval/rejection rates
   - Response time metrics
   - Seasonal patterns
4. **Historical Trends** - Track pest patterns over time for predictive recommendations
5. **Integration with Insurance** - Auto-file insurance claims for approved severe cases
6. **Mobile App Push Notifications** - Real-time alerts on mobile devices
7. **Multilingual Support** - Translate reports and comments to farmer's preferred language
8. **Integration with Weather API** - Show weather conditions at time of pest detection

## Testing

### Manual Testing Checklist:

- [ ] Create test agronomist account with assigned farm
- [ ] Create farmer account with farm
- [ ] Login as farmer, upload pest image
- [ ] Verify notification sent to agronomist
- [ ] Login as agronomist, view dashboard
- [ ] Verify pending report shows in dashboard
- [ ] Test all filters on dashboard
- [ ] Click review on a report
- [ ] Approve report and verify farmer notification
- [ ] Reject another report and verify farmer notification
- [ ] Request revision on another report
- [ ] Logout and login as farmer
- [ ] View pest detail and verify status shows approval/rejection
- [ ] Verify agronomist notes are displayed
- [ ] Test API endpoints with curl/Postman

## Database Queries

### Get all pending reports for an agronomist:
```python
from core.models import PestReport, User

agronomist = User.objects.get(username='agronomist_name')
pending_reports = PestReport.objects.filter(
    farm__in=agronomist.assigned_farms.all(),
    status='pending'
).order_by('-created_at')
```

### Get statistics for agronomist dashboard:
```python
reports = PestReport.objects.filter(
    farm__in=agronomist.assigned_farms.all()
)

stats = {
    'total': reports.count(),
    'pending': reports.filter(status='pending').count(),
    'approved': reports.filter(status='approved').count(),
    'rejected': reports.filter(status='rejected').count(),
    'needs_revision': reports.filter(status='needs_revision').count(),
    'severe': reports.filter(severity='severe').count(),
}
```

### Get farmer's notification status:
```python
farmer_notifications = Notification.objects.filter(
    user=farmer,
    is_read=False
).order_by('-created_at')
```

## Configuration

No additional configuration needed! The system uses existing Django infrastructure:
- Notification system already implemented
- User roles/types already configured
- Farm assignments already available via RBAC system

## Troubleshooting

### Issue: Agronomist doesn't see any reports
**Solution:** Verify that:
1. Agronomist user_type is set to 'agronomist'
2. Agronomist is assigned to the farm where reports are being submitted
3. Pest reports have status='pending' (check database directly)

### Issue: Notifications not appearing
**Solution:**
1. Check that farmer/agronomist accounts have accepts_email and accepts_sms enabled
2. Verify Notification objects are created in database
3. Check Django admin notifications for the user

### Issue: Farmer cannot see agronomist's comments
**Solution:**
1. Verify report.agronomist_notes is populated in database
2. Check that report.status is not 'pending'
3. Check templates are rendering the notes correctly

## Support

For issues or questions:
1. Check the implementation files in `/core/views_pest_verification.py`
2. Review the forms in `/core/forms_pest_verification.py`
3. Check the templates in `/templates/pest/`
