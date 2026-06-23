# Project Templates - Visual Reference & Component Library

## Component Patterns Used

### 1. Header Card Pattern
```django
<div class="bg-gradient-to-r from-[color]-600 to-[color]-700 px-6 py-4 text-white">
    <h3 class="text-lg font-bold flex items-center gap-2">
        <i class="ri-[icon]-line"></i> Section Title
    </h3>
</div>
```
**Colors:**
- Green: Primary actions (`from-green-600 to-green-700`)
- Blue: Information (`from-blue-600 to-blue-700`)
- Purple: Metadata (`from-purple-600 to-purple-700`)
- Indigo: Tasks (`from-indigo-600 to-indigo-700`)

---

### 2. Stat Card Pattern
```django
<div class="bg-[color]-50 rounded-lg p-4 border-l-4 border-[color]-500">
    <p class="text-gray-600 text-sm font-semibold">Label</p>
    <p class="text-2xl font-bold text-gray-800 mt-2">Value</p>
</div>
```
**Color Combinations:**
- Blue Stats: `bg-blue-50 border-blue-500`
- Orange Spending: `bg-orange-50 border-orange-500`
- Green Success: `bg-green-50 border-green-500`

---

### 3. Badge Pattern

**Status Badge:**
```django
<span class="px-3 py-1 rounded-full text-sm font-semibold
    {% if project.status == 'planning' %}bg-blue-100 text-blue-800
    {% elif project.status == 'active' %}bg-green-100 text-green-800
    {% elif project.status == 'paused' %}bg-yellow-100 text-yellow-800
    {% elif project.status == 'completed' %}bg-green-600 text-white
    {% endif %}">
    {{ project.get_status_display }}
</span>
```

**Priority Badge:**
```django
<span class="px-3 py-1 rounded-full text-sm font-semibold
    {% if project.priority == 'high' %}bg-red-100 text-red-800
    {% elif project.priority == 'medium' %}bg-orange-100 text-orange-800
    {% else %}bg-blue-100 text-blue-800
    {% endif %}">
    {{ project.get_priority_display }}
</span>
```

---

### 4. Progress Bar Pattern

**Standard Progress:**
```django
<div class="w-full bg-gray-200 rounded-full h-4">
    <div class="bg-gradient-to-r from-green-500 to-green-600 h-4 rounded-full transition-all" 
         style="width: {{ project.progress }}%"></div>
</div>
```

**Budget Utilization (Warning Colors):**
```django
<div class="w-full bg-gray-200 rounded-full h-3">
    <div class="bg-gradient-to-r from-orange-500 to-red-600 h-3 rounded-full transition-all"
         style="width: {{ usage_percent }}%"></div>
</div>
```

---

### 5. Button Patterns

**Primary Button:**
```django
<button class="bg-green-600 hover:bg-green-700 text-white px-6 py-2 rounded-lg font-semibold flex items-center gap-2 transition">
    <i class="ri-[icon]-line"></i> Label
</button>
```

**Secondary Button:**
```django
<button class="bg-gray-500 hover:bg-gray-600 text-white px-6 py-2 rounded-lg font-semibold transition">
    <i class="ri-[icon]-line"></i> Label
</button>
```

**Danger Button:**
```django
<button class="bg-red-600 hover:bg-red-700 text-white px-6 py-2 rounded-lg font-semibold transition">
    <i class="ri-delete-bin-line"></i> Delete
</button>
```

---

### 6. Form Field Pattern

**Input Field:**
```django
<div class="mb-6">
    <label for="{{ field.id_for_label }}" class="block text-sm font-semibold text-gray-700 mb-2">
        {{ field.label }} {% if field.field.required %}<span class="text-red-600">*</span>{% endif %}
    </label>
    {{ field }}
    {% if field.errors %}
        <p class="text-red-600 text-sm mt-2 flex items-start gap-1">
            <i class="ri-error-warning-line flex-shrink-0"></i>
            {{ field.errors.0 }}
        </p>
    {% else %}
        <p class="text-gray-600 text-sm mt-1">{{ help_text }}</p>
    {% endif %}
</div>
```

