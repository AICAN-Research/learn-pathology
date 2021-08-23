from django.db import models
from django.core.exceptions import FieldDoesNotExist
from django.apps import apps
from django.conf import settings


class Task(models.Model):
    """
    A generic base model for tasks, exercise etc.
    """
    name = models.CharField(max_length=256)

    @property
    def type(self):
        for app in apps.get_app_configs():
            print(app.name)
            models = app.get_models()
            for model in models:
                print(model)
                try:
                    if model._meta.get_field('task'):
                        print('has task')
                        try:
                            if model.objects.filter(task=self).exists():
                                print('exists')
                                return app.name
                        except:
                            print('err')
                            pass
                except FieldDoesNotExist:
                    pass

    @property
    def do_url(self):
        return self.type + ':do'

