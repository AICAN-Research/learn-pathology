from django.forms import ModelForm, Textarea
from click_question.models import  ClickQuestion




class ClickQuestionForm(ModelForm):
    class Meta:
        model = ClickQuestion
        fields = ['question', 'instructions', ]
        labels = {
            'question': 'Question',
            'instructions': 'Instructions',

        }
        widgets = {
            'question': Textarea(attrs={'rows': 1, 'cols': 70, 'resize': 'none'}),
            'instructions': Textarea(attrs={'rows': 1, 'cols': 70}),

        }
