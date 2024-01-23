
from task.models import Task
from slide.models import Slide, AnnotatedSlide, Annotation
from slide.views import slide_cache
from course.models import Course


def setup_common_task_context(task_id, course_id=None):

    task = Task.objects.get(id=task_id)
    slide = task.annotated_slide.slide
    context = {
        'task': task,
        'slide': slide,
        'course_id': course_id
    }

    # Add annotations from AnnotatedSlide object
    annotations = Annotation.objects.filter(annotated_slide=task.annotated_slide)
    context['annotations'] = []
    for a in annotations:
        context['annotations'].append(a.deserialize())

    # get id of next task
    if course_id:
        course = Course.objects.get(id=course_id)
        all_tasks = Task.objects.filter(course=course)
    else:
        all_tasks = Task.objects.all()

    # Get the task ID of the next object in the queryset
    this_task_index = list(all_tasks).index(task)
    if this_task_index < len(all_tasks) - 1:
        next_task_id = all_tasks[this_task_index + 1].id
    else:
        next_task_id = all_tasks[0].id
    next_task = Task.objects.get(id=next_task_id)
    context['next_task_id'] = next_task_id
    context['next_task'] = next_task

    return context
