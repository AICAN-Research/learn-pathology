import os
from django.core.exceptions import ValidationError
from django.forms import ModelForm,  ModelMultipleChoiceField
from slide.models import Slide
from tag.models import Tag


class SlideForm(ModelForm):
    class Meta:
        model = Slide
        fields = ['name', 'description', 'path', 'pathology', 'organ_tags', 'system_tags', 'other_tags']

    organ_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_organ=True),
        required=False,
        blank=True,
    )
    system_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_system=True),
        required=False,
        blank=True,
    )
    other_tags = ModelMultipleChoiceField(
        queryset=Tag.objects.filter(is_organ=False, is_system=False),
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
