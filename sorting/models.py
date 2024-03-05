from django.db import models
from task.models import Task


class SortingTask(models.Model):
    """
    A sorting task
    """
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    question = models.CharField(max_length=2048)
    instructions = models.CharField(max_length=2048,
                                    default='Sort the elements on the right to their counterparts on the left.')


class Pair(models.Model):
    """
    A pair in a sorting task
    """
    sorting_task = models.ForeignKey(SortingTask, on_delete=models.CASCADE)
    fixed = models.CharField(max_length=512)
    draggable = models.CharField(max_length=512)
