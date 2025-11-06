# calendar_app/urls.py
from django.urls import path
from . import views

app_name = 'calendar_app'

urlpatterns = [
    path('', views.calendar_view, name='calendar_view'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('user-page/', views.user_page, name='user_page'),
]