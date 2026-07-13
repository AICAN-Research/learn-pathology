from django.db import models
from django.core.files.storage import storages

def resources_storage():
    return storages["resources"]


class Tutorial(models.Model):
    title = models.CharField(max_length=255)
    pdf = models.FileField(storage=resources_storage)

    def __str__(self):
        return self.title
