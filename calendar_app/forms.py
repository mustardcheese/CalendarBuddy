from django import forms
from home.models import Task
from .models import Document  # Import Document from current app


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "date",
            "start_time",
            "end_time",
            "location",
            "color",
            "category",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "placeholder": "Enter task title...",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control form-control-sm",
                    "placeholder": "Enter task description...",
                }
            ),
            "date": forms.DateInput(
                attrs={"type": "date", "class": "form-control form-control-sm"}
            ),
            "start_time": forms.TimeInput(
                attrs={"type": "time", "class": "form-control form-control-sm"}
            ),
            "end_time": forms.TimeInput(
                attrs={"type": "time", "class": "form-control form-control-sm"}
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control form-control-sm",
                    "placeholder": "Enter location...",
                }
            ),
            "color": forms.Select(attrs={"class": "form-select form-select-sm"}),
            "category": forms.Select(attrs={"class": "form-select form-select-sm"}),
        }


class CalendarSearchForm(forms.Form):
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search tasks...",
                "class": "form-control form-control-sm",
            }
        ),
    )

    category = forms.ChoiceField(
        required=False,
        choices=[("", "All Categories")] + Task.CATEGORY_CHOICES,
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
        label="Category",
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control form-control-sm"}
        ),
        label="From Date",
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control form-control-sm"}
        ),
        label="To Date",
    )


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents linked to tasks"""

    class Meta:
        model = Document
        fields = ["file", "title", "description", "tags", "task"]
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Document title (optional)",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "form-control",
                    "placeholder": "Add a description...",
                }
            ),
            "tags": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "work, school, personal, etc.",
                }
            ),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "task": forms.Select(attrs={"class": "form-select"}),
        }
        labels = {
            "task": "Link to Task (Optional)",
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["title"].required = False
        if user:
            # Only show tasks belonging to the current user
            self.fields["task"].queryset = Task.objects.filter(user=user).order_by(
                "-date"
            )

    def clean_file(self):
        """Validate the uploaded file"""
        file = self.cleaned_data.get("file")
        if file:
            # Check file size (10MB limit)
            max_size = 10 * 1024 * 1024  # 10MB
            if file.size > max_size:
                raise forms.ValidationError(
                    f"File size must be less than 10MB. Your file is {file.size / (1024 * 1024):.1f}MB."
                )

            # Check file extensions
            valid_extensions = [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".bmp",
                ".webp",
                ".svg",  # Images
                ".pdf",  # PDFs
                ".doc",
                ".docx",  # Word
                ".xls",
                ".xlsx",
                ".csv",  # Excel/CSV
                ".ppt",
                ".pptx",  # PowerPoint
                ".txt",
                ".md",
                ".rtf",  # Text
                ".zip",
                ".rar",
                ".7z",
                ".tar",
                ".gz",  # Archives
            ]

            import os

            ext = os.path.splitext(file.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    "Unsupported file type. Please upload images, documents, or archives."
                )

        return file


class DocumentFilterForm(forms.Form):
    """Form for filtering documents"""

    tag = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Filter by tag..."}
        ),
        label="",
    )

    task = forms.ModelChoiceField(
        queryset=Task.objects.none(),  # Will be set in view
        required=False,
        empty_label="All Tasks",
        widget=forms.Select(attrs={"class": "form-select"}),
        label="",
    )

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Set the queryset for tasks belonging to the user
            self.fields["task"].queryset = Task.objects.filter(user=user).order_by(
                "-date"
            )
