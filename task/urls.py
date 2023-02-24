from django.urls import path, include
from django.contrib.auth import views as auth_views
from task import views

app_name = 'task'
urlpatterns = [
    path('new/<int:slide_id>', views.new, name='new'),
    path('list/', views.list, name='list'),
    path('delete/<int:task_id>/', views.delete, name='task_delete')
]

