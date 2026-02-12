import html

from django.shortcuts import get_object_or_404

from task.forms import TaskForm
from task.models import Task
from slide.models import Slide, AnnotatedSlide, Annotation
from course.models import Course


def setup_common_new_task_context(task_id, slide_id=None, course_id=None):

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
    elif slide_id:
        all_tasks = Task.objects.filter(annotated_slide__slide=slide_id)
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
    context['slide_id'] = slide_id

    return context


def setup_common_edit_task_context(task_id, course_id=None):
    task = get_object_or_404(Task, id=task_id)
    annotated_slide = task.annotated_slide
    slide = annotated_slide.slide
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
    task.created_by = request.user
    task.save()

    organ_tags = task_form.cleaned_data['organ_tags']
    if organ_tags is None:
        # If no organ tag selected, use same organ as the slide
        organ_tags = slide.tags.get(is_organ=True)
    other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
    task.tags.set([organ_tags] + other_tags)

    save_annotations(request, annotated_slide)

    if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
        course = Course.objects.get(id=course_id)
        course.task.add(task)

    return task


def process_edit_task_request(request, task, task_form):
    # Update annotations
    annotated_slide = task.annotated_slide
    delete_annotations(annotated_slide)         # Delete current annotations first
    save_annotations(request, annotated_slide)  # Add all current annotations

    # Process tags
    organ_tags = task_form.cleaned_data['organ_tags']
    if organ_tags is None:
        # If no organ tag selected, use same organ as the slide
        slide = task.annotated_slide.slide
        organ_tags = slide.tags.get(is_organ=True)
    other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
    task.tags.set([organ_tags] + other_tags)


def save_annotations(request, annotated_slide):
    """
    Saves annotations that have been added to a slide in a task.
    These annotations are added as hidden <input> fields with name="annotation-**".
    """
    for key in request.POST:
        if key.startswith('annotation-'):
            annotation_string = html.unescape(request.POST.get(key))
            annotation = Annotation(annotated_slide=annotated_slide,
                                    json_string=annotation_string)
            annotation.save()


def delete_annotations(annotated_slide):
    """ Deletes all annotations connected to the AnnotatedSlide """
    Annotation.objects.filter(annotated_slide=annotated_slide).delete()
