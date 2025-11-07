from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Group(models.Model):
    """
    Represents a group/team where admins can assign tasks to members
    """
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class GroupMembership(models.Model):
    """
    Links users to groups with role-based permissions
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['group', 'user']
        ordering = ['group', 'role', 'user__username']

    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.role})"

    def is_admin(self):
        return self.role == 'admin'


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

    # Task assignment fields
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks',
        help_text="Admin who assigned this task"
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tasks',
        help_text="Group this task was assigned from"
    )
    is_deletable = models.BooleanField(
        default=True,
        help_text="Whether the user can delete this task"
    )

    class Meta:
        ordering = ['date', 'created_at']

    def __str__(self):
        return f"{self.title} - {self.date}"

    def is_assigned_task(self):
        """Returns True if this is an assigned task (not personal)"""
        return self.assigned_by is not None and self.group is not None

    def can_be_deleted_by(self, user):
        """Check if a user can delete this task"""
        # Own personal tasks can always be deleted
        if not self.is_assigned_task():
            return True
        # Assigned tasks depend on is_deletable flag
        return self.is_deletable
