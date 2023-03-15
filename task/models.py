from django.db import models
from django.core.exceptions import FieldDoesNotExist
from django.apps import apps
from django.conf import settings
from slide.models import AnnotatedSlide
from tag.models import Tag


class Task(models.Model):
    """
    A generic base model for tasks, exercise etc.
    """
    name = models.CharField(max_length=256)
    annotated_slide = models.ForeignKey(AnnotatedSlide, on_delete=models.CASCADE)
    pathology = models.BooleanField(default=False, help_text='Is the task about pathology or not (general histology)')
    tags = models.ManyToManyField(Tag)

    @property
    def type(self):
        for app in apps.get_app_configs():
            # print(app.name)
            models = app.get_models()
            for model in models:
                if str(model).find('AnnotatedSlide') >= 0: continue
                # print(model)
                try:
                    task_field = model._meta.get_field('task')
                    if task_field.remote_field.model.__name__ == 'Task':
                        # print('has task')
                        try:
                            if model.objects.filter(task=self).exists():
                                # print('exists')
                                return app.name
                        except:
                            # print('err')
                            pass
                except FieldDoesNotExist:
                    pass
        raise RuntimeError('Task type not found!')

    @property
    def do_url(self):
        return self.type + ':do'

    def edit_url(self):
        return self.type + ':edit'

    @property
    def type_model(self):
        for app in apps.get_app_configs():
            # print(app.name)
            models = app.get_models()
            for model in models:
                # print(model)
                try:
                    task_field = model._meta.get_field('task')
                    if task_field.remote_field.model.__name__ == 'Task':
                        # print('has task')
                        try:
                            if model.objects.filter(task=self).exists():
                                # print('exists')
                                return model.objects.get(task=self)
                        except:
                            # print('err')
                            pass
                except FieldDoesNotExist:
                    pass
        raise RuntimeError('Task type not found!')

