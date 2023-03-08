from django.db import models
from task.models import Task

class ClickQuestion(models.Model):
    """
    A click task
    """

    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    question = models.CharField(max_length=2048)
    instructions = models.CharField(max_length=2048, default='Double click at the correct position on the slide.')



