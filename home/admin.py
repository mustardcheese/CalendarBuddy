from django.contrib import admin
from django.contrib.auth.models import Group as DjangoGroup
from django.core.exceptions import ValidationError
from django import forms
from .models import Task, Group, GroupMembership

# Register your models here.


class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1
    autocomplete_fields = ['user']


# Unregister Django's built-in Group model to remove it from auth section
admin.site.unregister(DjangoGroup)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at', 'member_count']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    inlines = [GroupMembershipInline]

    def member_count(self, obj):
        return obj.memberships.count()
    member_count.short_description = 'Members'


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'role', 'joined_at']
    list_filter = ['role', 'joined_at', 'group']
    search_fields = ['user__username', 'group__name']


class TaskAdminForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        group = cleaned_data.get('group')

        # Ensure at least one is selected
        if not user and not group:
            raise ValidationError('A task must be assigned to either a user or a group.')

        # Ensure only one is selected
        if user and group:
            raise ValidationError('A task can be assigned to either a user OR a group, not both.')

        return cleaned_data

    def save(self, commit=True):
        """Override save to ensure user field is properly set to None if not provided"""
        instance = super().save(commit=False)

        # Explicitly set user to None if it's not in cleaned_data or is empty
        if not self.cleaned_data.get('user'):
            instance.user = None

        if commit:
            instance.save()

        return instance


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm
    list_display = ['title', 'user', 'date', 'category', 'group', 'assigned_by', 'is_deletable', 'created_at']
    list_filter = ['date', 'color', 'category', 'is_deletable', 'group']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'date', 'location', 'color', 'category')
        }),
        ('Assignment', {
            'fields': ('user', 'group', 'assigned_by', 'is_deletable'),
            'description': 'Assign to EITHER a user OR a group (not both)'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Ensure user field is properly set to None if group is selected"""
        if obj.group and not obj.user:
            obj.user = None
        elif obj.user and not obj.group:
            obj.group = None
        super().save_model(request, obj, form, change)
