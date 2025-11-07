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

        if user and group:
            raise ValidationError('A task can be assigned to either a user OR a group, not both.')

        if not user and not group:
            raise ValidationError('A task must be assigned to either a user or a group.')

        return cleaned_data


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    form = TaskAdminForm
    list_display = ['title', 'user', 'date', 'group', 'assigned_by', 'is_deletable', 'created_at']
    list_filter = ['date', 'color', 'is_deletable', 'group']
    search_fields = ['title', 'description', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'date', 'location', 'color')
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
