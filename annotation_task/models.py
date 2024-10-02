from django.db import models
from task.models import Task


class AnnotationTask(models.Model):
    """
    A annotation task
    """

    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    question = models.CharField(max_length=2048)
    instructions = models.CharField(max_length=2048, default='Match the letters to the correct labels by dragging the labels up and down. Click on the letter to find the annotation.')
