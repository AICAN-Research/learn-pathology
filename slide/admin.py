from django.contrib import admin
from django.contrib.admin import register
from .models import Slide

# Register your models here.
@register(Slide)
class SlideAdmin(admin.ModelAdmin):
    pass
