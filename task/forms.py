from django.forms import ModelForm,  Textarea, ModelMultipleChoiceField, ModelChoiceField
from task.models import Task
from tag.models import Tag


class TaskForm(ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'pathology', 'organ_tags', 'other_tags']
        labels = {
            'name': 'Question name',
            'pathology': 'Is the question about histology or pathology?',
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



