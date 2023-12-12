from django import template
from task.models import Task

register = template.Library()

@register.filter
def get_task_type_for_header(task):
    if isinstance(task, Task):
        task_type = task.type
        task_type = task_type.split('_')
        s = task_type[0].capitalize()
        if len(task_type) > 1:
            for word in task_type[1:]:
                s += ' ' + word
        return s + ': '
    else:
        return ''
