from django.db import models


class ApprovedUser(models.Model):
    """
    List of pre approved users which can login with Feide
    """
    username = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.username
