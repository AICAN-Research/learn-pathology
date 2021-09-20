from django.db import models
from django.forms import ModelForm


class Tag(models.Model):
    name = models.CharField(max_length=255)
    is_organ = models.BooleanField(help_text='Is this an organ tag?')
    is_system = models.BooleanField(help_text='Is this a system tag?')

    def __str__(self):
        return self.name


class TagForm(ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'is_organ', 'is_system']