# Project Views - Implementation Examples

## Complete Views Implementation

```python
# core/projects/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db.models import Q
from core.models import Project, Farm
from core.forms import ProjectForm


# ============================================================
# LIST VIEW
# ============================================================

class ProjectListView(LoginRequiredMixin, ListView):
    """Display list of projects with filtering and pagination"""
    model = Project
    template_name = 'projects/list.html'
    context_object_name = 'projects'
    paginate_by = 10
    login_url = 'account_login'
    
    def get_queryset(self):
        """Get projects based on user role with filtering"""
        user = self.request.user
        
        # Start with user's own projects
        if hasattr(user, 'user_type') and user.user_type in ['agronomist', 'veterinarian']:
            # Agronomists see farms they're assigned to
            farms = Farm.objects.filter(assigned_to=user)
            queryset = Project.objects.filter(farm__in=farms)
        elif hasattr(user, 'user_type') and user.user_type == 'cooperative_admin':
            # Cooperative admins see their cooperative's farms
            queryset = Project.objects.filter(farm__cooperative=user)
        else:
            # Farmers see their own farms
            queryset = Project.objects.filter(farm__owner=user)
        
        # Apply filters
        farm_id = self.request.GET.get('farm')
        if farm_id:
            queryset = queryset.filter(farm_id=farm_id)
        
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.select_related('farm', 'created_by').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add filter options to context"""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's farms for filter dropdown
        if user.is_staff:
            context['farms'] = Farm.objects.all()
        else:
            context['farms'] = Farm.objects.filter(owner=user)
        
        context['categories'] = Project.CATEGORY_CHOICES
        context['statuses'] = Project.STATUS_CHOICES
        
        return context


# ============================================================
# DETAIL VIEW
# ============================================================

class ProjectDetailView(LoginRequiredMixin, DetailView):
    """Display detailed project information"""
    model = Project
    template_name = 'projects/detail.html'
    context_object_name = 'project'
    login_url = 'account_login'
    
    def get_queryset(self):
        """Only show projects user has access to"""
        user = self.request.user
        
        if user.is_staff:
            return Project.objects.all()
        
        if hasattr(user, 'user_type') and user.user_type in ['agronomist', 'veterinarian']:
            farms = Farm.objects.filter(assigned_to=user)
            return Project.objects.filter(farm__in=farms)
        
        if hasattr(user, 'user_type') and user.user_type == 'cooperative_admin':
            return Project.objects.filter(farm__cooperative=user)
        
        return Project.objects.filter(farm__owner=user)
    
    def get_context_data(self, **kwargs):
        """Add project-related data"""
        context = super().get_context_data(**kwargs)
        project = self.get_object()
        
        # Calculate statistics
        context['task_stats'] = {
            'total': project.task_set.count(),
            'completed': project.task_set.filter(is_completed=True).count(),
        }
        
        return context


# ============================================================
# CREATE VIEW
# ============================================================

class ProjectCreateView(LoginRequiredMixin, CreateView):
    """Create a new project"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'
    login_url = 'account_login'
    success_url = reverse_lazy('core:project_list')
    
    def get_form_kwargs(self):
        """Limit farms to user's farms"""
        kwargs = super().get_form_kwargs()
        user = self.request.user
        
        # Filter form's farm queryset
        kwargs['farms'] = Farm.objects.filter(owner=user)
        
        return kwargs
    
    def form_valid(self, form):
        """Set created_by and save"""
        form.instance.created_by = self.request.user
        
        # Validate project farm belongs to user
        if form.instance.farm.owner != self.request.user and not self.request.user.is_staff:
            form.add_error('farm', 'You can only create projects on your own farms.')
            return self.form_invalid(form)
        
        response = super().form_valid(form)
        return response
    
    def get_context_data(self, **kwargs):
        """Add context for template"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Create New Project'
        return context


# ============================================================
# UPDATE VIEW
# ============================================================

class ProjectEditView(LoginRequiredMixin, UpdateView):
    """Edit an existing project"""
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'
    login_url = 'account_login'
    success_url = reverse_lazy('core:project_list')
    
    def get_queryset(self):
        """Only allow editing own projects (or staff)"""
        user = self.request.user
        
        if user.is_staff:
            return Project.objects.all()
        
        return Project.objects.filter(created_by=user)
    
    def get_form_kwargs(self):
        """Limit farms to user's farms"""
        kwargs = super().get_form_kwargs()
        user = self.request.user
        
        kwargs['farms'] = Farm.objects.filter(owner=user)
        
        return kwargs
    
    def form_valid(self, form):
        """Validate farm ownership"""
        if form.instance.farm.owner != self.request.user and not self.request.user.is_staff:
            form.add_error('farm', 'You can only edit projects on your own farms.')
            return self.form_invalid(form)
        
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        """Add context for template"""
        context = super().get_context_data(**kwargs)
        context['title'] = f"Edit Project: {self.object.name}"
        return context


# ============================================================
# DELETE VIEW
# ============================================================

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a project"""
    model = Project
    template_name = 'projects/delete_confirm.html'
    success_url = reverse_lazy('core:project_list')
    login_url = 'account_login'
    
    def get_queryset(self):
        """Only allow deleting own projects (or staff)"""
        user = self.request.user
        
        if user.is_staff:
            return Project.objects.all()
        
        return Project.objects.filter(created_by=user)
    
    def delete(self, request, *args, **kwargs):
        """Log deletion and redirect"""
        project = self.get_object()
        
        # Log the deletion (optional)
        # logger.info(f"Project '{project.name}' deleted by {request.user}")
        
        return super().delete(request, *args, **kwargs)


# ============================================================
# FUNCTION-BASED VIEW ALTERNATIVES
# ============================================================

@login_required
def project_list(request):
    """Function-based project list view"""
    user = request.user
    
    # Get user's projects
    if user.is_staff:
        projects = Project.objects.all()
    else:
        projects = Project.objects.filter(farm__owner=user)
    
    # Apply filters
    if request.GET.get('farm'):
        projects = projects.filter(farm_id=request.GET.get('farm'))
    
    if request.GET.get('category'):
        projects = projects.filter(category=request.GET.get('category'))
    
    if request.GET.get('status'):
        projects = projects.filter(status=request.GET.get('status'))
    
    # Pagination
    paginator = Paginator(projects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    farms = Farm.objects.filter(owner=user)
    
    context = {
        'page_obj': page_obj,
        'projects': page_obj.object_list,
        'farms': farms,
        'categories': Project.CATEGORY_CHOICES,
        'statuses': Project.STATUS_CHOICES,
    }
    
    return render(request, 'projects/list.html', context)


@login_required
def project_detail(request, pk):
    """Function-based project detail view"""
    user = request.user
    
    # Get project with permission check
    if user.is_staff:
        project = get_object_or_404(Project, pk=pk)
    else:
        project = get_object_or_404(Project, pk=pk, farm__owner=user)
    
    context = {
        'project': project,
    }
    
    return render(request, 'projects/detail.html', context)


@login_required
def project_create(request):
    """Function-based project create view"""
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            
            # Validate farm ownership
            if project.farm.owner != request.user and not request.user.is_staff:
                form.add_error('farm', 'Invalid farm selection')
                return render(request, 'projects/form.html', {'form': form})
            
            project.save()
            return redirect('core:project_detail', pk=project.pk)
    else:
        form = ProjectForm()
        # Limit to user's farms
        form.fields['farm'].queryset = Farm.objects.filter(owner=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Project',
    }
    
    return render(request, 'projects/form.html', context)


@login_required
def project_edit(request, pk):
    """Function-based project edit view"""
    if request.user.is_staff:
        project = get_object_or_404(Project, pk=pk)
    else:
        project = get_object_or_404(Project, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            # Validate farm ownership
            if form.instance.farm.owner != request.user and not request.user.is_staff:
                form.add_error('farm', 'Invalid farm selection')
                return render(request, 'projects/form.html', {
                    'form': form,
                    'title': f'Edit Project: {project.name}',
                })
            
            form.save()
            return redirect('core:project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
        # Limit to user's farms
        form.fields['farm'].queryset = Farm.objects.filter(owner=request.user)
    
    context = {
        'form': form,
        'title': f'Edit Project: {project.name}',
    }
    
    return render(request, 'projects/form.html', context)


@login_required
def project_delete(request, pk):
    """Function-based project delete view"""
    if request.user.is_staff:
        project = get_object_or_404(Project, pk=pk)
    else:
        project = get_object_or_404(Project, pk=pk, created_by=request.user)
    
    if request.method == 'POST':
        project.delete()
        return redirect('core:project_list')
    
    context = {
        'project': project,
    }
    
    return render(request, 'projects/delete_confirm.html', context)
```

