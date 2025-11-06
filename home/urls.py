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

    # Group management URLs
    path('groups/', views.groups_list_view, name='groups_list'),
    path('groups/create/', views.create_group, name='create_group'),
    path('groups/<int:group_id>/', views.group_detail_view, name='group_detail'),
    path('groups/<int:group_id>/add-member/', views.add_member_to_group, name='add_member_to_group'),
    path('groups/<int:group_id>/remove-member/<int:user_id>/', views.remove_member_from_group, name='remove_member_from_group'),
    path('groups/<int:group_id>/assign-task/', views.assign_task_to_group, name='assign_task_to_group'),
    path('api/assigned-tasks/delete/<int:task_id>/', views.delete_assigned_task, name='delete_assigned_task'),
]
