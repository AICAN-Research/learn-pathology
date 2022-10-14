from django import forms

from course.models import Course


class CourseForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = ['code', 'title', 'description', 'long_description', 'teacher']
        labels = {
            'code': 'Course code',
            'title': 'Course name',
            'description': 'Description (short, will be displayed in course list)',
            'long_description': 'Course description (visible on course page). You can also add this later.',
            'teacher': 'Teachers'
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 1, 'cols': 100}),
        }


class DeleteCourseForm(forms.Form):

    confirmDelete = forms.BooleanField(label="Yes, I want to delete the course",
                                       required=False)


class CourseLongDescriptionForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = ['long_description']
        labels = {
            'long_description': 'Course description (visible on course page)'
        }


class CourseLearningOutcomesForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = ['learning_outcomes']
        labels = {
            'learning_outcomes': 'Learning outcomes'
        }