## URL Configuration

```python
# core/urls.py
from django.urls import path
from core.projects import views

app_name = 'core'

urlpatterns = [
    # Projects
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/edit/', views.ProjectEditView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
]
```

## Form Configuration

```python
# core/projects/forms.py
from django import forms
from core.models import Project


class ProjectForm(forms.ModelForm):
    """Form for creating and editing projects"""
    
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'farm',
            'category', 'priority', 'status', 'progress',
            'start_date', 'target_completion_date',
            'budget', 'actual_cost',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
                'placeholder': 'Enter project name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
                'rows': 4,
                'placeholder': 'Describe your project goals and scope',
            }),
            'farm': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
            }),
            'category': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
            }),
            'status': forms.Select(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
            }),
            'progress': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
                'type': 'range',
                'min': '0',
                'max': '100',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
                'type': 'date',
            }),
            'target_completion_date': forms.DateInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
                'type': 'date',
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'placeholder': 'Enter amount in KES',
            }),
            'actual_cost': forms.NumberInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500',
                'step': '0.01',
                'placeholder': 'Enter amount in KES',
            }),
        }
    
    def __init__(self, *args, farms=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limit farms to user's farms if provided
        if farms:
            self.fields['farm'].queryset = farms
    
    def clean(self):
        """Validate form data"""
        cleaned_data = super().clean()
        
        start_date = cleaned_data.get('start_date')
        target_date = cleaned_data.get('target_completion_date')
        
        # Validate dates
        if start_date and target_date:
            if target_date <= start_date:
                self.add_error('target_completion_date',
                    'Target completion date must be after start date.')
        
        # Validate budget
        budget = cleaned_data.get('budget')
        actual_cost = cleaned_data.get('actual_cost')
        
        if actual_cost and budget:
            if actual_cost > budget:
                self.add_error('actual_cost',
                    'Actual cost cannot exceed budget.')
        
        return cleaned_data
```

## Delete Confirmation Template

```django
{# templates/projects/delete_confirm.html #}
{% extends 'base.html' %}
{% load static %}

{% block title %}Delete Project - FarmWise{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-6 max-w-2xl">
    <div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-red-500">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">Delete Project</h1>
        <p class="text-gray-600 mb-6">This action cannot be undone.</p>
        
        <div class="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p class="text-red-800 font-semibold">Are you sure you want to delete this project?</p>
            <p class="text-red-700 text-sm mt-2">{{ project.name }}</p>
            <p class="text-red-600 text-xs mt-1">{{ project.farm.name }}</p>
        </div>
        
        <div class="flex gap-4">
            <form method="post" class="flex-1">
                {% csrf_token %}
                <button type="submit" class="w-full bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-semibold transition">
                    <i class="ri-delete-bin-line"></i> Delete Project
                </button>
            </form>
            <a href="{% url 'core:project_detail' project.id %}" class="flex-1 bg-gray-500 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold text-center transition">
                <i class="ri-close-line"></i> Cancel
            </a>
        </div>
    </div>
</div>
{% endblock %}
```

