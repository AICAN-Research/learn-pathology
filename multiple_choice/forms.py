from django.forms import ModelForm, ModelMultipleChoiceField, Textarea, Select, SelectMultiple, ModelChoiceField
from multiple_choice.models import Choice, MultipleChoice
from task.models import Task
from tag.models import Tag



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
        fields = ['question', 'instructions', 'explanation']
        labels = {
            'question': 'Question',
            'instructions': 'Instructions',
            'explanation': 'Explanation of answer'
        }
        widgets = {
            'question': Textarea(attrs={'rows': 1, 'cols': 70, 'resize': 'none'}),
            'instructions': Textarea(attrs={'rows': 1, 'cols': 70}),
            'explanation': Textarea(attrs={'rows': 10, 'cols': 70}),
        }


