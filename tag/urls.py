from django.urls import path, include
from tag import views

app_name = 'tag'
urlpatterns = [
    path('', views.index, name='index'),
    path('new/', views.new, name='new'),
    path('edit/<int:tag_id>/', views.edit, name='edit'),
    path('delete/<int:tag_id>/', views.delete, name='delete'),
]
