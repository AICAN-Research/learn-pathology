import os
from django.core.exceptions import ValidationError
from django.db.models import TextField
from django.forms import ModelForm, ModelMultipleChoiceField, FileInput, \
    FileField, TextInput, Textarea
from slide.models import Slide
from tag.models import Tag


class SlideForm(ModelForm):
    image_file = FileField()
    class Meta:
        model = Slide
        fields = ['name', 'description', 'image_file', 'pathology', 'organ_tags', 'stain_tags', 'other_tags']
        exclude = ['path']
        widgets = {
            'image_file': FileInput(),
        }

    organ_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_organ=True),
        required=False,
        blank=True,
    )
    stain_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_stain=True),
        required=False,
        blank=True,
    )
    other_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_organ=False, is_stain=False),
        required=False,
        blank=True,
    )

    def clean_path(self):
        data = self.cleaned_data['path']
        if not os.path.exists(data):
            raise ValidationError("Path does not point to a file")

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data

    def save(self, file_path='', **kwargs):
        # Update the created Slide object with the location of the uploaded file
        self.instance.path = file_path
        return super().save(**kwargs)


class SlideDescriptionForm(ModelForm):
    class Meta:
        model = Slide
        fields = ['description', 'long_description']
        exclude = ['name', 'path', 'image_file', 'pathology', 'organ_tags', 'stain_tags', 'other_tags']
        widgets = {
            'name': Textarea(attrs={'cols': '40', 'rows': '1', 'style': 'resize:none'}),
            'description': Textarea(attrs={'cols': '40', 'rows': '1', 'style': 'resize:none'}),
            'long_description': Textarea(attrs={'cols': '40', 'rows': '10'}),
        }
