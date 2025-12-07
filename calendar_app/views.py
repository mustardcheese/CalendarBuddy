from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime, date
from django.utils import timezone
from datetime import timedelta
import requests
import calendar
from django.contrib import messages
from home.models import Task  # Use Task from home app
from .forms import TaskForm, CalendarSearchForm, DocumentUploadForm, DocumentFilterForm
from .models import Document
import json
import urllib.parse


@login_required
def calendar_view(request):
    # Get current month/year or from request
    today = date.today()
    month = int(request.GET.get("month", today.month))
    year = int(request.GET.get("year", today.year))

    # Handle task creation
    task_form = TaskForm(request.POST or None)

    # DEBUG: Print what's happening
    print(f"=== CALENDAR VIEW DEBUG ===")
    print(f"Request method: {request.method}")

    if request.method == "POST":
        print("✅ FORM SUBMITTED!")

        # Check if this is a task submission
        if "add_task" in request.POST:
            print("✅ ADD TASK FORM DETECTED!")

            if task_form.is_valid():
                print("✅ FORM IS VALID!")
                task = task_form.save(commit=False)
                task.user = request.user

                # Check for conflicts
                conflicts = Task.get_conflicts(
                    user=request.user,
                    date=task.date,
                    start_time=task.start_time,
                    end_time=task.end_time,
                )

                if conflicts.exists():
                    conflict_list = ", ".join(
                        [
                            f"'{c.title}' ({c.start_time.strftime('%I:%M %p')} - {c.end_time.strftime('%I:%M %p')})"
                            for c in conflicts
                        ]
                    )
                    messages.warning(
                        request, f"⚠️ Time conflict detected with: {conflict_list}"
                    )

                task.save()
                messages.success(request, f"Task '{task.title}' created successfully!")

                # Redirect to clear the form and show the new task
                return redirect("calendar_app:calendar_view")
            else:
                print("❌ FORM ERRORS:", task_form.errors)

    # Handle search and filters
    search_form = CalendarSearchForm(request.GET or None)
    # Get tasks assigned to user OR to groups the user is a member of
    tasks = Task.objects.filter(
        Q(user=request.user) | Q(group__memberships__user=request.user)
    ).distinct()

    if search_form.is_valid():
        search_keyword = search_form.cleaned_data.get("search")
        category_filter = search_form.cleaned_data.get("category")
        start_date = search_form.cleaned_data.get("start_date")
        end_date = search_form.cleaned_data.get("end_date")

        # Apply filters
        if search_keyword:
            tasks = tasks.filter(
                Q(title__icontains=search_keyword)
                | Q(description__icontains=search_keyword)
                | Q(location__icontains=search_keyword)
            )

        if category_filter:
            tasks = tasks.filter(category=category_filter)

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
        "month": month,
        "year": year,
        "month_name": date(year, month, 1).strftime("%B"),
        "calendar": month_days,
        "tasks_by_date": tasks_by_date,
        "prev_month": prev_month,
        "prev_year": prev_year,
        "next_month": next_month,
        "next_year": next_year,
        "task_form": task_form,
        "search_form": search_form,
        "search_keyword": request.GET.get("search", ""),
        "filter_date": request.GET.get("filter_date"),
        "filter_location": request.GET.get("filter_location"),
        "filter_event": request.GET.get("filter_event"),
    }

    return render(request, "calendar_app/calendar.html", context)


@login_required
def delete_task(request, task_id):
    # Get task that belongs to user OR their groups
    task = get_object_or_404(
        Task,
        Q(id=task_id)
        & (Q(user=request.user) | Q(group__memberships__user=request.user)),
    )
    if request.method == "POST":
        # Check if task can be deleted (respects is_deletable for assigned tasks)
        if task.can_be_deleted_by(request.user):
            task.delete()
        else:
            # Can add a message here if desired
            pass
        return redirect("calendar_app:calendar_view")
    return redirect("calendar_app:calendar_view")


def get_weather(lat, long):
    headers = {"User-Agent": "calender_buddy", "Accept": "application/json"}
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
    print("test", first_period)
    return {
        "name": first_period["name"],
        "temperature": first_period["temperature"],
        "temperatureUnit": first_period["temperatureUnit"],
        "precipitation": first_period.get("probabilityOfPrecipitation", {}).get(
            "value", 0
        ),
        "detailedForecast": first_period["detailedForecast"],
    }


