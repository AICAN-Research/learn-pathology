from django.db import models
from django import forms


class Tag(models.Model):
    name = models.CharField(max_length=255)
    is_organ = models.BooleanField(help_text='Is this an organ tag?', default=False)
    is_stain = models.BooleanField(help_text='Is this a stain tag?', default=False)

    def __str__(self):
        return self.name


class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'is_organ', 'is_stain']


class DeleteTagForm(forms.Form):
    confirmDelete = forms.BooleanField(label="Yes, I want to delete the tag",
                                       required=False)

