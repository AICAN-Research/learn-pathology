from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A LearnPathology user"""
    is_student = models.BooleanField(default=True)
    is_teacher = models.BooleanField(default=False)
