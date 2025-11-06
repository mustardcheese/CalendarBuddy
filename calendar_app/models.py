from django.db import models
from django.contrib.auth.models import User

class EventCategory(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#007bff')
    
    def __str__(self):
        return self.name

class Task(models.Model):
    COLOR_CHOICES = [
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('red', 'Red'),
        ('yellow', 'Yellow'),
        ('purple', 'Purple'),
        ('orange', 'Orange'),
    ]
    
    title = models.CharField(max_length=200)  # Short title/name
    description = models.TextField(blank=True)  # Longer description
    date = models.DateField()
    location = models.CharField(max_length=200, blank=True)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='blue')
    category = models.CharField(max_length=50, blank=True, default='')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title