**CSS Classes:**
```css
input[type="text"],
input[type="date"],
input[type="number"],
textarea,
select {
    @apply w-full border border-gray-300 rounded-lg px-4 py-2 
           focus:ring-2 focus:ring-green-500 focus:border-transparent 
           transition;
}

textarea {
    @apply resize-vertical min-h-24;
}

input[type="range"] {
    @apply w-full cursor-pointer;
}
```

---

### 7. Grid Layouts

**Responsive 2-Column:**
```django
<div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    <div>Content</div>
    <div>Content</div>
</div>
```

**Responsive 3-Column:**
```django
<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    <div>Content</div>
    <div>Content</div>
    <div>Content</div>
</div>
```

**Main + Sidebar (3-column):**
```django
<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
    <div class="lg:col-span-2">Main content</div>
    <div class="lg:col-span-1">Sidebar</div>
</div>
```

---

### 8. Card Patterns

**Basic Card:**
```django
<div class="bg-white rounded-lg shadow-md p-6">
    Content
</div>
```

**Card with Accent Border:**
```django
<div class="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
    Content
</div>
```

**Card with Top Border:**
```django
<div class="bg-white rounded-lg shadow-md p-6 border-t-4 border-green-500">
    Content
</div>
```

**Hoverable Card:**
```django
<div class="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6 border-l-4 border-green-500">
    Content
</div>
```

---

### 9. Alert/Message Patterns

**Error Alert:**
```django
<div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
    Error message
</div>
```

**Success Alert:**
```django
<div class="bg-green-100 border border-green-300 text-green-700 px-4 py-3 rounded-lg">
    Success message
</div>
```

**Info Alert:**
```django
<div class="bg-blue-100 border border-blue-300 text-blue-700 px-4 py-3 rounded-lg">
    Information message
</div>
```

**Warning Alert:**
```django
<div class="bg-yellow-100 border border-yellow-300 text-yellow-700 px-4 py-3 rounded-lg">
    Warning message
</div>
```

---

### 10. Icon + Text Pattern

**Section Header:**
```django
<h3 class="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
    <i class="ri-[icon]-line text-green-600"></i> Section Title
</h3>
```

**Info Line:**
```django
<p class="text-gray-600 font-semibold mb-1">
    <i class="ri-[icon]-line text-green-600 mr-2"></i>Label
</p>
```

---

## Color Palette

### Primary Colors
- Green 600: `#16a34a` - Primary actions
- Green 700: `#15803d` - Hover state
- Green 500: `#22c55e` - Accents

### Secondary Colors
- Blue 600: `#2563eb` - Information
- Orange 600: `#ea580c` - Spending/Warning
- Red 600: `#dc2626` - Delete/Danger

### Neutral Colors
- Gray 800: `#1f2937` - Text
- Gray 600: `#4b5563` - Secondary text
- Gray 500: `#6b7280` - Muted text
- Gray 200: `#e5e7eb` - Borders

### Status Colors
- Planning: Blue (`#3b82f6`)
- Active: Green (`#22c55e`)
- Paused: Yellow (`#eab308`)
- Completed: Green 600 (`#16a34a`)

---

## Remix Icons Used

```
Navigation & UI:
ri-home-line          - Home
ri-arrow-right-s-line - Arrow right
ri-arrow-left-line    - Back arrow
ri-close-line         - Close/Cancel
ri-search-line        - Search

Actions:
ri-edit-line          - Edit
ri-delete-bin-line    - Delete
ri-eye-line           - View
ri-add-line           - Add/Create
ri-add-circle-line    - Add circle
ri-check-line         - Check/Complete
ri-check-double-line  - Check double

Content:
ri-information-line   - Information
ri-error-warning-line - Warning/Error
ri-layout-line        - Category/Layout
ri-settings-line      - Settings
ri-list-check         - Checklist

Domain Specific:
ri-farm-line          - Farm
ri-building-line      - Building
ri-projector-line     - Projects
ri-folder-line        - Folder
ri-folder-open-line   - Folder open
ri-progress-8-line    - Progress
ri-money-dollar-circle-line - Budget
ri-calendar-line      - Calendar
ri-calendar-check-line - Calendar check
ri-time-line          - Time
ri-admin-line         - Admin
```

