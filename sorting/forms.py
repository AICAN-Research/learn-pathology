from django.forms import ModelForm, Textarea, TextInput
from sorting.models import SortingTask, Pair


class SortingTaskForm(ModelForm):
    class Meta:
        model = SortingTask
        fields = ['question', 'instructions']

        widgets = {'question': Textarea(attrs={'rows': 1, 'cols': 70}),
                   'instructions': Textarea(attrs={'rows': 1, 'cols': 70})}


class PairForm(ModelForm):
    class Meta:
        model = Pair
        fields = ['fixed', 'draggable']
        widgets = {'fixed': TextInput(attrs={'readonly': True})}
