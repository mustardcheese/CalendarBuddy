from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime, date
import calendar
from .models import Task  # Removed EventCategory import
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
    tasks = Task.objects.filter(user=request.user)
    
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
                Q(location__icontains=search_keyword) |
                Q(category__icontains=search_keyword)  # FIXED: Added missing pipe character
            )
        
        if category_filter:
            tasks = tasks.filter(category__icontains=category_filter)
        
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
    task = get_object_or_404(Task, id=task_id, user=request.user)
    if request.method == 'POST':
        task.delete()
        return redirect('calendar_app:calendar_view')
    return redirect('calendar_app:calendar_view')