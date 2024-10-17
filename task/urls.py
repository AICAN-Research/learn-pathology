from django.urls import path, include
from django.contrib.auth import views as auth_views
from task import views

app_name = 'task'
urlpatterns = [
    path('new1/', views.new1, name='new1'),
    path('new1/<int:course_id>', views.new1, name='new1'),
    path('new2/', views.new2, name='new2'),
    path('new2/<str:course_id>', views.new2, name='new2'),
    path('new3/<int:course_id>', views.new3, name='new3'),
    path('new3/', views.new3, name='new3'),
    path('list/', views.list, name='list'),
    path('list/<int:slide_id>', views.list, name='list'),
    path('delete/<int:task_id>/', views.delete, name='task_delete'),
    path('reset', views.reset_image_browser, name='reset'),
    path('reset/<int:course_id>', views.reset_image_browser, name='reset'),
]

