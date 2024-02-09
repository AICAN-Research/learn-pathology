import json

from django.contrib import messages
from django.db import transaction
from django.forms import formset_factory, modelformset_factory
from django.shortcuts import render, redirect, get_object_or_404

from task.common import process_new_task_request, process_edit_task_request, \
    setup_common_new_task_context, setup_common_edit_task_context
from slide.views import slide_cache
from task.models import Task
from task.forms import TaskForm
from one_to_one.models import OneToOne, SortingPair
from one_to_one.forms import OneToOneForm, SortingPairForm
from course.models import Course
from user.decorators import teacher_required


def do(request, task_id, course_id=None):
    """
    Student form for answering/viewing a one-to-one sorting task

    Parameters
    ----------
    request : Http request

    task_id : int
        ID of Task instance
    course_id : int
        ID of Course instance
    """

    context = setup_common_new_task_context(task_id, course_id)
    slide_cache.load_slide_to_cache(context['slide'].id)

    # ======== Multiple choice specific ========
    one_to_one = context['task'].onetoone

    mode = 'get'
    id_order = [1, 2, 3]
    answer_order = []
    if request.method == 'POST':
        # Process form
        id_order = request.POST.get('item_ids', None).split(',')
        id_order =[int(x) for x in id_order]
        for i, item in enumerate(id_order):
            if item == i + 1:
                answer_order.append(True)
            else:
                answer_order.append(False)

        mode = 'post'

    context['one_to_one'] = one_to_one
    context['answer_order'] = json.dumps(answer_order)
    context['mode'] = mode
    context['id_order'] = json.dumps(id_order)
    return render(request, 'one_to_one/do.html', context)


@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a one-to-one sorting task
    """

    # Get slide
    slide = slide_cache.load_slide_to_cache(slide_id)

    # Process forms
    SortingPairFormSet = formset_factory(SortingPairForm, extra=5)
    if request.method == 'POST':  # Form was submitted

        task_form = TaskForm(request.POST)
        one_to_one_form = OneToOneForm(request.POST)
        sorting_pair_formset = SortingPairFormSet(request.POST)

        with transaction.atomic():
         # Make save operation atomic
            if one_to_one_form.is_valid() and task_form.is_valid() and sorting_pair_formset.is_valid():

                task = process_new_task_request(request, slide_id, course_id)

                # Create one to one sorting task
                one_to_one_task = one_to_one_form.save(commit=False)
                one_to_one_task.task = task
                one_to_one_task.save()

                for pairForm in sorting_pair_formset:
                    pair = pairForm.save(commit=False)
                    if len(pair.fixed) > 0 and len(pair.draggable) > 0:
                        pair.task = one_to_one_task
                        pair.save()

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')
                return redirect('task:list')
    else:
        task_form = TaskForm()
        one_to_one_form = OneToOneForm()
        sorting_pair_formset = SortingPairFormSet()

    return render(request, 'one_to_one/new.html', {
        'slide': slide,
        'taskForm': task_form,
        'oneToOneForm': one_to_one_form,
        'sortingPairFormSet': sorting_pair_formset,
    })


@teacher_required
def edit(request, task_id,course_id=None):
    """
    Teacher form for editing a one-to-one sorting task
    """

    context = setup_common_edit_task_context(task_id, course_id)

    SortingPairFormSet = modelformset_factory(SortingPair, form=SortingPairForm, extra=5)
    one_to_one = get_object_or_404(OneToOne, task=context['task'])
    sorting_pair = SortingPair.objects.filter(task=one_to_one)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        task_form = TaskForm(request.POST or None, instance=context['task'])
        one_to_one_form = OneToOneForm(request.POST or None, instance=one_to_one)
        sorting_pair_formset = SortingPairFormSet(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if task_form.is_valid() and one_to_one_form.is_valid():

                # Save instance data to database
                task = task_form.save()
                process_edit_task_request(request, task, task_form)
                one_to_one = one_to_one_form.save()
                #one_to_one.sortingpair_set.all().delete()

                for pairForm in sorting_pair_formset:
                    print(pairForm.errors)

                    if pairForm.is_valid():

                        pair = pairForm.save(commit=False)
                        print(f'{pair.fixed} is valid ')
                        if len(pair.fixed) > 0 and len(pair.draggable) > 0:
                            pair.task = one_to_one
                            pair.save()

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
        one_to_one_form = OneToOneForm(instance=context['task'].onetoone)
        sorting_pair_formset = SortingPairFormSet(queryset=sorting_pair)

        context['taskForm'] = task_form
        context['oneToOneForm'] = one_to_one_form
        context['sortingPairFormSet'] = sorting_pair_formset

    return render(request, 'one_to_one/new.html', context)


def get_sorting_pair_formset(num_extra_fields=5):
    SortingPairFormSet = formset_factory(SortingPairForm, extra=num_extra_fields)
    sorting_pair_formset = SortingPairFormSet()
    return sorting_pair_formset
