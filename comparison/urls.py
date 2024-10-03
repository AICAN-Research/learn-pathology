from django.urls import path, include
from django.contrib.auth import views as auth_views
from comparison import views

app_name = 'comparison'
urlpatterns = [
    path('index', views.index, name='index'),
    path('compare', views.comparision_view, name='compare'),
    path('compare/<int:slide_1>/<int:slide_2>/', views.comparision_view, name='compare'),
    path('reset', views.reset_image_browser, name='reset'),

]
