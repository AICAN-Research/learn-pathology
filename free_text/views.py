from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404

from common.task import setup_common_task_context, process_new_task_request
from slide.models import Slide, AnnotatedSlide, Annotation
from slide.views import slide_cache
from task.models import Task
from task.forms import TaskForm
from free_text.forms import FreeTextForm
from free_text.models import FreeText
from course.models import Course
from user.decorators import teacher_required


def do(request, task_id, course_id=None):
    """
    Student form for answering/viewing a free text task

    Parameters
    ----------
    request : Http request

    task_id : int
        ID of Task instance
    course_id : int
        ID of Course instance
    """

    context = setup_common_task_context(task_id, course_id)
    slide_cache.load_slide_to_cache(context['slide'].id)

    # ======== Free text specific ========
    free_text = context['task'].freetext

    answered = None
    student_text = None
    if request.method == 'POST':
        # Process form
        student_text = request.POST.get('studentText',None)
        if student_text:
            answered = 'yes'
        else:
            answered = 'no'

    context['free_text'] = free_text
    context['answered'] = answered
    context['student_text'] = student_text
    return render(request, 'free_text/do.html', context)


@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a free text task
    """

    # Get slide
    slide = slide_cache.load_slide_to_cache(slide_id)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        task_form = TaskForm(request.POST)
        free_text_form = FreeTextForm(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if free_text_form.is_valid() and task_form.is_valid():

                task = process_new_task_request(request, slide_id, course_id)

                # Create free text
                free_text = free_text_form.save(commit=False)
                free_text.task = task
                free_text.save()

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')
                return redirect('task:list')
    else:
        task_form = TaskForm()
        free_text_form = FreeTextForm()

    return render(request, 'free_text/new.html', {
        'slide': slide,
        'taskForm': task_form,
        'freeTextForm': free_text_form,
    })


@teacher_required
def edit(request, task_id,course_id = None):
    """
    Teacher form for editing a free text task
    """

    # Get model instances from database
    task = get_object_or_404(Task, id=task_id)
    free_text = get_object_or_404(FreeText, task_id=task_id)

    # Get slide and pointers
    annotated_slide = task.annotated_slide
    slide = annotated_slide.slide
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        # Get submitted forms
        task_form = TaskForm(request.POST or None, instance=task)
        free_text_form = FreeTextForm(request.POST or None, instance=free_text)

        # pointers = Pointer.objects.filter(annotated_slide=task.annotated_slide)

        with transaction.atomic():  # Make save operation atomic
            if free_text_form.is_valid() and task_form.is_valid():

                # Save instance data to database
                task = task_form.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                free_text = free_text_form.save()

                # Store annotations (pointers)
                # Delete old pointers first
                # Pointer.objects.filter(annotated_slide=annotated_slide).delete()
                # BoundingBox.objects.filter(annotated_slide=annotated_slide).delete()
                # Add all current pointers
                # for key in request.POST:
                #
                #     if key.startswith('right-arrow-overlay-') and key.endswith('-text'):
                #         save_pointer_annotation(request, key, annotated_slide)
                #
                #     if key.startswith('boundingbox-') and key.endswith('-text'):
                #         save_boundingbox_annotation(request, key, annotated_slide)

                messages.add_message(request, messages.SUCCESS,
                                     f'The task {task.name} was altered!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')

        return redirect('task:list')

    else:  # GET
        task_form = TaskForm(instance=task)  # , initial=task.tags.all())
        task_form.fields['organ_tags'].initial = task.tags.filter(is_organ=True)
        task_form.fields['other_tags'].initial = task.tags.filter(is_stain=False, is_organ=False)

        free_text_form = FreeTextForm(instance=task.freetext)

    context = {
        'slide': slide,
        'annotated_slide': annotated_slide,
        'taskForm': task_form,
        'freeTextForm': free_text_form,
        'task': task
        # 'pointers': Pointer.objects.filter(annotated_slide=annotated_slide),
        # 'boxes': BoundingBox.objects.filter(annotated_slide=annotated_slide),

    }

    if course_id is not None:
        context['course_id'] = course_id

    return render(request, 'free_text/new.html', context)
