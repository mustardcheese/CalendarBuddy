from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Project, ProjectMembership, Task
from .forms import ProjectCreateForm


@login_required
def project_list(request):
    """Display all projects the user is a member of"""
    memberships = request.user.project_memberships.select_related('project').all()

    # Separate admin and collaborator projects
    admin_projects = [m for m in memberships if m.is_admin()]
    collaborator_projects = [m for m in memberships if not m.is_admin()]

    context = {
        'admin_projects': admin_projects,
        'collaborator_projects': collaborator_projects,
    }
    return render(request, 'home/project_list.html', context)


@login_required
def project_create(request):
    """Create a new project (user becomes admin)"""
    if request.method == 'POST':
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()

            # Add creator as admin
            ProjectMembership.objects.create(
                project=project,
                user=request.user,
                role='admin'
            )

            messages.success(request, f'Project "{project.name}" created successfully!')
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectCreateForm()

    return render(request, 'home/project_create.html', {'form': form})


@login_required
def project_detail(request, project_id):
    """View project details and members"""
    project = get_object_or_404(Project, id=project_id)

    # Check if user is a member
    membership = ProjectMembership.objects.filter(
        project=project,
        user=request.user
    ).first()

    if not membership:
        messages.error(request, "You are not a member of this project.")
        return redirect('project_list')

    # Get all members
    memberships = project.memberships.select_related('user').all()

    # Get recent tasks for this project
    recent_tasks = project.tasks.select_related('user').order_by('-created_at')[:10]

    context = {
        'project': project,
        'membership': membership,
        'is_admin': membership.is_admin(),
        'memberships': memberships,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'home/project_detail.html', context)


@login_required
def project_add_member(request, project_id):
    """Add a collaborator to the project (admin only)"""
    project = get_object_or_404(Project, id=project_id)

    # Check if user is admin
    membership = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
        role='admin'
    ).first()

    if not membership:
        messages.error(request, "Only project admins can add collaborators.")
        return redirect('project_detail', project_id=project_id)

    if request.method == 'POST':
        username = request.POST.get('username')
        role = request.POST.get('role', 'collaborator')

        try:
            user = User.objects.get(username=username)

            # Check if already a member
            if ProjectMembership.objects.filter(project=project, user=user).exists():
                messages.warning(request, f"{username} is already a member of this project.")
            else:
                ProjectMembership.objects.create(
                    project=project,
                    user=user,
                    role=role
                )
                messages.success(request, f"{username} added to {project.name}.")
        except User.DoesNotExist:
            messages.error(request, f"User '{username}' not found.")

        return redirect('project_detail', project_id=project_id)

    # GET request - show form
    all_users = User.objects.exclude(
        id__in=project.memberships.values_list('user_id', flat=True)
    ).order_by('username')

    context = {
        'project': project,
        'available_users': all_users,
    }
    return render(request, 'home/project_add_member.html', context)


@login_required
def project_remove_member(request, project_id, user_id):
    """Remove a collaborator from the project (admin only)"""
    if request.method != 'POST':
        return redirect('project_detail', project_id=project_id)

    project = get_object_or_404(Project, id=project_id)

    # Check if requester is admin
    requester_membership = ProjectMembership.objects.filter(
        project=project,
        user=request.user,
        role='admin'
    ).first()

    if not requester_membership:
        messages.error(request, "Only project admins can remove members.")
        return redirect('project_detail', project_id=project_id)

    # Get the membership to remove
    membership = get_object_or_404(ProjectMembership, project=project, user_id=user_id)

    # Don't allow removing the creator
    if membership.user == project.created_by:
        messages.error(request, "Cannot remove the project creator.")
        return redirect('project_detail', project_id=project_id)

    username = membership.user.username
    membership.delete()
    messages.success(request, f"{username} removed from {project.name}.")

    return redirect('project_detail', project_id=project_id)


@login_required
def project_calendar(request, project_id):
    """View shared calendar showing all project members' tasks"""
    project = get_object_or_404(Project, id=project_id)

    # Check if user is a member
    membership = ProjectMembership.objects.filter(
        project=project,
        user=request.user
    ).first()

    if not membership:
        messages.error(request, "You are not a member of this project.")
        return redirect('project_list')

    # Get all project members
    member_users = project.get_all_members()

    # Get tasks for all project members (both personal and project tasks)
    tasks = Task.objects.filter(
        Q(user__in=member_users) | Q(project=project)
    ).select_related('user', 'project').distinct().order_by('date', 'start_time')

    # Group tasks by user for display
    tasks_by_user = {}
    for member in member_users:
        member_tasks = tasks.filter(user=member)
        tasks_by_user[member] = member_tasks

    context = {
        'project': project,
        'membership': membership,
        'is_admin': membership.is_admin(),
        'tasks': tasks,
        'tasks_by_user': tasks_by_user,
        'members': member_users,
    }
    return render(request, 'home/project_calendar.html', context)