@login_required
def user_page(request):
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + timedelta(days=6)  # Sunday

    # Filter tasks for the user OR group tasks
    weekly_tasks = (
        Task.objects.filter(
            Q(user=request.user) | Q(group__memberships__user=request.user),
            date__range=[start_of_week, end_of_week],
            completed=False,
        )
        .distinct()
        .order_by("date", "start_time")
    )

    # ---------- BUILD MAP MARKERS ----------
    markers = []

    for task in weekly_tasks:
        if task.location and task.location.strip():
            try:
                query = urllib.parse.quote(task.location)
                url = (
                    f"https://nominatim.openstreetmap.org/search"
                    f"?q={query}&format=json&limit=1"
                )
                headers = {"User-Agent": "calendar_buddy_app"}

                r = requests.get(url, headers=headers, timeout=5)
                data = r.json()

                if data:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])

                    markers.append(
                        {
                            "title": task.title,
                            "location": task.location,
                            "lat": lat,
                            "lon": lon,
                            "date": str(task.date),
                        }
                    )

            except Exception as e:
                print("GEOCODING ERROR:", e)

    markers_json = json.dumps(markers)

    # ---------- WEATHER ----------
    weather = get_weather(33.7756, -84.3963)

    context = {
        "weekly_tasks": weekly_tasks,
        "start_of_week": start_of_week,
        "end_of_week": end_of_week,
        "weather": weather,
        "markers_json": markers_json,  # ← CRITICAL
    }

    return render(request, "calendar_app/user_page.html", context)


def complete_task(request, task_id):
    task = get_object_or_404(
        Task,
        Q(id=task_id)
        & (Q(user=request.user) | Q(group__memberships__user=request.user)),
    )
    task.completed = True
    task.save()
    return redirect("calendar_app:user_page")


# ================== DOCUMENT VIEWS ==================


@login_required
def upload_document(request):
    """Handle document uploads"""
    if request.method == "POST":
        form = DocumentUploadForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.user = request.user
            document.save()
            messages.success(request, f'"{document.title}" uploaded successfully!')
            return redirect("calendar_app:document_list")  # ← ADDED calendar_app:
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = DocumentUploadForm(user=request.user)

    return render(
        request,
        "calendar_app/upload_document.html",
        {"form": form, "title": "Upload Document"},
    )


@login_required
def document_list(request):
    """Display all documents with filtering options"""
    documents = Document.objects.filter(user=request.user)

    # Initialize filter form with current user
    filter_form = DocumentFilterForm(request.user, request.GET or None)

    if filter_form.is_valid():
        tag_filter = filter_form.cleaned_data.get("tag")
        task_filter = filter_form.cleaned_data.get("task")

        if tag_filter:
            documents = documents.filter(tags__icontains=tag_filter)

        if task_filter:
            documents = documents.filter(task=task_filter)

    # Get all unique tags for tag cloud/quick filter
    all_tags = set()
    for doc in Document.objects.filter(user=request.user):
        if doc.tags:
            for tag in doc.tags.split(","):
                cleaned_tag = tag.strip()
                if cleaned_tag:
                    all_tags.add(cleaned_tag)

    # Count documents by type for statistics
    doc_stats = {
        "total": documents.count(),
        "images": documents.filter(file_type="image").count(),
        "pdfs": documents.filter(file_type="pdf").count(),
        "documents": documents.filter(
            file_type__in=["document", "spreadsheet", "presentation", "text"]
        ).count(),
    }

    context = {
        "documents": documents,
        "all_tags": sorted(all_tags),
        "filter_form": filter_form,
        "doc_stats": doc_stats,
        "title": "My Documents",
    }

    return render(request, "calendar_app/document_list.html", context)


@login_required
def document_detail(request, document_id):
    """Display detailed view of a single document"""
    document = get_object_or_404(Document, id=document_id, user=request.user)

    # Get related documents (same tags or same task)
    related_documents = Document.objects.filter(user=request.user).exclude(
        id=document_id
    )

    if document.tags:
        tag_list = document.tag_list()
        if tag_list:
            related_documents = related_documents.filter(
                Q(tags__icontains=tag_list[0]) | Q(task=document.task)
            ).distinct()[:4]

    context = {
        "document": document,
        "related_documents": related_documents,
        "title": document.title,
    }

    return render(request, "calendar_app/document_detail.html", context)


@login_required
def delete_document(request, document_id):
    """Delete a document"""
    document = get_object_or_404(Document, id=document_id, user=request.user)

    if request.method == "POST":
        document_title = document.title
        document.delete()
        messages.success(request, f'"{document_title}" has been deleted.')
        return redirect("calendar_app:document_list")  # ← ADDED calendar_app:

    return render(
        request,
        "calendar_app/confirm_delete.html",
        {"document": document, "title": "Delete Document"},
    )


@login_required
def task_documents(request, task_id):
    """View all documents linked to a specific task"""
    task = get_object_or_404(
        Task,
        Q(id=task_id)
        & (Q(user=request.user) | Q(group__memberships__user=request.user)),
    )

    documents = Document.objects.filter(user=request.user, task=task)

    context = {
        "task": task,
        "documents": documents,
        "title": f"Documents for {task.title}",
    }

    return render(request, "calendar_app/task_documents.html", context)
