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

    confirmDelete = forms.BooleanField(label="Yes, I want to delete the course",
                                       required=False)

class CourseLongDescriptionForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = ['long_description']
        labels = {
            'long_description': 'Description'
        }