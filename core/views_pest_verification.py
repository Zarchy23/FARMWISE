# core/views_pest_verification.py
# Views for pest detection verification workflow

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta

from .models import PestReport, Notification, User, Farm, Field
from .forms_pest_verification import (
    PestReportApprovalForm,
    PestReportRejectionForm,
    PestReportRevisionRequestForm,
    AgronomistDashboardFilterForm
)


def is_agronomist(user):
    """Check if user is an agronomist"""
    return user.user_type == 'agronomist'


def send_notification(user, title, message, notification_type='info', link=''):
    """Helper function to send notifications"""
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        link=link
    )
    return notification


@login_required
def agronomist_pest_dashboard(request):
    """Agronomist dashboard for reviewing pest detection reports - ALL agronomists see all reports"""
    
    # Check if user is agronomist
    if not is_agronomist(request.user):
        messages.error(request, 'Only agronomists can access this dashboard.')
        return redirect('core:dashboard')
    
    # Get ALL pest reports from ALL farms (no farm assignment restriction)
    # This allows any agronomist to see all pest detections and decisions made by others
    reports_query = PestReport.objects.all().select_related(
        'farmer', 'farm', 'field', 'crop', 'verified_by'
    )
    
    # Apply filters
    filter_form = AgronomistDashboardFilterForm(request.GET, agronomist_user=request.user)
    
    # Status filter
    status_filter = request.GET.get('status_filter', '')
    if status_filter:
        reports_query = reports_query.filter(status=status_filter)
    
    # Severity filter
    severity_filter = request.GET.get('severity_filter', '')
    if severity_filter:
        reports_query = reports_query.filter(severity=severity_filter)
    
    # Search query
    search_query = request.GET.get('search_query', '')
    if search_query:
        reports_query = reports_query.filter(
            Q(ai_diagnosis__icontains=search_query) |
            Q(farm__name__icontains=search_query) |
            Q(field__name__icontains=search_query) |
            Q(farmer__first_name__icontains=search_query) |
            Q(farmer__last_name__icontains=search_query)
        )
    
    # Date range filter
    date_from = request.GET.get('date_from')
    if date_from:
        reports_query = reports_query.filter(created_at__date__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        reports_query = reports_query.filter(created_at__date__lte=date_to)
    
    # Farm filter
    farm_filter = request.GET.get('farm_filter')
    if farm_filter:
        reports_query = reports_query.filter(farm_id=farm_filter)
    
    # Order by priority: pending first, then by severity and date
    reports_query = reports_query.order_by('-agronomist_verified', '-created_at')
    
    # Count statistics
    stats = {
        'pending': reports_query.filter(status='pending').count(),
        'approved': reports_query.filter(status='approved').count(),
        'rejected': reports_query.filter(status='rejected').count(),
        'needs_revision': reports_query.filter(status='needs_revision').count(),
        'total': reports_query.count(),
        'severe': reports_query.filter(severity='severe').count(),
    }
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(reports_query, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reports': page_obj.object_list,
        'filter_form': filter_form,
        'stats': stats,
    }
    
    return render(request, 'pest/agronomist_dashboard.html', context)


@login_required
def pest_verification_detail(request, pk):
    """Detailed view of a pest report for verification - any agronomist can view and review"""
    
    report = get_object_or_404(PestReport, pk=pk)
    
    # Check permissions - only agronomists can view and make decisions
    if not is_agronomist(request.user):
        messages.error(request, 'Only agronomists can access this.')
        return redirect('core:dashboard')
    
    # Any agronomist can view any report - no farm assignment restriction
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            form = PestReportApprovalForm(request.POST)
            if form.is_valid():
                return approve_pest_report(request, report, form)
        
        elif action == 'reject':
            form = PestReportRejectionForm(request.POST)
            if form.is_valid():
                return reject_pest_report(request, report, form)
        
        elif action == 'request_revision':
            form = PestReportRevisionRequestForm(request.POST)
            if form.is_valid():
                return request_pest_report_revision(request, report, form)
    
    approval_form = PestReportApprovalForm()
    rejection_form = PestReportRejectionForm()
    revision_form = PestReportRevisionRequestForm()
    
    context = {
        'report': report,
        'approval_form': approval_form,
        'rejection_form': rejection_form,
        'revision_form': revision_form,
        'can_edit': report.status == 'pending',
    }
    
    return render(request, 'pest/verification_detail.html', context)


def approve_pest_report(request, report, form):
    """Approve a pest report"""
    
    agronomist_notes = form.cleaned_data.get('agronomist_notes', '')
    severity_adjustment = form.cleaned_data.get('severity_adjustment', '')
    additional_treatment = form.cleaned_data.get('additional_treatment', '')
    
    # Update report
    report.agronomist_verified = True
    report.verified_by = request.user
    report.status = 'approved'
    report.agronomist_notes = agronomist_notes
    
    # Adjust severity if requested
    if severity_adjustment:
        report.severity = severity_adjustment
    
    # Add to treatment recommendations
    if additional_treatment:
        report.treatment_recommended = (report.treatment_recommended or '') + f"\n\n[Agronomist Addition]: {additional_treatment}"
    
    report.updated_at = timezone.now()
    report.save()
    
    # Send notification to farmer
    notification_message = f"""
Your pest detection report for {report.farm.name} has been APPROVED by agronomist {request.user.get_full_name()}.

Diagnosis: {report.ai_diagnosis}
Severity: {report.get_severity_display()}
Confidence: {report.confidence}%

Professional Assessment: {agronomist_notes or 'No additional notes'}

Recommended Treatment: {report.treatment_recommended}
"""
    
    send_notification(
        user=report.farmer,
        title=f'✓ Pest Report Approved - {report.ai_diagnosis}',
        message=notification_message.strip(),
        notification_type='success',
        link=f'/pest-detection/{report.id}/'
    )
    
    messages.success(request, f'Pest report {report.id} approved successfully!')
    
    return redirect('core:agronomist_pest_dashboard')


def reject_pest_report(request, report, form):
    """Reject a pest report"""
    
    rejection_reason = form.cleaned_data.get('rejection_reason', '')
    suggested_action = form.cleaned_data.get('suggested_action', '')
    send_for_revision = form.cleaned_data.get('send_for_revision', False)
    
    # Update report
    report.status = 'rejected'
    report.agronomist_notes = f"REJECTION: {rejection_reason}\n\nSuggested Action: {suggested_action}"
    report.verified_by = request.user
    report.updated_at = timezone.now()
    report.save()
    
    # Send notification to farmer
    notification_message = f"""
Your pest detection report for {report.farm.name} could not be verified.

Original AI Diagnosis: {report.ai_diagnosis}

Reason: {rejection_reason}

Next Steps: {suggested_action or 'Please resubmit with clearer information'}
"""
    
    send_notification(
        user=report.farmer,
        title=f'⚠ Pest Report Needs Resubmission - {report.ai_diagnosis}',
        message=notification_message.strip(),
        notification_type='warning',
        link=f'/pest-detection/{report.id}/'
    )
    
    messages.success(request, f'Pest report {report.id} rejected. Farmer has been notified.')
    
    return redirect('core:agronomist_pest_dashboard')


def request_pest_report_revision(request, report, form):
    """Request revision of a pest report"""
    
    revision_notes = form.cleaned_data.get('revision_notes', '')
    reference_links = form.cleaned_data.get('reference_links', '')
    
    # Update report
    report.status = 'needs_revision'
    report.agronomist_notes = f"REVISION NEEDED:\n{revision_notes}\n\nResources: {reference_links}"
    report.verified_by = request.user
    report.updated_at = timezone.now()
    report.save()
    
    # Send notification to farmer
    notification_message = f"""
Your pest detection report for {report.farm.name} needs revision.

Current AI Diagnosis: {report.ai_diagnosis}

Required Information:
{revision_notes}

Helpful Resources:
{reference_links or 'Check your email for additional resources'}

Please resubmit with the requested information.
"""
    
    send_notification(
        user=report.farmer,
        title=f'⟳ Pest Report - Revision Needed',
        message=notification_message.strip(),
        notification_type='info',
        link=f'/pest-detection/{report.id}/'
    )
    
    messages.success(request, f'Revision request sent to farmer for report {report.id}.')
    
    return redirect('core:agronomist_pest_dashboard')


@login_required
@require_http_methods(["POST"])
def api_approve_pest_report(request, pk):
    """API endpoint for approving pest report (AJAX)"""
    
    if not is_agronomist(request.user):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    report = get_object_or_404(PestReport, pk=pk)
    
    # Any agronomist can approve any report (collaborative model)
    
    # Get form data
    import json
    data = json.loads(request.body)
    
    notes = data.get('notes', '')
    severity = data.get('severity', report.severity)
    
    report.agronomist_verified = True
    report.verified_by = request.user
    report.status = 'approved'
    report.agronomist_notes = notes
    report.severity = severity
    report.updated_at = timezone.now()
    report.save()
    
    # Send notification
    send_notification(
        user=report.farmer,
        title=f'✓ Pest Report Approved - {report.ai_diagnosis}',
        message=f'Your pest report has been verified and approved by agronomist {request.user.get_full_name()}.\n\n{notes}',
        notification_type='success'
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Report {report.id} approved',
        'report_id': report.id
    })


