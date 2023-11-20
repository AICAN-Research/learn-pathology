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
from django.contrib.flatpages import views
from django.urls import path, include, re_path
from django.conf.urls.static import static
from django.conf import settings

import learnpathology.views
import slide.views

urlpatterns = [
    path('', learnpathology.views.index, name='frontpage'),
    path('viewer/<int:slide_id>/', slide.views.whole_slide_viewer, name="view_wsi"),
    path('viewer/tile/<int:slide_id>/<int:osd_level>/<int:x>/<int:y>/', slide.views.tile, name="tile"),
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('multiple_choice/', include('multiple_choice.urls')),
    path('slide/', include('slide.urls')),
    path('tag/', include('tag.urls')),
    path('course/', include('course.urls')),
    path('task/', include('task.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('free_text/', include('free_text.urls')),
    path('click_question/', include('click_question.urls')),
    path('one_to_one/', include('one_to_one.urls')),
    path('many_to_one/', include('many_to_one.urls')),
    path('sorting/', include('sorting.urls'))
]

urlpatterns += [
    # Define specific paths (can be used with {% url %} tag
    # path('about/', views.flatpage, {'url': '/about/'}, name='about'),
    # path('privacy/', views.flatpage, {'url': '/privacy/'}, name='privacy'),

    # Or, use this 'catchall' pattern for all flatpages
    re_path(r'^(?P<url>.*/)$', views.flatpage),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
