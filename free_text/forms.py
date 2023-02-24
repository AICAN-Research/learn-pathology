from django.forms import ModelForm, Textarea
from free_text.models import  FreeText




class FreeTextForm(ModelForm):
    class Meta:
        model = FreeText
        fields = ['question', 'instructions', 'answer']
        labels = {
            'question': 'Question',
            'instructions': 'Instructions',
            'answer': 'Optimal answer'
        }
        widgets = {
            'question': Textarea(attrs={'rows': 1, 'cols': 70, 'resize': 'none'}),
            'instructions': Textarea(attrs={'rows': 1, 'cols': 70}),
            'answer': Textarea(attrs={'rows':10, 'col':70}),
        }
