from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime, date
from django.utils import timezone
from datetime import timedelta
import requests
import calendar
from home.models import Task  # Use Task from home app
from .forms import TaskForm, CalendarSearchForm

@login_required
def calendar_view(request):
    # Get current month/year or from request
    today = date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))
    
    # Handle task creation
    task_form = TaskForm(request.POST or None)
    
    # DEBUG: Print what's happening
    print(f"=== CALENDAR VIEW DEBUG ===")
    print(f"Request method: {request.method}")
    
    if request.method == 'POST':
        print("✅ FORM SUBMITTED!")
        
        # Check if this is a task submission
        if 'add_task' in request.POST:
            print("✅ ADD TASK FORM DETECTED!")
            
            if task_form.is_valid():
                print("✅ FORM IS VALID!")
                task = task_form.save(commit=False)
                task.user = request.user
                task.save()
                print(f"✅ TASK SAVED: '{task.title}' on {task.date}")
                
                # Redirect to clear the form and show the new task
                return redirect('calendar_app:calendar_view')
            else:
                print("❌ FORM ERRORS:", task_form.errors)
    
    # Handle search and filters
    search_form = CalendarSearchForm(request.GET or None)
    # Get tasks assigned to user OR to groups the user is a member of
    tasks = Task.objects.filter(
        Q(user=request.user) |
        Q(group__memberships__user=request.user)
    ).distinct()
    
    if search_form.is_valid():
        search_keyword = search_form.cleaned_data.get('search')
        category_filter = search_form.cleaned_data.get('category')
        start_date = search_form.cleaned_data.get('start_date')
        end_date = search_form.cleaned_data.get('end_date')
        
        # Apply filters
        if search_keyword:
            tasks = tasks.filter(
                Q(title__icontains=search_keyword) |
                Q(description__icontains=search_keyword) |
                Q(location__icontains=search_keyword)
            )
        
        if start_date:
            tasks = tasks.filter(date__gte=start_date)
        if end_date:
            tasks = tasks.filter(date__lte=end_date)
    
    # Calendar logic
    cal = calendar.Calendar(firstweekday=6)  # Start with Sunday
    month_days = cal.monthdayscalendar(year, month)
    
    # Get tasks for the current month view
    tasks_by_date = {}
    for task in tasks.filter(date__year=year, date__month=month):
        day = task.date.day
        if day not in tasks_by_date:
            tasks_by_date[day] = []
        tasks_by_date[day].append(task)
    
    # Navigation
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    
    context = {
        'month': month,
        'year': year,
        'month_name': date(year, month, 1).strftime('%B'),
        'calendar': month_days,
        'tasks_by_date': tasks_by_date,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'task_form': task_form,
        'search_form': search_form,
        'search_keyword': request.GET.get('search', ''),
        'filter_date': request.GET.get('filter_date'),
        'filter_location': request.GET.get('filter_location'),
        'filter_event': request.GET.get('filter_event'),
    }
    
    return render(request, 'calendar_app/calendar.html', context)

@login_required
def delete_task(request, task_id):
    # Get task that belongs to user OR their groups
    task = get_object_or_404(
        Task,
        Q(id=task_id) & (Q(user=request.user) | Q(group__memberships__user=request.user))
    )
    if request.method == 'POST':
        # Check if task can be deleted (respects is_deletable for assigned tasks)
        if task.can_be_deleted_by(request.user):
            task.delete()
        else:
            # Can add a message here if desired
            pass
        return redirect('calendar_app:calendar_view')
    return redirect('calendar_app:calendar_view')


def get_weather(lat, long):
    headers = {
        "User-Agent": "calender_buddy",
        "Accept": "application/json"
    }
    points_url = f"https://api.weather.gov/points/{lat},{long}"
    print("Fetching weather data from:", points_url)
    resp = requests.get(points_url, headers=headers)
    print("Status code:", resp.status_code)
    print("Content snippet:", resp.text[:500])
    
    if resp.status_code != 200:
        return {}
    grid_data = resp.json()
    if "properties" not in grid_data:
        print("No properties key found in response!")
        return {}
    forecast_url = grid_data["properties"]["forecast"]

    forecast_resp = requests.get(forecast_url, headers=headers)
    if forecast_resp.status_code != 200:
        return {}

    forecast_data = forecast_resp.json()
    # Return just the first period (today or next)
    first_period = forecast_data["properties"]["periods"][0]
    print("test",first_period)
    return {
        "name": first_period["name"],
        "temperature": first_period["temperature"],
        "temperatureUnit": first_period["temperatureUnit"],
        "precipitation": first_period.get("probabilityOfPrecipitation", {}).get("value", 0),
        "detailedForecast": first_period["detailedForecast"]
    }


@login_required
def user_page(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    # Filter tasks for the current user OR groups they're in, within this week
    weekly_tasks = Task.objects.filter(
        Q(user=request.user) | Q(group__memberships__user=request.user),
        date__range=[start_of_week, end_of_week]
    ).distinct().order_by('date')

    weather = get_weather(33.7756,-84.3963) 
    context = {
        'weekly_tasks': weekly_tasks,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'weather': weather,
    }

    return render(request, 'calendar_app/user_page.html', context)