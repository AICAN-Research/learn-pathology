from django.core.files.storage import FileSystemStorage
from django.db import models
from learnpathology import settings

class Tutorial(models.Model):
    title = models.CharField(max_length=255)
    pdf = models.FileField(storage=FileSystemStorage(location=settings.RESOURCES_DIR))

    def __str__(self):
        return self.title
