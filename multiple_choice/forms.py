from django.forms import ModelForm, ModelMultipleChoiceField
from multiple_choice.models import Choice, MultipleChoice
from task.models import Task
from tag.models import Tag


class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'pathology', 'organ_tags', 'system_tags', 'other_tags']

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
        fields = ['question']
