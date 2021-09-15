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