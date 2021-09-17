from django import forms
from django.db import models
from slide.models import Slide
from task.models import Task
from user.models import User


class Course(models.Model):
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField()
    teacher = models.ManyToManyField(User)
    task = models.ManyToManyField(Task)
    slide = models.ManyToManyField(Slide)
    # TODO add annotations later

    def __str__(self):
        return self.code + " - " + self.title


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
