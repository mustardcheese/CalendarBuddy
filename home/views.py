from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Task
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
    year = int(request.GET.get('year', datetime.now().year))
    month = int(request.GET.get('month', datetime.now().month))

    # Ensure weeks start on Sunday
    calendar.setfirstweekday(calendar.SUNDAY)
    cal = calendar.monthcalendar(year, month)
    month_name = calendar.month_name[month]
    
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

    # Organize tasks by date
    tasks_by_date = {}
    for task in month_tasks:
        day = task.date.day
        if day not in tasks_by_date:
            tasks_by_date[day] = []
        tasks_by_date[day].append(task)

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

        # Parse the date string into a proper Python date object
        date_str = data.get('date')
        task_date = datetime.fromisoformat(date_str).date() if date_str else None

        task = Task.objects.create(
            user=request.user,
            title=data.get('title'),
            description=data.get('description', ''),
            date=task_date,  # use the parsed date here
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
