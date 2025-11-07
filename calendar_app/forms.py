from django import forms
from home.models import Task

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'date', 'location', 'color', 'category']
        widgets = {
            'title': forms.TextInput(attrs={  # Changed from Textarea to TextInput
                'class': 'form-control form-control-sm',
                'placeholder': 'Enter task title...'
            }),
            'description': forms.Textarea(attrs={  # Separate description field
                'rows': 3,
                'class': 'form-control form-control-sm',
                'placeholder': 'Enter task description...'
            }),
            'date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control form-control-sm'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control form-control-sm',
                'placeholder': 'Enter location...'
            }),
            'color': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select form-select-sm'
            }),
        }

class CalendarSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search tasks...',
            'class': 'form-control form-control-sm'
        })
    )
    
    category = forms.ChoiceField(
        required=False,
        choices=[('', 'All Categories')] + Task.CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select form-select-sm'
        }),
        label="Category"
    )
    
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm'
        }),
        label="From Date"
    )
    
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control form-control-sm'
        }),
        label="To Date"
    )