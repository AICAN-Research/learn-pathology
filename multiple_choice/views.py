import random

from django.contrib import messages
from django.db import transaction
from django.forms import formset_factory, modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404

from slide.models import AnnotatedSlide
from task.common import process_new_task_request, process_edit_task_request, \
    setup_common_new_task_context, setup_common_edit_task_context
from slide.models import Slide
from slide.views import slide_cache
from task.forms import TaskForm
from multiple_choice.models import MultipleChoice, Choice, RandomMCChoice
from multiple_choice.forms import MultipleChoiceForm, ChoiceForm
from course.models import Course
from user.decorators import teacher_required


def do(request, task_id, course_id=None, slide_id=None):
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

    context = setup_common_new_task_context(task_id, slide_id, course_id)
    slide_cache.load_slide_to_cache(context['slide'].id)

    # ======== Multiple choice specific ========
    multiple_choice = context['task'].multiplechoice

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

    context['multiple_choice'] = multiple_choice
    context['answered'] = answered
    context['len_answered'] = len(answered)
    context['choice_text'] = choice_text
    context['counter_corr_answ'] = counter_corr_answ
    return render(request, 'multiple_choice/do.html', context)


@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a multiple choice task

    Parameters
    ----------
    request : Http request

    slide_id : int
        ID of Slide instance
    course_id : int
        ID of Course instance
    """

    # Get slide
    slide = slide_cache.load_slide_to_cache(slide_id)

    # Process forms
    ChoiceFormset = formset_factory(ChoiceForm, extra=5)
    if request.method == 'POST':  # Form was submitted
        task_form = TaskForm(request.POST)
        multiple_choice_form = MultipleChoiceForm(request.POST)
        choice_formset = ChoiceFormset(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if multiple_choice_form.is_valid() and task_form.is_valid() and choice_formset.is_valid():

                task = process_new_task_request(request, slide_id, course_id)

                # Create multiple choice
                multiple_choice = multiple_choice_form.save(commit=False)
                multiple_choice.task = task
                multiple_choice.save()

                # Create choices
                for choiceForm in choice_formset:
                    choice = choiceForm.save(commit=False)
                    if len(choice.text) > 0:
                        choice.task = multiple_choice
                        choice.save()

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')
                return redirect('task:list')
    else:
        task_form = TaskForm()
        multiple_choice_form = MultipleChoiceForm()
        choice_formset = ChoiceFormset()

    return render(request, 'multiple_choice/new.html', {
        'slide': slide,
        'taskForm': task_form,
        'multipleChoiceForm': multiple_choice_form,
        'choiceFormset': choice_formset,
    })


@teacher_required
def edit(request, task_id, course_id=None):
    """
    Teacher form for editing a multiple choice task

        Parameters
    ----------
    request : Http request

    task_id : int
        ID of Task instance
    course_id : int
        ID of Course instance
    """

    context = setup_common_edit_task_context(task_id, course_id)

    ChoiceFormset = modelformset_factory(Choice, form=ChoiceForm, extra=4, max_num=4)
    multiple_choice = get_object_or_404(MultipleChoice, task=context['task'])
    choices = Choice.objects.filter(task=multiple_choice)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        task_form = TaskForm(request.POST or None, instance=context['task'])
        multiple_choice_form = MultipleChoiceForm(request.POST or None, instance=multiple_choice)
        choice_formset = ChoiceFormset(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if task_form.is_valid() and multiple_choice_form.is_valid():

                # Save instance data to database
                task = task_form.save()
                process_edit_task_request(request, task, task_form)
                multiple_choice = multiple_choice_form.save()
                Choice.objects.filter(task=multiple_choice).delete()

                for choiceForm in choice_formset:
                    choice = Choice()
                    text = request.POST.get(f"{choiceForm.prefix}-text")
                    correct = request.POST.get(f"{choiceForm.prefix}-correct")

                    if len(text) > 0:
                        choice.task = multiple_choice
                        choice.text = text
                        if correct:
                            choice.correct = True
                        else:
                            choice.correct = False
                        choice.save()

                messages.add_message(request, messages.SUCCESS,
                                     f'The task {task.name} was altered!')

                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')

        return redirect('task:list')


    else:

        task_form = TaskForm(instance=context['task'])

        task_form.fields['other_tags'].initial = context['task'].tags.filter(is_stain=False, is_organ=False)

        try:

            task_form.fields['organ_tags'].initial = context['task'].tags.get(is_organ=True)

        except:

            pass
        multiple_choice_form = MultipleChoiceForm(instance=context['task'].multiplechoice)
        choice_formset = ChoiceFormset(queryset=choices)

        context['taskForm'] = task_form
        context['multipleChoiceForm'] = multiple_choice_form
        context['choiceFormset'] = choice_formset

        slide_cache.load_slide_to_cache(context['slide'].id)
        return render(request, 'multiple_choice/new.html', context)


def get_choice_formset():
    ChoiceFormset = formset_factory(ChoiceForm, extra=4)
    choice_formset = ChoiceFormset()
    return choice_formset
