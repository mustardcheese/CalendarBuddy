from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Task, Group, GroupMembership, AssignedTask
import calendar
from datetime import datetime, date
import json

# Create your views here.

def index(request):
    """Landing page view"""
    return render(request, 'home/index.html')

def signup_view(request):
    """User signup view"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created successfully for {username}!')
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'home/signup.html', {'form': form})

def login_view(request):
    """User login view"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'home/login.html', {'form': form})

@login_required
def calendar_view(request):
    """Calendar view with tasks"""
    # Get current month and year from query params or use current date
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))

    # Get filter parameters
    filter_date = request.GET.get('filter_date') == 'on'
    filter_location = request.GET.get('filter_location') == 'on'
    filter_event = request.GET.get('filter_event') == 'on'
    search_keyword = request.GET.get('search', '')

    # Create calendar
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]

    # Get all tasks for current user
    tasks = Task.objects.filter(user=request.user)

    # Apply filters
    if search_keyword:
        tasks = tasks.filter(title__icontains=search_keyword)

    # Get tasks for the current month
    month_tasks = tasks.filter(date__year=year, date__month=month)

    # Get assigned tasks for groups the user is a member of
    user_groups = Group.objects.filter(memberships__user=request.user)
    assigned_tasks = AssignedTask.objects.filter(
        group__in=user_groups,
        date__year=year,
        date__month=month
    )

    # Apply search filter to assigned tasks
    if search_keyword:
        assigned_tasks = assigned_tasks.filter(title__icontains=search_keyword)

    # Organize tasks by date
    tasks_by_date = {}
    for task in month_tasks:
        day = task.date.day
        if day not in tasks_by_date:
            tasks_by_date[day] = []
        tasks_by_date[day].append({
            'task': task,
            'type': 'personal'
        })

    # Add assigned tasks to the calendar
    for assigned_task in assigned_tasks:
        day = assigned_task.date.day
        if day not in tasks_by_date:
            tasks_by_date[day] = []
        tasks_by_date[day].append({
            'task': assigned_task,
            'type': 'assigned',
            'group_name': assigned_task.group.name
        })

    # Calculate previous and next month
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    context = {
        'calendar': cal,
        'month_name': month_name,
        'year': year,
        'month': month,
        'tasks_by_date': tasks_by_date,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'filter_date': filter_date,
        'filter_location': filter_location,
        'filter_event': filter_event,
        'search_keyword': search_keyword,
    }

    return render(request, 'home/calendar.html', context)

