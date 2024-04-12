from django.db import models
from task.models import Task


class OneToOne(models.Model):
    """
    A one-to-one sorting task
    """
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    question = models.CharField(max_length=2048)
    instructions = models.CharField(max_length=2048,
                                    default='Sort the elements on the right to their counterparts on the left.')


class SortingPair(models.Model):
    """
    A pair in a one-to-one sorting task
    """
    task = models.ForeignKey(OneToOne, on_delete=models.CASCADE)
    fixed = models.CharField(max_length=512)
    draggable = models.CharField(max_length=512)
