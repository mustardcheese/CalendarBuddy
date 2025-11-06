from django import forms
from .models import Task, EventCategory

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'date', 'location', 'color', 'category']
        widgets = {
            'title': forms.Textarea(attrs={
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default color if needed
        if not self.instance.pk:  # Only for new tasks
            self.initial['color'] = 'blue'

class CalendarSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search tasks...',
            'class': 'form-control form-control-sm'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=EventCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
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