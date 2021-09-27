from django import forms

from course.models import Course
from slide.models import Slide


class CourseForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = ['code', 'title', 'description', 'teacher']
        labels = {
            'code': 'Course code',
            'title': 'Course name',
            'description': 'Description',
            'teacher': 'Teachers'
        }


class DeleteCourseForm(forms.Form):

    confirmDelete = forms.BooleanField(label="Yes, I want to delete the course",
                                       required=False)


class SlideSelectionForm(forms.ModelForm):

    def __init__(self, course):
        super().__init__()
        self.fields['slides'].initial = [slide.id for slide in course.slide.all()]

    slides = forms.ModelMultipleChoiceField(
        queryset=Slide.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Slide
        fields = ['slides']
