# Project Templates - Quick Reference Guide

## Quick Start

### 1. List All Projects
**Template:** `templates/projects/list.html`
**URL Name:** `core:project_list`
**View:**
```python
from django.shortcuts import render
from core.models import Project

def project_list(request):
    projects = Project.objects.filter(farm__owner=request.user)
    context = {
        'projects': projects,
        'farms': Farm.objects.filter(owner=request.user),
        'categories': Project.CATEGORY_CHOICES,
        'statuses': Project.STATUS_CHOICES,
    }
    return render(request, 'projects/list.html', context)
```

### 2. Create/Edit Project
**Template:** `templates/projects/form.html`
**URL Names:** 
- Create: `core:project_create`
- Edit: `core:project_edit`

**View:**
```python
from django.views.generic import CreateView, UpdateView
from core.models import Project
from core.forms import ProjectForm

class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

class ProjectEditView(UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/form.html'
    
    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)
```

### 3. View Project Details
**Template:** `templates/projects/detail.html`
**URL Name:** `core:project_detail`
**View:**
```python
from django.views.generic import DetailView
from core.models import Project

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'projects/detail.html'
    context_object_name = 'project'
```

### 4. Delete Project
**URL Name:** `core:project_delete`
**View:**
```python
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from core.models import Project

class ProjectDeleteView(DeleteView):
    model = Project
    success_url = reverse_lazy('core:project_list')
    
    def get_queryset(self):
        return Project.objects.filter(created_by=self.request.user)
```

---

## URL Configuration

```python
# core/urls.py
from django.urls import path
from core.projects import views

urlpatterns = [
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/<int:pk>/edit/', views.ProjectEditView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
]
```

---

## Permission System

### Check if User Can Edit
```django
{% if project.created_by == user or user.is_staff or user.is_superuser %}
    <!-- Show edit button -->
{% endif %}
```

### Check if User is Related to Project's Farm
```django
{% if project.farm.owner == user %}
    <!-- Show farm-specific actions -->
{% endif %}
```

### Check if User is Agronomist Assigned to Farm
```django
{% if user in project.farm.assigned_to.all %}
    <!-- Show agronomist actions -->
{% endif %}
```

---

## Model Fields Expected

```python
class Project(models.Model):
    # Basic Information
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    
    # Project Details
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    progress = models.IntegerField(default=0)  # 0-100%
    
    # Timeline
    start_date = models.DateField(blank=True, null=True)
    target_completion_date = models.DateField(blank=True, null=True)
    
    # Budget
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## Form Fields Rendered

```python
# ProjectForm should include:
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name', 'description', 'farm',
            'category', 'priority', 'status', 'progress',
            'start_date', 'target_completion_date',
            'budget', 'actual_cost',
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind classes to fields
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'w-full border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-green-500 focus:border-transparent transition'
            })
```

---

## Template Variables Reference

### List View Context
```python
{
    'projects': QuerySet,              # Filtered projects
    'farms': QuerySet,                 # User's farms
    'categories': list,                # Project categories
    'statuses': list,                  # Project statuses
    'page_obj': Page,                  # Pagination object
    'paginator': Paginator,            # Paginator object
}
```

### Detail View Context
```python
{
    'project': Project,                # Current project
    'user': User,                      # Current user
}
```

### Form View Context
```python
{
    'form': ProjectForm,               # Django form instance
    'title': str,                      # "Create Project" or "Edit Project"
}
```

---

## Common Issues & Solutions

### Issue: Permission Denied on Edit
**Solution:**
```python
def get_queryset(self):
    return Project.objects.filter(created_by=self.request.user)
```

### Issue: Form Not Validating
**Solution:** Check project model has all required fields. Ensure form's Meta.fields matches.

### Issue: Progress Bar Not Showing
**Solution:** Ensure progress field is integer 0-100. Check template for correct syntax:
```django
style="width: {{ project.progress|default:0 }}%"
```

### Issue: Budget Calculation Wrong
**Solution:** Use JavaScript fallback in template:
```javascript
const percentage = ({{ project.actual_cost }}/{{ project.budget }}) * 100;
```

---

## Deployment Checklist

- [ ] All URLs configured in `urls.py`
- [ ] All views created and tested
- [ ] Permission checks working correctly
- [ ] Static files collected (CSS/icons/fonts)
- [ ] Database migrations applied
- [ ] Templates tested on different screen sizes
- [ ] Form validation working
- [ ] Empty states displaying correctly
- [ ] Pagination working
- [ ] Admin panel access restricted to staff
- [ ] Error pages configured (404, 500)

---

## Testing Template Rendering

### Quick Test View (DEBUG only)
```python
# views.py
from django.shortcuts import render
from core.models import Project, Farm

def project_list_test(request):
    projects = Project.objects.all()[:5]
    farms = Farm.objects.all()[:5]
    return render(request, 'projects/list.html', {
        'projects': projects,
        'farms': farms,
        'categories': Project.CATEGORY_CHOICES,
        'statuses': Project.STATUS_CHOICES,
    })
```

### Test Form Rendering
```python
from core.forms import ProjectForm

form = ProjectForm()
# Check form renders without errors
print(form.as_p())
```

---

## CSS Classes Used

### Containers
- `.container mx-auto` - Max width container
- `.grid grid-cols-1 md:grid-cols-2` - Responsive grid

### Cards
- `.bg-white rounded-lg shadow-md p-6` - Card base
- `.border-l-4 border-green-500` - Left accent border
- `.bg-gradient-to-r from-green-600 to-green-700` - Gradient header

### Buttons
- `.bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg` - Primary
- `.bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg` - Secondary
- `.bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg` - Danger

### Badges
- `.px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800` - Status
- `.px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800` - Tag

### Progress
- `.bg-gray-200 rounded-full h-4` - Progress bar background
- `.bg-gradient-to-r from-green-500 to-green-600 h-4 rounded-full` - Progress fill

---

## Performance Optimization

### Database Queries
```python
# Use select_related for ForeignKey
projects = Project.objects.select_related('farm', 'created_by')

# Use prefetch_related for reverse ForeignKey
projects = Project.objects.prefetch_related('task_set')

# Limit results for list view
projects = Project.objects.all()[:10]
```

### Pagination
```python
from django.core.paginator import Paginator

def project_list(request):
    all_projects = Project.objects.all()
    paginator = Paginator(all_projects, 10)  # 10 per page
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'projects/list.html', {'page_obj': page_obj})
```

### Caching
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 5)  # 5 minutes
def project_list(request):
    ...
```

