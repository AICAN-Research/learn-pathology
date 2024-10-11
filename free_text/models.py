from django.db import models
from task.models import Task

class FreeText(models.Model):
    """
    A free text task
    """

    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    question = models.CharField(max_length=2048)
    instructions = models.CharField(max_length=2048, default='Answer the question with your own words. Use as many '
                                                             'terminology as possible.')
    answer = models.CharField(max_length=2048)


