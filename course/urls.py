from django.urls import path, include
from course import views

app_name = 'course'
urlpatterns = [
    path('index/', views.index, name='index'),
    path('new/', views.new, name='new'),
    path('edit/<int:course_id>', views.edit, name='edit'),
    path('edit_description/<int:course_id>', views.edit_long_description, name='edit_description'),
    path('edit_learning_outcomes/<int:course_id>', views.edit_learning_outcomes, name='edit_learning_outcomes'),
    path('delete/<int:course_id>', views.delete, name='delete'),
    path('view/<int:course_id>', views.course_page, name='view'),
    path('view/<int:course_id>/<str:active_tab>', views.course_page, name='view'),
    path('view/<int:course_id>/<int:return_task>', views.course_page, name='view'),
    path('slide_selection/<int:course_id>', views.slide_selection, name='slide_selection'),
    path('slide_selection/<int:course_id>/reset', views.reset_slide_selection, name='reset_slide_selection'),
    path('task_selection/<int:course_id>', views.task_selection, name='task_selection'),
    path('add_item/', views.add_to_course, name='add_item'),
    path('remove_item/', views.remove_from_course, name='remove_item'),
  path('<int:course_id>/upload/', views.upload_material, name='upload_material'),
]
