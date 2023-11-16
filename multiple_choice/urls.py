from django.urls import path, include
from django.contrib.auth import views as auth_views
from multiple_choice import views

app_name = 'multiple_choice'
urlpatterns = [
    path('do/<int:task_id>/<int:course_id>', views.do, name='do'),
    path('new/<int:slide_id>/', views.new, name='new'),
    path('new/<int:slide_id>/<int:course_id>', views.new, name='new'),
    path('edit/<int:task_id>/', views.edit, name='edit'),
    path('edit/<int:task_id>/<int:course_id>', views.edit, name='edit'),
    path('do_random/', views.do_random, name='do_random'),
    path('do_random/<int:slide_id>', views.do_random, name='do_random'),
]
