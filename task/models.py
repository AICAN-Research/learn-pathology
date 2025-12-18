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
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)

    @property
    def type(self):
        for app in apps.get_app_configs():
            if app.label == 'user': continue
            models = app.get_models()
            for model in models:
                if str(model).find('AnnotatedSlide') >= 0: continue
                try:
                    task_field = model._meta.get_field('task')
                    if task_field.remote_field.model.__name__ == 'Task':
                        try:
                            if model.objects.filter(task=self).exists():
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
            if app.label == 'user': continue
            models = app.get_models()
            for model in models:
                try:
                    task_field = model._meta.get_field('task')
                    if task_field.remote_field.model.__name__ == 'Task':
                        try:
                            if model.objects.filter(task=self).exists():
                                return model.objects.get(task=self)
                        except:
                            # print('err')
                            pass
                except FieldDoesNotExist:
                    pass
        raise RuntimeError('Task type not found!')

