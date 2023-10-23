from django.db import models
from task.models import Task


class SortingTask(models.Model):
    """
    A sorting task
    """
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    question = models.CharField(max_length=1000)
    instructions = models.CharField(max_length=1000)


class Pair(models.Model):
    """
    A pair in a sorting task
    """
    sorting_task = models.ForeignKey(SortingTask, on_delete=models.CASCADE)
    fixed = models.CharField(max_length=200, )
    draggable = models.CharField(max_length=200)
