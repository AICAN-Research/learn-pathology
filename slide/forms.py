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
        queryset=Tag.objects.filter(is_organ=True).order_by('name'),
        required=True,
        label='Organ System',
    )
    stain_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_stain=True).order_by('name'),
        required=True,
        label='Stain',
    )
    other_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_organ=False, is_stain=False).order_by('name'),
        required=False,
        blank=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            # Initial must have list of id, not a query sets
            self.fields['organ_tags'].initial = [x.pk for x in self.instance.tags.filter(is_organ=True)]
            self.fields['stain_tags'].initial = [x.pk for x in self.instance.tags.filter(is_stain=True)]
            self.fields['other_tags'].initial = [x.pk for x in self.instance.tags.filter(is_organ=False, is_stain=False)]
