from django.forms import ModelForm, Textarea
from annotation_task.models import  AnnotationTask




class AnnotationTaskForm(ModelForm):
    class Meta:
        model = AnnotationTask
        fields = ['question', 'instructions', ]
        labels = {
            'question': 'Question',
            'instructions': 'Instructions',

        }
        widgets = {
            'question': Textarea(attrs={'rows': 1, 'cols': 70, 'resize': 'none'}),
            'instructions': Textarea(attrs={'rows': 2, 'cols': 70}),

        }
