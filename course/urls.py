from django.urls import path, include
from course import views

app_name = 'course'
urlpatterns = [
    path('index/', views.index, name='index'),
    path('new/', views.new, name='new'),
    path('edit/<int:course_id>', views.edit, name='edit'),
    path('view/<int:course_id>', views.course_page, name='view'),
]
