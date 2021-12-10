from django import forms
from multiple_choice.models import Choice, MultipleChoice
from task.models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name']


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'correct']
        labels = {
            'text': ('Choice text'),
            'correct': ('Correct?'),
        }


class MultipleChoiceForm(forms.ModelForm):
    class Meta:
        model = MultipleChoice
        fields = ['question', 'instructions']
