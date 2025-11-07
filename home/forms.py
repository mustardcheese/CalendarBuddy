from django import forms
from django.contrib.auth.models import User
from .models import Group, Task


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }


class GroupCreateForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Study Group, Project Team'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional description'}),
        }


class TaskAssignmentForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Task title'})
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Task description'})
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    location = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Location (optional)'})
    )
    color = forms.ChoiceField(
        choices=Task.COLOR_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    is_deletable = forms.BooleanField(
        required=False,
        initial=True,
        label="Allow users to delete this task",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    assign_to_all = forms.BooleanField(
        required=False,
        initial=False,
        label="Assign to all group members",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'assign_to_all'})
    )
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label="Or select specific users"
    )

    def __init__(self, *args, **kwargs):
        group = kwargs.pop('group', None)
        super().__init__(*args, **kwargs)
        if group:
            # Only show users who are members of this group
            self.fields['users'].queryset = User.objects.filter(
                group_memberships__group=group
            ).distinct().order_by('username')

    def clean(self):
        cleaned_data = super().clean()
        assign_to_all = cleaned_data.get('assign_to_all')
        users = cleaned_data.get('users')

        if not assign_to_all and not users:
            raise forms.ValidationError("Please either select 'Assign to all' or choose specific users.")

        return cleaned_data