---

## Spacing Scale

- 1 = 0.25rem (4px)
- 2 = 0.5rem (8px)
- 3 = 0.75rem (12px)
- 4 = 1rem (16px)
- 6 = 1.5rem (24px)
- 8 = 2rem (32px)
- 12 = 3rem (48px)

Used in templates:
- `p-6` - 24px padding (cards)
- `px-4 py-2` - 16px horizontal, 8px vertical (buttons)
- `px-6 py-3` - 24px horizontal, 12px vertical (large buttons)
- `gap-2` - 8px gap
- `gap-4` - 16px gap
- `gap-6` - 24px gap
- `mb-2` through `mb-8` - Margin bottom

---

## Responsive Breakpoints

```
Mobile First:  Default (< 640px)
Tablet:        md:     >= 768px
Desktop:       lg:     >= 1024px
Large:         xl:     >= 1280px

Used in Templates:
- grid-cols-1 md:grid-cols-2 lg:grid-cols-3
- flex-col md:flex-row
- px-4 (mobile) → px-6 (larger)
- text-sm md:text-base lg:text-lg
```

---

## Typography Hierarchy

```
Page Title:        text-3xl font-bold text-gray-800
Section Header:    text-lg font-bold text-gray-800
Subsection:        text-base font-semibold text-gray-700
Body Text:         text-sm font-normal text-gray-600
Small/Caption:     text-xs font-normal text-gray-500

Button Text:       text-sm font-semibold
Label Text:        text-sm font-semibold text-gray-700
Help Text:         text-sm text-gray-600
Error Text:        text-sm text-red-600
```

---

## Shadow Scale

```
No Shadow:         (no shadow class)
Subtle:            shadow-sm
Medium:            shadow-md (default card)
Large:             shadow-lg (cards on hover)
Extra Large:       shadow-xl (modals)

Used in Templates:
- shadow-md on cards
- hover:shadow-lg on hoverable cards
```

---

## Animation/Transition Classes

```
Transitions Used:
- transition          - Basic transition
- hover:opacity-75    - Opacity on hover
- focus:ring-2        - Focus ring on form fields
- focus:ring-green-500 - Green focus ring

Custom Styles:
- duration-300        - 300ms transition
- ease-in-out         - Easing function
```

---

## Common Component Combinations

### Project Card Combination
```django
<div class="bg-white rounded-lg shadow-md hover:shadow-lg transition p-6 border-l-4 border-green-500">
    <!-- Header with badges -->
    <div class="flex items-center gap-3 mb-2 flex-wrap">
        <h2 class="text-xl font-bold text-gray-800">{{ project.name }}</h2>
        <span class="px-3 py-1 rounded-full text-sm font-semibold bg-green-100 text-green-800">
            {{ project.get_status_display }}
        </span>
    </div>
    
    <!-- Grid of info -->
    <div class="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm mt-4">
        <div><p class="text-gray-600 font-medium">Farm</p><p class="text-gray-800">{{ project.farm.name }}</p></div>
    </div>
    
    <!-- Progress bar -->
    <div class="mt-4 pt-4 border-t border-gray-200">
        <div class="flex items-center justify-between mb-2">
            <span class="text-sm font-medium text-gray-700">Progress</span>
            <span class="text-sm font-semibold text-gray-800">{{ project.progress }}%</span>
        </div>
        <div class="w-full bg-gray-200 rounded-full h-2">
            <div class="bg-green-600 h-2 rounded-full" style="width: {{ project.progress }}%"></div>
        </div>
    </div>
    
    <!-- Action buttons -->
    <div class="flex gap-2 mt-4">
        <a href="#" class="flex-1 bg-blue-600 text-white px-4 py-2 rounded text-center text-sm font-semibold">View</a>
        {% if can_edit %}<a href="#" class="flex-1 bg-green-600 text-white px-4 py-2 rounded text-center text-sm font-semibold">Edit</a>{% endif %}
    </div>
</div>
```

This produces a professional, functional project card with all key information and interaction options.

