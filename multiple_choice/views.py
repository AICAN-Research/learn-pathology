import random

from django.contrib import messages
from django.db import transaction
from django.forms import formset_factory, modelformset_factory
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404

from slide.models import Slide, Pointer, AnnotatedSlide, BoundingBox
from slide.views import slide_cache, save_boundingbox_annotation, save_pointer_annotation
from task.models import Task
from task.forms import TaskForm
from multiple_choice.models import MultipleChoice, Choice, RandomMCChoice
from multiple_choice.forms import MultipleChoiceForm, ChoiceForm
from course.models import Course
from user.decorators import teacher_required


def do(request, task_id, course_id=None):
    """
    Student form for answering/viewing a multiple choice task

    Parameters
    ----------
    request : Http request

    task_id : int
        ID of Task instance
    course_id : int
        ID of Course instance
    """
    this_task = Task.objects.get(id=task_id)
    multiple_choice = this_task.multiplechoice

    # get id of next task
    if course_id:
        course = Course.objects.get(id=course_id)
        all_tasks = Task.objects.filter(course=course)
    else:
        all_tasks = Task.objects.all()

    # Get the task ID of the next object in the queryset
    this_task_index = list(all_tasks).index(this_task)
    if this_task_index < len(all_tasks) - 1:
        next_task_id = all_tasks[this_task_index + 1].id
    else:
        next_task_id = all_tasks[0].id

    next_task = Task.objects.get(id=next_task_id)

    answered = []
    choice_text = []
    if request.method == 'POST':
        print('POST')
        # Process form
        id_post_choice = request.POST.getlist('choice', None)
        if id_post_choice:
            for id in id_post_choice:
                choice = Choice.objects.get(task=multiple_choice, id=id)
                choice_text.append(choice.text)
                if choice.correct:
                    answered.append('correct')
                else:
                    answered.append('incorrect')
        else:
            answered.append('no')

    # Determine if question is single or multiple choice
    counter_corr_answ = len(list(Choice.objects.filter(task=multiple_choice, correct=True)))

    slide = slide_cache.load_slide_to_cache(this_task.annotated_slide.slide.id)
    return render(request, 'multiple_choice/do.html', {
        'task': this_task,
        'multiple_choice': multiple_choice,
        'slide': slide,
        'answered': answered,
        'len_answered': len(answered),
        'choice_text': choice_text,
        'course_id': course_id,
        'counter_corr_answ': counter_corr_answ,
        'next_task_id': next_task_id,
        'next_task': next_task,
    })


