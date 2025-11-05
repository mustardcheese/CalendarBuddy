from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Task(models.Model):
    COLOR_CHOICES = [
        ('blue', 'Blue'),
        ('green', 'Green'),
        ('red', 'Red'),
        ('yellow', 'Yellow'),
        ('purple', 'Purple'),
        ('orange', 'Orange'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    location = models.CharField(max_length=200, blank=True)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default='blue')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date', 'created_at']

    def __str__(self):
        return f"{self.title} - {self.date}"
