# core/forms_pest_verification.py
# Forms for pest detection verification workflow

from django import forms
from .models import PestReport, Notification
from django.contrib.auth import get_user_model

User = get_user_model()


class PestReportApprovalForm(forms.Form):
    """Form for agronomist to approve pest reports"""
    
    DECISION_CHOICES = [
        ('approved', '✓ Approve - Diagnosis is correct'),
        ('needs_revision', '⟳ Request Revision - Needs more info'),
    ]
    
    decision = forms.ChoiceField(
        choices=DECISION_CHOICES,
        widget=forms.RadioSelect,
        label='Approval Decision',
        help_text='Approve the diagnosis or request revision'
    )
    
    agronomist_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Add your expert assessment, additional observations, or questions for the farmer'
        }),
        label='Professional Assessment',
        help_text='Share your expertise to help the farmer',
        required=False
    )
    
    severity_adjustment = forms.ChoiceField(
        choices=[
            ('', '-- Keep original severity --'),
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('severe', 'Severe'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control',
        }),
        label='Severity Adjustment (optional)',
        required=False
    )
    
    additional_treatment = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Any additional treatment recommendations'
        }),
        label='Additional Treatment Tips',
        required=False
    )


class PestReportRejectionForm(forms.Form):
    """Form for agronomist to reject pest reports"""
    
    rejection_reason = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Explain why this diagnosis cannot be verified (e.g., image quality, unclear symptoms)'
        }),
        label='Reason for Rejection',
        help_text='Provide clear feedback for the farmer to resubmit',
        required=True
    )
    
    suggested_action = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'What should the farmer do instead? (e.g., take clearer photo, wait for symptoms to show)'
        }),
        label='Suggested Action',
        help_text='Guide the farmer on next steps',
        required=False
    )
    
    send_for_revision = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='Request farmer to resubmit with improvements'
    )


class PestReportRevisionRequestForm(forms.Form):
    """Form for agronomist to request revision"""
    
    revision_notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'What information or action do you need from the farmer? (e.g., provide better photo angles, describe symptoms in detail)'
        }),
        label='Revision Requirements',
        help_text='Clear instructions for the farmer to improve the submission',
        required=True
    )
    
    reference_links = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Any external guide links or resources'
        }),
        label='Helpful Resources (optional)',
        required=False
    )


class AgronomistDashboardFilterForm(forms.Form):
    """Form for filtering pest reports on agronomist dashboard"""
    
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('needs_revision', 'Needs Revision'),
    ]
    
    SEVERITY_CHOICES = [
        ('', 'All Severity Levels'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('severe', 'Severe'),
    ]
    
    status_filter = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label='Status'
    )
    
    severity_filter = forms.ChoiceField(
        choices=SEVERITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label='Severity'
    )
    
    search_query = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by pest name, location, or AI diagnosis...'
        }),
        required=False,
        label='Search'
    )
    
    date_from = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=False,
        label='From Date'
    )
    
    date_to = forms.DateField(
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        }),
        required=False,
        label='To Date'
    )
    
    farm_filter = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False,
        label='Farm',
        empty_label='All Farms'
    )
    
    def __init__(self, data=None, files=None, agronomist_user=None, **kwargs):
        super().__init__(data=data, files=files, **kwargs)
        # Show ALL farms for any agronomist to review
        # (not just assigned farms - allows any agronomist to see all pest detections)
        from core.models import Farm
        self.fields['farm_filter'].queryset = Farm.objects.all()
