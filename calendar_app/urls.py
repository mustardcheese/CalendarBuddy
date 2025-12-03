# calendar_app/urls.py
from django.urls import path
from . import views

app_name = 'calendar_app'

urlpatterns = [
    # Calendar views
    path('', views.calendar_view, name='calendar_view'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete_task'),
    path('user-page/', views.user_page, name='user_page'),
    
    # Document management URLs
    path('documents/', views.document_list, name='document_list'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/<int:document_id>/', views.document_detail, name='document_detail'),
    path('documents/<int:document_id>/delete/', views.delete_document, name='delete_document'),
    path('tasks/<int:task_id>/documents/', views.task_documents, name='task_documents'),
]