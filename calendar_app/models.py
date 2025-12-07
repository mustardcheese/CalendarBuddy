# calendar_app/models.py
from django.db import models
from django.contrib.auth.models import User
from home.models import Task  # Import Task from home app

class Document(models.Model):
    """Model for storing uploaded documents/images linked to tasks"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to='documents/%Y/%m/%d/')
    file_type = models.CharField(max_length=50, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    task = models.ForeignKey(Task, on_delete=models.SET_NULL, 
                            null=True, blank=True, related_name='documents')
    description = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def save(self, *args, **kwargs):
        # Auto-detect file type from extension
        if not self.file_type:
            ext = self.file.name.split('.')[-1].lower()
            image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
            if ext in image_extensions:
                self.file_type = 'image'
            elif ext in ['pdf']:
                self.file_type = 'pdf'
            elif ext in ['doc', 'docx']:
                self.file_type = 'document'
            elif ext in ['xls', 'xlsx', 'csv']:
                self.file_type = 'spreadsheet'
            elif ext in ['ppt', 'pptx']:
                self.file_type = 'presentation'
            elif ext in ['txt', 'md', 'rtf']:
                self.file_type = 'text'
            elif ext in ['zip', 'rar', '7z', 'tar', 'gz']:
                self.file_type = 'archive'
            else:
                self.file_type = 'other'
        
        # Extract title from filename if not provided
        if not self.title:
            import re
            filename = self.file.name.split('/')[-1].split('.')[0]
            # Convert snake_case and kebab-case to Title Case
            filename = re.sub(r'[_\-]', ' ', filename)
            self.title = filename.title()
            
        super().save(*args, **kwargs)
    
    def get_file_icon(self):
        """Return appropriate Bootstrap icon class based on file type"""
        icons = {
            'image': 'bi-file-image',
            'pdf': 'bi-file-pdf',
            'document': 'bi-file-word',
            'spreadsheet': 'bi-file-excel',
            'presentation': 'bi-file-ppt',
            'text': 'bi-file-text',
            'archive': 'bi-file-zip',
            'other': 'bi-file-earmark'
        }
        return icons.get(self.file_type, 'bi-file-earmark')
    
    def get_file_size(self):
        """Return human-readable file size"""
        try:
            bytes = self.file.size
            if bytes < 1024:
                return f"{bytes} B"
            elif bytes < 1024 * 1024:
                return f"{bytes / 1024:.1f} KB"
            elif bytes < 1024 * 1024 * 1024:
                return f"{bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{bytes / (1024 * 1024 * 1024):.1f} GB"
        except:
            return "Unknown size"
    
    def tag_list(self):
        """Return tags as a list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def __str__(self):
        return self.title