def do_random(request, slide_id=None):
    """
    Student form for answering/viewing a random multiple choice task
    """

    if request.method == 'GET':  # If the request is GET
        # make a random question
        slides = Slide.objects.all()
        num_images = len(slides)
        slide_id = random.randrange(1, num_images + 1)

    slide = Slide.objects.get(id=slide_id)
    slide_cache.load_slide_to_cache(slide_id)
    # Load all choices for this slide
    answers = RandomMCChoice.objects.filter(slide=slide_id)

    answered = 'no'
    choice_text = None
    if request.method == 'POST':
        print('POST')
        # Process form
        choice_id = request.POST.get('choice', None)  # returns None if no choice was made
        if choice_id is not None:
            choice = RandomMCChoice.objects.get(slide=slide, id=choice_id)
            choice_text = choice.text
            if choice.correct:
                answered = 'correct'
            else:
                answered = 'incorrect'
        else:
            answered = 'no_choice'

    return render(request, 'multiple_choice/random_quest.html', {
        'answers': answers,
        'answered': answered,
        'slide': slide,
        'choice_text': choice_text,
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
    ChoiceFormset = formset_factory(ChoiceForm, extra=5)
    if request.method == 'POST':  # Form was submitted
        print("POST")
        task_form = TaskForm(request.POST)
        multiple_choice_form = MultipleChoiceForm(request.POST)
        choice_formset = ChoiceFormset(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if multiple_choice_form.is_valid() and task_form.is_valid() and choice_formset.is_valid():
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
                multiple_choice = multiple_choice_form.save(commit=False)
                multiple_choice.task = task
                multiple_choice.save()

                for choiceForm in choice_formset:
                    choice = choiceForm.save(commit=False)
                    if len(choice.text) > 0:
                        choice.task = multiple_choice
                        choice.save()

                # Store annotations (pointers)
                for key in request.POST:

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

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    course = Course.objects.get(id=course_id)
                    course.task.add(task)
                    return redirect('course:view', course_id=course_id, active_tab='tasks')
                return redirect('task:list')
    else:
        task_form = TaskForm()
        multiple_choice_form = MultipleChoiceForm()
        choice_formset = ChoiceFormset()

    return render(request, 'multiple_choice/new.html', {
        'slide': slide,
        'multipleChoiceForm': multiple_choice_form,
        'taskForm': task_form,
        'choiceFormset': choice_formset,
    })


def new_random(num_choices=5):
    """
    TODO:
      - Update docstring (this function description)
      - When re-generating random questions, remove old options first

    Teacher form for creating a multiple choice task


    Should return:
    - task
    - slide_id

    """

    # Iterate through slide_id's to generate new random questions
    for slide_id in Slide.objects.values_list('id', flat=True):
        new_choices = []

        slide = Slide.objects.get(id=slide_id)

        # Add correct answer
        choice = RandomMCChoice()
        choice.slide = slide
        choice.text = slide.description
        choice.correct = True
        new_choices.append(choice)

        # Use list comprehension to list all slide descriptions except the correct one
        incorrect_slide_descriptions = [slide.description for slide in Slide.objects.exclude(id=slide_id)]
        answers = random.sample(incorrect_slide_descriptions, k=num_choices - 1)

        for answer in answers:
            choice = RandomMCChoice()
            choice.slide = slide
            choice.text = answer
            choice.correct = False
            new_choices.append(choice)

        random.seed()
        random.shuffle(new_choices)
        for choice in new_choices:
            choice.save()


@teacher_required
def edit(request, task_id,course_id=None):
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
            if task_form.is_valid() and multiple_choice_form.is_valid():

                # Save instance data to database
                task = task_form.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                multiple_choice = multiple_choice_form.save()
                Choice.objects.filter(task=multiple_choice).delete()

                for choiceForm in choice_formset:
                    choice = Choice()
                    text = request.POST.get(f"{choiceForm.prefix}-text")
                    correct = request.POST.get(f"{choiceForm.prefix}-correct")
                    print(correct)

                    if len(text) > 0:
                        choice.task = multiple_choice
                        choice.text = text
                        if correct:
                            choice.correct = True
                        else:
                            choice.correct = False
                        choice.save()

                # Store annotations (pointers)
                # Delete old pointers first
                Pointer.objects.filter(annotated_slide=annotated_slide).delete()
                BoundingBox.objects.filter(annotated_slide=annotated_slide).delete()
                # Add all current pointers
                for key in request.POST:

                    if key.startswith('right-arrow-overlay-') and key.endswith('-text'):
                        save_pointer_annotation(request,key,annotated_slide)


                    if key.startswith('boundingbox-') and key.endswith('-text'):
                        save_boundingbox_annotation(request, key, annotated_slide)

                messages.add_message(request, messages.SUCCESS,
                                     f'The task {task.name} was altered!')

                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')

        return redirect('task:list')

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
        'boxes': BoundingBox.objects.filter(annotated_slide=annotated_slide),
    }
    return render(request, 'multiple_choice/edit.html', context)


def get_choice_formset(num_extra_fields=5):
    ChoiceFormset = formset_factory(ChoiceForm, extra=num_extra_fields)
    choice_formset = ChoiceFormset()
    return choice_formset
