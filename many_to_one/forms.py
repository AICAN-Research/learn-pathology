from django.forms import ModelForm, Textarea, TextInput, inlineformset_factory
from many_to_one.models import ManyToOne, TableColumn, TableRow
from task.models import Task




class ManyToOneForm(ModelForm):
    class Meta:
        model = ManyToOne
        fields = ['question', 'instructions']
        labels = {
            'question': 'Question',
            'instructions': 'Instructions',
        }
        widgets = {
            'question': Textarea(attrs={'rows': 1, 'cols': 70, 'resize': 'none'}),
            'instructions': Textarea(attrs={'rows': 1, 'cols': 70}),
        }



class TableColumnForm(ModelForm):
    class Meta:
        model = TableColumn

        fields = ['caption']
        labels = {
            'caption': ('Caption of the column'),

        }
        widgets = {
            'caption': Textarea(attrs={'rows': 1, 'cols': 20, 'resize': 'none','placeholder':'This is a caption'} ),

        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.nested = TableRowFormSet(instance=self.instance, prefix=self.prefix)


TableRowFormSet = inlineformset_factory(TableColumn, TableRow, fields=('answer',), extra=5, max_num=5)
class TableRowForm(ModelForm):
    class Meta:
        model = TableRow

        fields = ['answer']
        labels = {
            'answer': ('Field entry'),

        }
        widgets = {
            'answer': Textarea(attrs={'rows': 1, 'cols': 20, 'resize': 'none', 'placeholder': 'Sortable field'}),

        }