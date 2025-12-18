import json
import copy

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from task.common import process_new_task_request, process_edit_task_request, \
    setup_common_new_task_context, setup_common_edit_task_context
from slide.views import slide_cache
from task.forms import TaskForm
from annotation_task.forms import AnnotationTaskForm
from annotation_task.models import AnnotationTask
from course.models import Course
from user.decorators import teacher_required, creator_required


def do(request, task_id, course_id=None, slide_id=None):
    """
    Student form for answering/viewing an annotation task

    """

    context = setup_common_new_task_context(task_id, slide_id, course_id)
    slide_cache.load_slide_to_cache(context['slide'].id)

    # ======== Annotation task specific ========
    annotation_task = context['task'].annotationtask
    context['annotations_correct'] = copy.deepcopy(context['annotations'])

    for i, annotation in enumerate(context['annotations']):
        annotation['body'][0]['value'] = chr(65 + i)

    mode = 'get'
    id_order = []
    answer_order = []
    if request.method == 'POST':
        # Process form
        id_order = request.POST.get('item_ids', None).split(',')
        id_order = [int(x) for x in id_order]
        for i, item in enumerate(id_order):
            if item == i + 1:
                answer_order.append(True)
            else:
                answer_order.append(False)

        mode = 'post'

    context['annotation_task'] = annotation_task
    context['answer_order'] = json.dumps(answer_order)
    context['mode'] = mode
    context['id_order'] = json.dumps(id_order)
    return render(request, 'annotation_task/do.html', context)


@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a click question
    """

    # Get slide
    slide = slide_cache.load_slide_to_cache(slide_id)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        task_form = TaskForm(request.POST)
        annotation_task_form = AnnotationTaskForm(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if annotation_task_form.is_valid() and task_form.is_valid():

                task = process_new_task_request(request, slide_id, course_id)

                # Create click question
                annotation_task = annotation_task_form.save(commit=False)
                annotation_task.task = task
                annotation_task.save()

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')
                return redirect('task:list')
    else:
        task_form = TaskForm()
        annotation_task_form = AnnotationTaskForm()

    return render(request, 'annotation_task/new.html', {
        'slide': slide,
        'taskForm': task_form,
        'annotationTaskForm': annotation_task_form,
        'annotationTask' : True,



    })


@creator_required
@teacher_required
def edit(request, task_id, course_id=None):
    """
    Teacher form for editing a annotation task
    """

    context = setup_common_edit_task_context(task_id, course_id)
    annotation_task = get_object_or_404(AnnotationTask, task_id=task_id)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        task_form = TaskForm(request.POST or None, instance=context['task'])
        annotation_task_form = AnnotationTaskForm(request.POST or None, instance=annotation_task)

        with transaction.atomic():  # Make save operation atomic
            if  task_form.is_valid() and annotation_task_form.is_valid():

                # Save instance data to database
                task = task_form.save()
                process_edit_task_request(request, task, task_form)
                annotation_task = annotation_task_form.save()

                messages.add_message(request, messages.SUCCESS,
                                     f'The task {task.name} was altered!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')

        return redirect('task:list')

    else:  # GET
        task_form = TaskForm(instance=context['task'],
                             initial={'organ_tags': context['task'].tags.get(is_organ=True),
                                      'other_tags': context['task'].tags.filter(is_stain=False, is_organ=False)},
                             )
        annotation_task_form = AnnotationTaskForm(instance=context['task'].annotationtask)

        context['taskForm'] = task_form
        context['annotationTaskForm'] = annotation_task_form

    return render(request, 'annotation_task/new.html', context)
