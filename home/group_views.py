from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.db.models import Q
from .models import Group, GroupMembership, Task
from .forms import GroupCreateForm, TaskAssignmentForm


@login_required
def group_list(request):
    """Display all groups the user is a member of"""
    memberships = request.user.group_memberships.select_related('group').all()

    # Separate admin and regular member groups
    admin_groups = [m for m in memberships if m.is_admin()]
    member_groups = [m for m in memberships if not m.is_admin()]

    context = {
        'admin_groups': admin_groups,
        'member_groups': member_groups,
    }
    return render(request, 'home/group_list.html', context)


@login_required
def group_create(request):
    """Create a new group (user becomes admin)"""
    if request.method == 'POST':
        form = GroupCreateForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()

            # Add creator as admin
            GroupMembership.objects.create(
                group=group,
                user=request.user,
                role='admin'
            )

            messages.success(request, f'Group "{group.name}" created successfully!')
            return redirect('group_detail', group_id=group.id)
    else:
        form = GroupCreateForm()

    return render(request, 'home/group_create.html', {'form': form})


@login_required
def group_detail(request, group_id):
    """View group details and members"""
    group = get_object_or_404(Group, id=group_id)

    # Check if user is a member
    membership = GroupMembership.objects.filter(
        group=group,
        user=request.user
    ).first()

    if not membership:
        messages.error(request, "You are not a member of this group.")
        return redirect('group_list')

    # Get all members
    memberships = group.memberships.select_related('user').all()

    # Get recent tasks assigned to this group
    recent_tasks = group.tasks.select_related('assigned_by', 'user').order_by('-created_at')[:10]

    context = {
        'group': group,
        'membership': membership,
        'is_admin': membership.is_admin(),
        'memberships': memberships,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'home/group_detail.html', context)


@login_required
def group_add_member(request, group_id):
    """Add a member to the group (admin only)"""
    group = get_object_or_404(Group, id=group_id)

    # Check if user is admin
    membership = GroupMembership.objects.filter(
        group=group,
        user=request.user,
        role='admin'
    ).first()

    if not membership:
        messages.error(request, "Only group admins can add members.")
        return redirect('group_detail', group_id=group_id)

    if request.method == 'POST':
        username = request.POST.get('username')
        role = request.POST.get('role', 'member')

        try:
            user = User.objects.get(username=username)

            # Check if already a member
            if GroupMembership.objects.filter(group=group, user=user).exists():
                messages.warning(request, f"{username} is already a member of this group.")
            else:
                GroupMembership.objects.create(
                    group=group,
                    user=user,
                    role=role
                )
                messages.success(request, f"{username} added to {group.name}.")
        except User.DoesNotExist:
            messages.error(request, f"User '{username}' not found.")

        return redirect('group_detail', group_id=group_id)

    # GET request - show form
    all_users = User.objects.exclude(
        id__in=group.memberships.values_list('user_id', flat=True)
    ).order_by('username')

    context = {
        'group': group,
        'available_users': all_users,
    }
    return render(request, 'home/group_add_member.html', context)


@login_required
def group_remove_member(request, group_id, user_id):
    """Remove a member from the group (admin only)"""
    if request.method != 'POST':
        return redirect('group_detail', group_id=group_id)

    group = get_object_or_404(Group, id=group_id)

    # Check if requester is admin
    requester_membership = GroupMembership.objects.filter(
        group=group,
        user=request.user,
        role='admin'
    ).first()

    if not requester_membership:
        messages.error(request, "Only group admins can remove members.")
        return redirect('group_detail', group_id=group_id)

    # Get the membership to remove
    membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)

    # Don't allow removing the creator
    if membership.user == group.created_by:
        messages.error(request, "Cannot remove the group creator.")
        return redirect('group_detail', group_id=group_id)

    username = membership.user.username
    membership.delete()
    messages.success(request, f"{username} removed from {group.name}.")

    return redirect('group_detail', group_id=group_id)


@login_required
def assign_task(request, group_id):
    """Assign a task to group members (admin only)"""
    group = get_object_or_404(Group, id=group_id)

    # Check if user is admin
    membership = GroupMembership.objects.filter(
        group=group,
        user=request.user,
        role='admin'
    ).first()

    if not membership:
        messages.error(request, "Only group admins can assign tasks.")
        return redirect('group_detail', group_id=group_id)

    if request.method == 'POST':
        form = TaskAssignmentForm(request.POST, group=group)
        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            date = form.cleaned_data['date']
            location = form.cleaned_data['location']
            color = form.cleaned_data['color']
            is_deletable = form.cleaned_data['is_deletable']
            assign_to_all = form.cleaned_data['assign_to_all']
            selected_users = form.cleaned_data.get('users', [])

            # Determine which users to assign to
            if assign_to_all:
                users = User.objects.filter(
                    group_memberships__group=group
                ).distinct()
            else:
                users = selected_users

            # Create tasks for each user
            tasks_created = 0
            for user in users:
                Task.objects.create(
                    user=user,
                    title=title,
                    description=description,
                    date=date,
                    location=location,
                    color=color,
                    assigned_by=request.user,
                    group=group,
                    is_deletable=is_deletable
                )
                tasks_created += 1

            messages.success(
                request,
                f'Task "{title}" assigned to {tasks_created} user(s) in {group.name}.'
            )
            return redirect('group_detail', group_id=group_id)
    else:
        form = TaskAssignmentForm(group=group)

    context = {
        'group': group,
        'form': form,
    }
    return render(request, 'home/assign_task.html', context)


@login_required
def my_assigned_tasks(request):
    """View all tasks assigned to the current user"""
    assigned_tasks = Task.objects.filter(
        user=request.user,
        assigned_by__isnull=False
    ).select_related('assigned_by', 'group').order_by('date', '-created_at')

    context = {
        'assigned_tasks': assigned_tasks,
    }
    return render(request, 'home/my_assigned_tasks.html', context)
