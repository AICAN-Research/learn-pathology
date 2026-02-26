from django.urls import path
from resources import views


app_name = 'resources'
urlpatterns = [
    path('download_tutorial/<int:tutorial_id>', views.download_tutorial, name='download_tutorial'),
]
