from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('api/tasks/add/', views.add_task, name='add_task'),
    path('api/tasks/delete/<int:task_id>/', views.delete_task, name='delete_task'),
]
