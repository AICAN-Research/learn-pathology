from django.urls import path, include
from django.contrib.auth import views as auth_views
from multiple_choice import views

app_name = 'multiple_choice'
urlpatterns = [
    path('do/<int:task_id>/', views.do, name='do'),
    path('new/addedtask', views.added_task, name='added_task'),
    path('new/<int:slide_id>/', views.new, name='new'),
]
