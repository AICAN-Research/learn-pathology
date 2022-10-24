from django.forms import ModelForm, ModelMultipleChoiceField, Textarea, Select, SelectMultiple, ModelChoiceField
from multiple_choice.models import Choice, MultipleChoice
from task.models import Task
from tag.models import Tag


class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'pathology', 'organ_tags', 'other_tags']
        labels = {
            'name': 'Question name',
            'pathology': 'Is the question about pathology?',
        }
        widgets = {
            'name': Textarea(attrs={'rows': 1, 'cols': 70}),
        }

    organ_tags = ModelChoiceField(
        #widget=Select,
        label='Organ category (if left blank, will be set to same organ as corresponding slide)',
        queryset=Tag.objects.filter(is_organ=True),
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
        widgets = {
            'text': Textarea(attrs={'rows': 1, 'cols': 67, 'resize': 'none'}),
        }


class MultipleChoiceForm(ModelForm):
    class Meta:
        model = MultipleChoice
        fields = ['question', 'instructions']
        labels = {
            'question': 'Question',
            'instructions': 'Instructions',
        }
        widgets = {
            'question': Textarea(attrs={'rows': 1, 'cols': 70, 'resize': 'none'}),
            'instructions': Textarea(attrs={'rows': 1, 'cols': 70}),
        }
