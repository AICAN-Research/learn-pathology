from django.contrib import admin
from django.contrib.admin import register
from .models import Slide, AnnotatedSlide, Annotation, SlideUpload


@register(Slide)
class SlideAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'path', 'uploaded_by', 'date_added')


@register(SlideUpload)
class SlideUploadAdmin(admin.ModelAdmin):
    list_display = ('name', 'path', 'uploaded_by', 'date_uploaded', 'finished')


admin.site.register(Annotation)
