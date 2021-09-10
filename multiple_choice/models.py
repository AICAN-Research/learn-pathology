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
    annotated_slide = models.OneToOneField(AnnotatedSlide, on_delete=models.CASCADE) # TODO Move to Task?


class Choice(models.Model):
    """
    A choice in a multiple choice task
    """
    task = models.ForeignKey(MultipleChoice, on_delete=models.CASCADE)
    text = models.CharField(max_length=512)
    correct = models.BooleanField()


# Forms

class ChoiceForm(forms.ModelForm):

    text = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Alternative"}))
    correct = forms.RadioSelect()

    class Meta:
        model = Choice
        fields = ['text', 'correct']


class MultipleChoiceForm(forms.ModelForm):

    question = forms.CharField(widget=forms.TextInput())

    # Make multiple choice fields
    choiceFormset = forms.formset_factory(ChoiceForm, extra=3)

    annotated_slide = forms.ModelChoiceField(queryset=AnnotatedSlide.objects.all())

    class Meta:
        model = MultipleChoice
        fields = ['question', 'annotated_slide']
