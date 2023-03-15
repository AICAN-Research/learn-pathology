from django.forms import ModelForm,  Textarea
from one_to_one.models import OneToOne, SortingPair
from task.models import Task




class OneToOneForm(ModelForm):
    class Meta:
        model = OneToOne
        fields = ['question', 'instructions']
        labels = {
            'question': 'Question',
            'instructions': 'Instructions',
        }
        widgets = {
            'question': Textarea(attrs={'rows': 1, 'cols': 70, 'resize': 'none'}),
            'instructions': Textarea(attrs={'rows': 1, 'cols': 70}),
        }



class SortingPairForm(ModelForm):
    class Meta:
        model = SortingPair

        fields = ['fixed', 'dragable']
        labels = {
            'fixed': ('Entry for fixed table'),
            'dragable': ('Entry for dragable table'),
        }
        widgets = {
            'fixed': Textarea(attrs={'rows': 1, 'cols': 67, 'resize': 'none'}),
            'dragable': Textarea(attrs={'rows': 1, 'cols': 67, 'resize': 'none'}),
        }