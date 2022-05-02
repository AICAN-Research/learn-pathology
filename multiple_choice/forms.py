from django.forms import ModelForm, ModelMultipleChoiceField
from multiple_choice.models import Choice, MultipleChoice
from task.models import Task
from tag.models import Tag


class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'pathology', 'organ_tags', 'stain_tags', 'other_tags']

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


class ChoiceForm(ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'correct']
        labels = {
            'text': ('Choice text'),
            'correct': ('Correct?'),
        }


class MultipleChoiceForm(ModelForm):
    class Meta:
        model = MultipleChoice
        fields = ['question', 'instructions']
