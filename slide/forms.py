import os
from django.core.exceptions import ValidationError
from django.db.models import TextField
from django.forms import ModelForm, ModelMultipleChoiceField, FileInput, \
    FileField, TextInput, Textarea
from slide.models import Slide
from tag.models import Tag


class SlideDescriptionForm(ModelForm):
    class Meta:
        model = Slide
        fields = ['long_description']
        exclude = ['name', 'description', 'path', 'image_file', 'pathology', 'organ_tags', 'stain_tags', 'other_tags']
        widgets = {
            'name': Textarea(attrs={'cols': '40', 'rows': '1', 'style': 'resize:none'}),
            'description': Textarea(attrs={'cols': '40', 'rows': '1', 'style': 'resize:none'}),
            'long_description': Textarea(attrs={'cols': '40', 'rows': '10'}),
        }


class SlideMetadataForm(ModelForm):
    class Meta:
        model = Slide
        fields = ['name', 'description', 'long_description', 'pathology', 'organ_tags', 'stain_tags', 'other_tags']
        widgets = {
            'description': Textarea(attrs={'cols': '40', 'rows': '1', 'style': 'resize:none'}),
            'long_description': Textarea(attrs={'cols': '40', 'rows': '10'}),
        }

    organ_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_organ=True),
        required=True,
        label='Organ System',
    )
    stain_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_stain=True),
        required=True,
        label='Stain',
    )
    other_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_organ=False, is_stain=False),
        required=False,
        blank=True,
    )
