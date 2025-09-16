from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """A LearnPathology user"""
    is_student = models.BooleanField(default=True)
    is_teacher = models.BooleanField(default=False)
    is_uploader = models.BooleanField(default=False)
    need_password_reset = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True)
