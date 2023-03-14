from django.db import models
from slide.models import Slide, AnnotatedSlide
from task.models import Task


class ManyToOne(models.Model):
    """
    A many-to-one sorting task
    """
    task = models.OneToOneField(Task, on_delete=models.CASCADE)
    question = models.CharField(max_length=2048)
    instructions = models.CharField(max_length=2048, default='Sort the elements into the correct column.')


class TableColumn(models.Model):
    """
    A column in a many-to-one sorting task
    """
    task = models.ForeignKey(ManyToOne, on_delete=models.CASCADE)
    caption = models.CharField(max_length=512)


class TableRow(models.Model):
    """
    One row entry in a many-to-one sorting task
    """
    column = models.ForeignKey(TableColumn, on_delete=models.CASCADE)
    answer = models.CharField(max_length=512)