@login_required
@require_http_methods(["POST"])
def add_task(request):
    """Add a new task via AJAX"""
    try:
        data = json.loads(request.body)
        task = Task.objects.create(
            user=request.user,
            title=data.get('title'),
            description=data.get('description', ''),
            date=data.get('date'),
            location=data.get('location', ''),
            color=data.get('color', 'blue')
        )
        return JsonResponse({
            'success': True,
            'task': {
                'id': task.id,
                'title': task.title,
                'date': task.date.isoformat(),
                'location': task.location,
                'color': task.color
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

@login_required
@require_http_methods(["DELETE"])
def delete_task(request, task_id):
    """Delete a task via AJAX"""
    try:
        task = get_object_or_404(Task, id=task_id, user=request.user)
        task.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


# Group Management Views

@login_required
def groups_list_view(request):
    """View all groups the user is a member of or admin of"""
    user_memberships = GroupMembership.objects.filter(user=request.user).select_related('group')
    admin_groups = [m.group for m in user_memberships if m.is_admin]
    member_groups = [m.group for m in user_memberships if not m.is_admin]

    context = {
        'admin_groups': admin_groups,
        'member_groups': member_groups,
    }
    return render(request, 'home/groups_list.html', context)


@login_required
@require_http_methods(["POST"])
def create_group(request):
    """Create a new group"""
    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return JsonResponse({'success': False, 'error': 'Group name is required'}, status=400)

        # Check if group name already exists
        if Group.objects.filter(name=name).exists():
            return JsonResponse({'success': False, 'error': 'Group name already exists'}, status=400)

        # Create the group
        group = Group.objects.create(
            name=name,
            description=description,
            created_by=request.user
        )

        # Add creator as admin
        GroupMembership.objects.create(
            user=request.user,
            group=group,
            is_admin=True
        )

        return JsonResponse({
            'success': True,
            'group': {
                'id': group.id,
                'name': group.name,
                'description': group.description
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def group_detail_view(request, group_id):
    """View group details and members"""
    group = get_object_or_404(Group, id=group_id)

    # Check if user is a member of this group
    membership = GroupMembership.objects.filter(user=request.user, group=group).first()
    if not membership:
        messages.error(request, 'You are not a member of this group.')
        return redirect('groups_list')

    members = GroupMembership.objects.filter(group=group).select_related('user')
    assigned_tasks = AssignedTask.objects.filter(group=group).order_by('-date')

    # Get all users for adding to group (exclude current members)
    current_member_ids = [m.user.id for m in members]
    available_users = User.objects.exclude(id__in=current_member_ids)

    context = {
        'group': group,
        'membership': membership,
        'members': members,
        'assigned_tasks': assigned_tasks,
        'available_users': available_users,
    }
    return render(request, 'home/group_detail.html', context)


@login_required
@require_http_methods(["POST"])
def add_member_to_group(request, group_id):
    """Add a member to a group (admin only)"""
    try:
        group = get_object_or_404(Group, id=group_id)

        # Check if requester is admin
        membership = GroupMembership.objects.filter(user=request.user, group=group, is_admin=True).first()
        if not membership:
            return JsonResponse({'success': False, 'error': 'Only group admins can add members'}, status=403)

        data = json.loads(request.body)
        user_id = data.get('user_id')
        is_admin = data.get('is_admin', False)

        user = get_object_or_404(User, id=user_id)

        # Check if user is already a member
        if GroupMembership.objects.filter(user=user, group=group).exists():
            return JsonResponse({'success': False, 'error': 'User is already a member'}, status=400)

        # Add user to group
        new_membership = GroupMembership.objects.create(
            user=user,
            group=group,
            is_admin=is_admin
        )

        return JsonResponse({
            'success': True,
            'membership': {
                'id': new_membership.id,
                'user': user.username,
                'is_admin': is_admin
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def remove_member_from_group(request, group_id, user_id):
    """Remove a member from a group (admin only)"""
    try:
        group = get_object_or_404(Group, id=group_id)

        # Check if requester is admin
        requester_membership = GroupMembership.objects.filter(user=request.user, group=group, is_admin=True).first()
        if not requester_membership:
            return JsonResponse({'success': False, 'error': 'Only group admins can remove members'}, status=403)

        # Get the membership to remove
        membership = get_object_or_404(GroupMembership, user_id=user_id, group=group)

        # Prevent removing the last admin
        admin_count = GroupMembership.objects.filter(group=group, is_admin=True).count()
        if membership.is_admin and admin_count <= 1:
            return JsonResponse({'success': False, 'error': 'Cannot remove the last admin from the group'}, status=400)

        membership.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["POST"])
def assign_task_to_group(request, group_id):
    """Assign a task to a group (admin only)"""
    try:
        group = get_object_or_404(Group, id=group_id)

        # Check if requester is admin
        membership = GroupMembership.objects.filter(user=request.user, group=group, is_admin=True).first()
        if not membership:
            return JsonResponse({'success': False, 'error': 'Only group admins can assign tasks'}, status=403)

        data = json.loads(request.body)
        assigned_task = AssignedTask.objects.create(
            group=group,
            assigned_by=request.user,
            title=data.get('title'),
            description=data.get('description', ''),
            date=data.get('date'),
            location=data.get('location', ''),
            color=data.get('color', 'blue')
        )

        return JsonResponse({
            'success': True,
            'task': {
                'id': assigned_task.id,
                'title': assigned_task.title,
                'date': assigned_task.date.isoformat(),
                'location': assigned_task.location,
                'color': assigned_task.color
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
@require_http_methods(["DELETE"])
def delete_assigned_task(request, task_id):
    """Delete an assigned task (admin only)"""
    try:
        assigned_task = get_object_or_404(AssignedTask, id=task_id)

        # Check if requester is admin of the group
        membership = GroupMembership.objects.filter(
            user=request.user,
            group=assigned_task.group,
            is_admin=True
        ).first()

        if not membership:
            return JsonResponse({'success': False, 'error': 'Only group admins can delete assigned tasks'}, status=403)

        assigned_task.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)
