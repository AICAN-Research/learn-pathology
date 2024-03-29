import os.path

from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField
from django.db import models
from slide.models import Slide
from task.models import Task
from user.models import User


class Course(models.Model):
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=255)
    description = models.TextField()
    long_description = RichTextUploadingField(null=True, blank=True)  # longer description
    teacher = models.ManyToManyField(User)
    task = models.ManyToManyField(Task)
    slide = models.ManyToManyField(Slide)
    # TODO add annotations later
    learning_outcomes = RichTextField(null=True, blank=True, config_name='featherweight')

    def __str__(self):
        return self.code + " - " + self.title


class CourseMaterial(models.Model):
    """
    Model to store and access course materials (pdf, docx, pptx, mp4 files...)
    """
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=1024)
    description = models.TextField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.name} ({os.path.splitext(self.path)[-1]} file)'