@login_required
@require_http_methods(["POST"])
def api_reject_pest_report(request, pk):
    """API endpoint for rejecting pest report (AJAX)"""
    
    if not is_agronomist(request.user):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    report = get_object_or_404(PestReport, pk=pk)
    
    # Any agronomist can reject any report (collaborative model)
    
    import json
    data = json.loads(request.body)
    
    reason = data.get('reason', '')
    action = data.get('action', '')
    
    report.status = 'rejected'
    report.agronomist_notes = f"REJECTION: {reason}\n\nAction: {action}"
    report.verified_by = request.user
    report.updated_at = timezone.now()
    report.save()
    
    # Send notification
    send_notification(
        user=report.farmer,
        title=f'⚠ Pest Report Needs Resubmission',
        message=f'Your pest report could not be verified.\n\nReason: {reason}\n\nPlease {action}',
        notification_type='warning'
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Report {report.id} rejected',
        'report_id': report.id
    })


@login_required
def agronomist_statistics(request):
    """API endpoint for agronomist statistics"""
    
    if not is_agronomist(request.user):
        return JsonResponse({'error': 'Not authorized'}, status=403)
    
    # Show statistics for all reports (collaborative model)
    reports = PestReport.objects.all()
    
    stats = {
        'total_reviewed': reports.exclude(status='pending').count(),
        'pending': reports.filter(status='pending').count(),
        'approved': reports.filter(status='approved').count(),
        'rejected': reports.filter(status='rejected').count(),
        'needs_revision': reports.filter(status='needs_revision').count(),
        'average_severity': 'medium',  # Could calculate this
        'recent_activity': reports.filter(
            updated_at__gte=timezone.now() - timedelta(days=7)
        ).count(),
    }
    
    return JsonResponse(stats)
