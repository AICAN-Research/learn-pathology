from django import forms
from django.db import models
from slide.models import Slide, AnnotatedSlide
from task.models import Task


class MultipleChoice(models.Model):
    """
    A multiple choice exercise task
    """
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    question = models.CharField(max_length=2048)
    annotated_slide = models.ForeignKey(AnnotatedSlide, on_delete=models.CASCADE) # TODO Move to Task?


class Choice(models.Model):
    """
    A choice in a multiple choice task
    """
    task = models.ForeignKey(MultipleChoice, on_delete=models.CASCADE)
    text = models.CharField(max_length=512)
    correct = models.BooleanField()


# Forms

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
    annotated_slide = forms.ModelChoiceField(queryset=AnnotatedSlide.objects.all())
    class Meta:
        model = MultipleChoice
        fields = ['question', 'annotated_slide']
