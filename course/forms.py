from django import forms
from django.forms import FileField, FileInput
from course.models import Course, CourseMaterial
from user.models import User


class CourseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['teacher'].queryset = User.objects.filter(is_teacher=True).order_by('username')

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
            'title': forms.Textarea(attrs={'rows': 1, 'cols': 100}),
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


class CourseMaterialForm(forms.ModelForm):

    file = FileField()
    class Meta:
        model = CourseMaterial
        fields = ['name', 'description', 'file']
        exclude = ['course', 'path']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'cols': 40}),
            'file': FileInput(),
        }

    def save(self, file_path='', **kwargs):
        # Update the created CourseMaterial object with the location of the uploaded file
        self.instance.path = file_path
        return super().save(**kwargs)
