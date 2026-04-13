# core/forms_projects.py
# Forms for Farm Projects feature

from django import forms
from .models import FarmProject, ProjectTask, ProjectResource, ProjectMilestone


class FarmProjectForm(forms.ModelForm):
    """Form for creating/editing farm projects"""
    
    class Meta:
        model = FarmProject
        fields = ['farm', 'name', 'category', 'description', 'start_date', 'target_end_date', 
                  'budget', 'priority', 'status', 'notes']
        widgets = {
            'farm': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'Project name'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Project description'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'type': 'date'
            }),
            'target_end_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'type': 'date'
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'step': '0.01',
                'placeholder': '0.00',
                'min': '0'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Additional notes'
            }),
        }
        labels = {
            'farm': 'Select Farm',
            'name': 'Project Name',
            'category': 'Project Category',
            'description': 'Project Description',
            'start_date': 'Start Date',
            'target_end_date': 'Target End Date',
            'budget': 'Budget ($)',
            'priority': 'Priority Level',
            'status': 'Status',
            'notes': 'Notes',
        }


class ProjectTaskForm(forms.ModelForm):
    """Form for adding tasks to projects"""
    
    class Meta:
        model = ProjectTask
        fields = ['name', 'description', 'assigned_to', 'due_date', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'Task name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'Task description'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'Add notes'
            }),
        }
        labels = {
            'name': 'Task Name',
            'description': 'Description',
            'assigned_to': 'Assign To',
            'due_date': 'Due Date',
            'notes': 'Notes',
        }


class ProjectResourceForm(forms.ModelForm):
    """Form for adding resources to projects"""
    
    class Meta:
        model = ProjectResource
        fields = ['resource_type', 'name', 'quantity', 'unit', 'cost', 'notes']
        widgets = {
            'resource_type': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent'
            }),
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'Resource name'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'step': '0.01',
                'min': '0'
            }),
            'unit': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'e.g., kg, liters, hours'
            }),
            'cost': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'Resource notes'
            }),
        }
        labels = {
            'resource_type': 'Resource Type',
            'name': 'Resource Name',
            'quantity': 'Quantity',
            'unit': 'Unit',
            'cost': 'Cost ($)',
            'notes': 'Notes',
        }


class ProjectMilestoneForm(forms.ModelForm):
    """Form for adding milestones to projects"""
    
    class Meta:
        model = ProjectMilestone
        fields = ['name', 'target_date', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'placeholder': 'Milestone name'
            }),
            'target_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'type': 'date'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'Milestone notes'
            }),
        }
        labels = {
            'name': 'Milestone Name',
            'target_date': 'Target Date',
            'notes': 'Notes',
        }
