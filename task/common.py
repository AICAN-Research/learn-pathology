import html

from task.forms import TaskForm
from task.models import Task
from slide.models import Slide, AnnotatedSlide, Annotation
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


def process_new_task_request(request, slide_id, course_id=None):

    # Get slide
    slide = Slide.objects.get(pk=slide_id)

    # Create annotated slide
    annotated_slide = AnnotatedSlide(slide=slide)
    annotated_slide.save()

    # Create task
    task_form = TaskForm(request.POST)
    task = task_form.save(commit=False)
    task.annotated_slide = annotated_slide
    task.save()

    organ_tags = task_form.cleaned_data['organ_tags']
    other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
    task.tags.set([organ_tags] + other_tags)

    for key in request.POST:
        if key.startswith('annotation-'):
            annotation_string = html.unescape(request.POST.get(key))
            annotation = Annotation(annotated_slide=annotated_slide,
                                    json_string=annotation_string)
            annotation.save()

    if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
        course = Course.objects.get(id=course_id)
        course.task.add(task)

    return task
