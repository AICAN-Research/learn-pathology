from django.urls import path, include
from course import views

app_name = 'course'
urlpatterns = [
    path('index/', views.index, name='index'),
    path('new/', views.new, name='new'),
    path('edit/<int:course_id>', views.edit, name='edit'),
    path('delete/<int:course_id>', views.delete, name='delete'),
    path('view/<int:course_id>', views.course_page, name='view'),
    path('slide_selection/<int:course_id>', views.slide_selection, name='slide_selection'),
    path('task_selection/<int:course_id>', views.task_selection, name='task_selection'),
    path('add_item/', views.add_to_course, name='add_item'),
    path('remove_item/', views.remove_from_course, name='remove_item'),
]
