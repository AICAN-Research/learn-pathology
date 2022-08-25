from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views
import os
from learnpathology import settings
from slide import views

app_name = 'slide'
urlpatterns = [
    path('list/', views.index, name='list'),
    path('browser/', views.image_browser, name='browser'),
    path('view/<int:slide_id>/', views.whole_slide_view_full, name='view_full'),
    path('add/', views.add, name='add'),
] + static('thumbnails/', document_root=os.path.join(settings.BASE_DIR, 'thumbnails'))

