import random

from django.contrib import messages
from django.db import transaction
from django.forms import formset_factory, inlineformset_factory, modelformset_factory
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.utils.datastructures import MultiValueDictKeyError

from course.models import Course
from multiple_choice.models import MultipleChoice, Choice, RandomMCChoice
from slide.models import Slide, Pointer, AnnotatedSlide, BoundingBox
from slide.views import slide_cache
from user.decorators import teacher_required
from task.models import Task
from multiple_choice.forms import MultipleChoiceForm, ChoiceForm
from task.forms import TaskForm
from free_text.forms import FreeTextForm
from slide.views import save_boundingbox_annotation, save_pointer_annotation


def do(request, task_id, course_id=None):
    """
    Student form for answering/viewing a multiple choice task
    """
    task = MultipleChoice.objects.get(task=task_id)

    # get id of next task
    if course_id:
        course = Course.objects.get(id=course_id)
        all_tasks = list(Task.objects.filter(course=course).values_list('id', flat=True))

    else:
        all_tasks = list(MultipleChoice.objects.values_list('id', flat=True))
        course_id = 0

    current_index = all_tasks.index(task_id)
    try:
        next_id = all_tasks[current_index + 1]
    except IndexError:
        next_id = all_tasks[0]

    answered = []
    choice_text = []
    if request.method == 'POST':
        print('POST')
        # Process form


        id_post_choice = request.POST.getlist('choice',None)
        if id_post_choice:
            for id in id_post_choice:
                choice = Choice.objects.get(task=task, id=id)
                choice_text.append(choice.text)
                if choice.correct:
                    answered.append('correct')
                else:
                    answered.append('incorrect')
        else:
            answered.append('no')

    # determin if question is single or multiple choice
    counter_corr_answ = len(list(Choice.objects.filter(task=task, correct=True)))


    slide_cache.load_slide_to_cache(task.task.annotated_slide.slide.id)
    return render(request, 'multiple_choice/do.html', {
        'task': task,
        'answered': answered,
        'len_answered': len(answered),
        'choice_text': choice_text,
        'next_id': next_id,
        'course_id': course_id,
        'counter_corr_answ': counter_corr_answ,
    })






@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a multiple choice task
    """

    # Get slide
    slide = Slide.objects.get(pk=slide_id)
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms

    if request.method == 'POST':  # Form was submitted
        print("POST")
        task_form = TaskForm(request.POST)
        free_text_form = FreeTextForm(request.POST)


        with transaction.atomic():  # Make save operation atomic
            if free_text_form.is_valid() and task_form.is_valid():
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
                free_text = free_text_form.save(commit=False)
                free_text.task = task
                free_text.save()



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
        free_text_form = FreeTextForm()


    return render(request, 'free_text/new_free_text.html', {
        'slide': slide,
        'freeTextForm': free_text_form,
        'taskForm': task_form,
    })

@teacher_required
def new_task(request, slide_id, course_id=None):
    """
    Teacher form for creating a  task
    """

    # Get slide
    slide_id = slide_id
    slide = Slide.objects.get(pk=slide_id)
    slide_cache.load_slide_to_cache(slide.id)


    return render(request, 'multiple_choice/../task/templates/task/new.html', {
        'slide_id': slide_id,

    })




@teacher_required
def edit(request, task_id):
    """
    Teacher form for editing a multiple choice task
    """

    ChoiceFormset = modelformset_factory(Choice, form=ChoiceForm, extra=5)

    # Get model instances from database
    task = get_object_or_404(Task, id=task_id)
    multiple_choice = get_object_or_404(MultipleChoice, task=task)
    choices = Choice.objects.filter(task=multiple_choice)

    # Get slide and pointers
    annotated_slide = task.annotated_slide
    slide = annotated_slide.slide
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        # Get submitted forms
        task_form = TaskForm(request.POST or None, instance=task)
        multiple_choice_form = MultipleChoiceForm(request.POST or None, instance=multiple_choice)
        choice_formset = ChoiceFormset(request.POST)

        # pointers = Pointer.objects.filter(annotated_slide=task.annotated_slide)

        with transaction.atomic():  # Make save operation atomic
            if task_form.is_valid() and multiple_choice_form.is_valid() and choice_formset.is_valid():

                # Save instance data to database
                task = task_form.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                multiple_choice = multiple_choice_form.save()

                for choiceForm in choice_formset:
                    choice = choiceForm.save(commit=False)
                    if len(choice.text) > 0:
                        choice.task = multiple_choice
                        choice.save()

                # Store annotations (pointers)
                # Delete old pointers first
                Pointer.objects.filter(annotated_slide=annotated_slide).delete()
                BoundingBox.objects.filter(annotated_slide=annotated_slide).delete()
                # Add all current pointers
                for key in request.POST:
                    print(key, request.POST[key])
                    if key.startswith('right-arrow-overlay-') and key.endswith('-text'):
                        prefix = key[:-len('text')]
                        pointer = Pointer()
                        pointer.text = request.POST[key]
                        pointer.position_x = float(request.POST[prefix + 'x'])
                        pointer.position_y = float(request.POST[prefix + 'y'])
                        pointer.annotated_slide = annotated_slide
                        pointer.save()

                    if key.startswith('boundingbox-') and key.endswith('-text'):
                        save_boundingbox_annotation(request, key, annotated_slide)

                messages.add_message(request, messages.SUCCESS,
                                     f'The task {task.name} was altered!')

        return redirect('list')

    else:  # GET
        task_form = TaskForm(instance=task)  # , initial=task.tags.all())
        task_form.fields['organ_tags'].initial = task.tags.filter(is_organ=True)
        task_form.fields['other_tags'].initial = task.tags.filter(is_stain=False, is_organ=False)

        multiple_choice_form = MultipleChoiceForm(instance=task.multiplechoice)
        choice_formset = ChoiceFormset(queryset=choices)

    context = {
        'slide': slide,
        'annotated_slide': annotated_slide,
        'taskForm': task_form,
        'multipleChoiceForm': multiple_choice_form,
        'choiceFormset': choice_formset,
        'pointers': Pointer.objects.filter(annotated_slide=annotated_slide),
    }
    return render(request, 'multiple_choice/edit_mc.html', context)
