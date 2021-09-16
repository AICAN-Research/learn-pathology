from django.urls import path, include
from course import views

app_name = 'course'
urlpatterns = [
    path('new/', views.new, name='new'),
]
