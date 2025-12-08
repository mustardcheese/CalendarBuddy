from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, time

# Create your models here.


class Group(models.Model):
    """
    Represents a group/team where admins can assign tasks to members
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_groups"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class GroupMembership(models.Model):
    """
    Links users to groups with role-based permissions
    """

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("member", "Member"),
    ]

    group = models.ForeignKey(
        Group, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="group_memberships"
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="member")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["group", "user"]
        ordering = ["group", "role", "user__username"]

    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.role})"

    def is_admin(self):
        return self.role == "admin"


class Project(models.Model):
    """
    Represents a project where admins can add collaborators to view shared calendar
    """

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="created_projects"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]

    def get_all_members(self):
        """Returns all users who are members of this project"""
        return User.objects.filter(project_memberships__project=self)

    def is_admin(self, user):
        """Check if a user is an admin of this project"""
        return self.memberships.filter(user=user, role="admin").exists()

    def is_member(self, user):
        """Check if a user is a member of this project"""
        return self.memberships.filter(user=user).exists()


class ProjectMembership(models.Model):
    """
    Links users to projects with role-based permissions
    """

    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("collaborator", "Collaborator"),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="memberships"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="project_memberships"
    )
    role = models.CharField(max_length=15, choices=ROLE_CHOICES, default="collaborator")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["project", "user"]
        ordering = ["project", "role", "user__username"]

    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.role})"

    def is_admin(self):
        return self.role == "admin"


class Task(models.Model):
    COLOR_CHOICES = [
        ("blue", "Blue"),
        ("green", "Green"),
        ("red", "Red"),
        ("yellow", "Yellow"),
        ("purple", "Purple"),
        ("orange", "Orange"),
    ]

    CATEGORY_CHOICES = [
        ("work", "Work"),
        ("personal", "Personal"),
        ("school", "School"),
        ("health", "Health"),
        ("social", "Social"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="tasks",
        null=True,
        blank=True,
        help_text="User this task is assigned to (leave empty if assigning to a group)",
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    start_time = models.TimeField(
        null=True, blank=True, help_text="Start time of the task"
    )
    end_time = models.TimeField(null=True, blank=True, help_text="End time of the task")
    location = models.CharField(max_length=200, blank=True)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES, default="blue")
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, blank=True, default=""
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed = models.BooleanField(default=False)

    # Task assignment fields
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_tasks",
        help_text="Admin who assigned this task",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks",
        help_text="Group this task was assigned to (leave empty if assigning to a user)",
    )
    is_deletable = models.BooleanField(
        default=True, help_text="Whether the user can delete this task"
    )
    project = models.ForeignKey(
        "Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tasks",
        help_text="Project this task belongs to",
    )

    class Meta:
        ordering = ["date", "start_time", "created_at"]

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

    @classmethod
    def get_conflicts(cls, user, date, start_time, end_time, exclude_task_id=None):
        """
        Find tasks that conflict with the given time range.
        Returns a queryset of conflicting tasks.
        """
        from django.db.models import Q

        if not start_time or not end_time:
            return cls.objects.none()

        # Get tasks for this user on this date that have times set
        tasks = cls.objects.filter(
            Q(user=user) | Q(group__memberships__user=user),
            date=date,
            start_time__isnull=False,
            end_time__isnull=False,
        )

        if exclude_task_id:
            tasks = tasks.exclude(id=exclude_task_id)

        # Find overlapping tasks
        # Conflict exists if: existing_start < new_end AND existing_end > new_start
        conflicts = tasks.filter(start_time__lt=end_time, end_time__gt=start_time)

        return conflicts.distinct()
