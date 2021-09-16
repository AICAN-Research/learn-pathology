from django.urls import path, include
from course import views

app_name = 'course'
urlpatterns = [
    path('index/', views.index, name='index'),
    path('new/', views.new, name='new'),
]
