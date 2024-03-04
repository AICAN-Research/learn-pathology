from django.urls import path
from one_to_one import views

app_name = 'one_to_one'

urlpatterns = [
    path('do/<int:task_id>/<int:course_id>', views.do, name='do'),
    path('new/<int:slide_id>/', views.new, name='new'),
    path('new/<int:slide_id>/<int:course_id>', views.new, name='new'),
    path('edit/<int:task_id>/', views.edit, name='edit'),
    path('edit/<int:task_id>/<int:course_id>', views.edit, name='edit'),
]
