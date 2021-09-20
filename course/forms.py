from django import forms

from course.models import Course


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

    confirmDelete = forms.ChoiceField(choices=((True, "Yes, delete"),
                                               (False, "No, keep course")),
                                      widget=forms.RadioSelect,
                                      label=""
                                      )
