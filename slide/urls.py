from django.urls import path, include
from django.contrib.auth import views as auth_views
from slide import views

app_name = 'slide'
urlpatterns = [
    path('list/', views.index, name='list'),
    path('view/<int:slide_id>/', views.whole_slide_view_full, name='view_full'),
]
