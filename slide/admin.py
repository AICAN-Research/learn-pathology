from django.contrib import admin
from django.contrib.admin import register
from .models import Slide, AnnotatedSlide, Annotation

# Register your models here.
@register(Slide)
class SlideAdmin(admin.ModelAdmin):
    pass
admin.site.register(Annotation)
