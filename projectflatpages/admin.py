from django.contrib import admin
from django.db import models
from django.contrib.flatpages.admin import FlatpageForm, FlatPageAdmin
from django.contrib.flatpages.models import FlatPage
from ckeditor.fields import RichTextFormField
from ckeditor_uploader.fields import RichTextUploadingField


class FlatPageAdmin(FlatPageAdmin):
    class Meta:
        model = FlatPage
        fields = '__all__'
        widgets = {
            'content': RichTextUploadingField(config_name='lightweight'),
        }


# Re-register FlatPageAdmin
admin.site.unregister(FlatPage)
admin.site.register(FlatPage, FlatPageAdmin)
