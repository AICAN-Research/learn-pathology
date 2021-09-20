"""learnpathology URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

import learnpathology.views
import slide.views
import task.views

urlpatterns = [
    path('', learnpathology.views.index, name='frontpage'),
    path('viewer/<int:slide_id>/', slide.views.whole_slide_viewer, name="view_wsi"),
    path('viewer/tile/<int:slide_id>/<int:osd_level>/<int:x>/<int:y>/', slide.views.tile, name="tile"),
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('multiple_choice/', include('multiple_choice.urls')),
    path('slide/', include('slide.urls')),
    path('tasks/', task.views.list, name='task_list'),
    path('task/delete/<int:task_id>/', task.views.delete, name='task_delete'),
    path('tag/', include('tag.urls')),
    path('course/', include('course.urls')),
]
