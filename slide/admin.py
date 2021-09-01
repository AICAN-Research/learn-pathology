from django.contrib import admin
from django.contrib.admin import register
from .models import Slide, AnnotatedSlide, Pointer

# Register your models here.
@register(Slide)
class SlideAdmin(admin.ModelAdmin):
    pass
admin.site.register(AnnotatedSlide)
admin.site.register(Pointer)
