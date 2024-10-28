from django.forms import ModelForm, Textarea
from annotation_task.models import  AnnotationTask


class AnnotationTaskForm(ModelForm):
    class Meta:
        model = AnnotationTask
        fields = []
