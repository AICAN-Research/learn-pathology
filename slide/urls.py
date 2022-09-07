from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views
import os
from learnpathology import settings
from slide import views

app_name = 'slide'
urlpatterns = [
    path('list/', views.index, name='list'),
    path('browser/', views.grid_view, name='browser'),
    path('browser/grid-view', views.grid_view, name='grid_view'),
    path('browser/list-view', views.list_view, name='list_view'),
    path('view/<int:slide_id>/', views.whole_slide_view_full, name='view_full'),
    path('add/', views.add, name='add'),
] + static('thumbnails/', document_root=os.path.join(settings.BASE_DIR, 'thumbnails'))

