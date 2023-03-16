from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404

from slide.models import Slide, Pointer, AnnotatedSlide, BoundingBox
from slide.views import slide_cache, save_boundingbox_annotation, save_pointer_annotation
from task.models import Task
from task.forms import TaskForm
from click_question.forms import ClickQuestionForm
from click_question.models import ClickQuestion
from course.models import Course
from user.decorators import teacher_required


def do(request, task_id, course_id=None):
    """
    Student form for answering/viewing a click question
    """
    task = ClickQuestion.objects.get(task_id=task_id)

    # get id of next task
    #TODO include all task types for next task
    # if course_id:
    #     course = Course.objects.get(id=course_id)
    #     all_tasks = list(Task.objects.filter(course=course).values_list('id', flat=True))
    #
    # else:
    #     all_tasks = list(FreeText.objects.values_list('id', flat=True))
    #     course_id = 0
    #
    # current_index = all_tasks.index(task_id)
    # try:
    #     next_id = all_tasks[current_index + 1]
    # except IndexError:
    #     next_id = all_tasks[0]

    student_selection = None
    answered = None
    if request.method == 'POST':
        print('POST')
        # Process form
        student_selection = request.POST.get('studentText',None)
        if student_selection:
            answered = 'yes'
        else:
            answered = 'no'

    slide_cache.load_slide_to_cache(task.task.annotated_slide.slide.id)
    return render(request, 'click_question/do.html', {
        'task': task,
        'answered': answered,
        'course_id': course_id,
        'student_selection': student_selection,
    })


@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a click question
    """

    # Get slide
    slide = Slide.objects.get(pk=slide_id)
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms

    if request.method == 'POST':  # Form was submitted
        print("POST")
        task_form = TaskForm(request.POST)
        click_question_form = ClickQuestionForm(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if click_question_form.is_valid() and task_form.is_valid():
                # Create annotated slide
                annotated_slide = AnnotatedSlide()
                annotated_slide.slide = slide
                annotated_slide.save()

                # Create task
                task = task_form.save(commit=False)
                task.annotated_slide = annotated_slide
                task.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                # Create multiple choice
                click_question = click_question_form.save(commit=False)
                click_question.task = task
                click_question.save()

                # Store annotations (pointers)
                for key in request.POST:
                    print(key, request.POST[key])
                    if key.startswith('right-arrow-overlay-') and key.endswith('-text'):
                        save_pointer_annotation(request, key, annotated_slide)

                    if key.startswith('boundingbox-') and key.endswith('-text'):
                        save_boundingbox_annotation(request, key, annotated_slide)

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    course = Course.objects.get(id=course_id)
                    course.task.add(task)
                    return redirect('course:view', course_id=course_id)
                return redirect('task:list')
    else:
        task_form = TaskForm()
        click_question_form = ClickQuestionForm()

    return render(request, 'click_question/new.html', {
        'slide': slide,
        'clickQuestionForm': click_question_form,
        'taskForm': task_form,
    })


@teacher_required
def edit(request, task_id, course_id=None):
    """
    Teacher form for editing a click question
    """

    # Get model instances from database
    task = get_object_or_404(Task, id=task_id)
    click_question = get_object_or_404(ClickQuestion, task_id=task_id)

    # Get slide and pointers
    annotated_slide = task.annotated_slide
    slide = annotated_slide.slide
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        # Get submitted forms
        task_form = TaskForm(request.POST or None, instance=task)
        click_question_form = ClickQuestionForm(request.POST or None, instance=click_question)

        # pointers = Pointer.objects.filter(annotated_slide=task.annotated_slide)

        with transaction.atomic():  # Make save operation atomic
            if click_question_form.is_valid() and task_form.is_valid():

                # Save instance data to database
                task = task_form.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                free_text = click_question_form.save()

                # Store annotations (pointers)
                # Delete old pointers first
                Pointer.objects.filter(annotated_slide=annotated_slide).delete()
                BoundingBox.objects.filter(annotated_slide=annotated_slide).delete()
                # Add all current pointers
                for key in request.POST:
                    print(key, request.POST[key])
                    if key.startswith('right-arrow-overlay-') and key.endswith('-text'):
                        save_pointer_annotation(request, key, annotated_slide)

                    if key.startswith('boundingbox-') and key.endswith('-text'):
                        save_boundingbox_annotation(request, key, annotated_slide)

                messages.add_message(request, messages.SUCCESS,
                                     f'The task {task.name} was altered!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):

                    return redirect('course:view', course_id=course_id)

        return redirect('task:list')

    else:  # GET
        task_form = TaskForm(instance=task)  # , initial=task.tags.all())
        task_form.fields['organ_tags'].initial = task.tags.filter(is_organ=True)
        task_form.fields['other_tags'].initial = task.tags.filter(is_stain=False, is_organ=False)

        click_question_form = ClickQuestionForm(instance=task.clickquestion)

    context = {
        'slide': slide,
        'annotated_slide': annotated_slide,
        'taskForm': task_form,
        'clickQuestionForm': click_question_form,
        'pointers': Pointer.objects.filter(annotated_slide=annotated_slide),
        'boxes':  BoundingBox.objects.filter(annotated_slide=annotated_slide),

    }
    return render(request, 'click_question/edit.html', context)
