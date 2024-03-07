import json

from django.db import transaction
from django.contrib import messages
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render

from task.forms import TaskForm
from course.models import Course
from user.decorators import teacher_required
from sorting.models import SortingTask, Pair
from sorting.forms import SortingTaskForm, PairForm
from slide.views import slide_cache
from task.common import process_new_task_request, process_edit_task_request, \
    setup_common_new_task_context, setup_common_edit_task_context


def do(request, task_id, course_id=None):
    """
    Student form for answering/viewing a sorting task

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

    # ======== Sorting specific ========
    sorting = context['task'].sortingtask

    mode = 'get'
    id_order = []
    is_correct_order = []
    if request.method == 'POST':
        # Get and check answers
        id_order = request.POST.get('item_ids', None).split(',')
        id_order = list(map(int, id_order))
        is_correct_order = [True if item == i + 1 else False for i, item in enumerate(id_order)]

        mode = 'post'

    context['sorting'] = sorting
    context['is_correct_order'] = json.dumps(is_correct_order)
    context['mode'] = mode
    context['id_order'] = json.dumps(id_order)
    return render(request, 'sorting/do.html', context)


@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a sorting task

    Parameters
    ----------
    request : Http request

    slide_id : int
        ID of Slide instance
    course_id : int
        ID of Course instance
    """

    # Get slide
    slide = slide_cache.load_slide_to_cache(slide_id=slide_id)

    PairFormSet = modelformset_factory(Pair, form=PairForm, extra=5)

    if request.method == 'POST':
        task_form = TaskForm(request.POST)
        sorting_task_form = SortingTaskForm(request.POST)
        pair_formset = PairFormSet(request.POST,
                                   initial=[{'fixed': chr(97 + x)} for x in range(PairFormSet.extra)])

        with transaction.atomic():
            if task_form.is_valid() and sorting_task_form.is_valid() and pair_formset.is_valid():
                task = process_new_task_request(request, slide_id, course_id)

                # Create sorting task
                sorting_task = sorting_task_form.save(commit=False)
                sorting_task.task = task
                sorting_task.save()

                # Create sorting pairs
                for pair_form in pair_formset:
                    if pair_form.has_changed():
                        pair = pair_form.save(commit=False)
                        pair.sorting_task = sorting_task
                        pair.save()

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')

                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect("course:view", course_id=course_id, active_tab='tasks')

                return redirect("task:list")

    else:
        task_form = TaskForm()
        sorting_task_form = SortingTaskForm()
        pair_formset = PairFormSet(queryset=Pair.objects.none(),
                                   initial=[{'fixed': chr(97 + x)} for x in range(PairFormSet.extra)])

    return render(request, 'sorting/new.html', {
        'slide': slide,
        'task_form': task_form,
        'sorting_task_form': sorting_task_form,
        'pair_formset': pair_formset
    })


@teacher_required
def edit(request, task_id, course_id=None):
    """
    Teacher form for editing a sorting task

    Parameters
    ----------
    request : Http request

    task_id : int
        ID of Task instance
    course_id : int
        ID of Course instance
    """
    context = setup_common_edit_task_context(task_id, course_id)

    sorting_task = get_object_or_404(SortingTask, task=context['task'])
    sorting_pair = Pair.objects.filter(sorting_task=sorting_task)
    PairFormSet = modelformset_factory(Pair, form=PairForm, extra=5)

    # Process forms
    if request.method == "POST":
        task_form = TaskForm(request.POST, instance=context['task'])
        sorting_task_form = SortingTaskForm(request.POST, instance=sorting_task)
        pair_formset = PairFormSet(request.POST,
                                   queryset=sorting_pair,
                                   initial=[{'fixed': chr(97 + sorting_pair.count() + x)} for x in
                                            range(PairFormSet.extra)])

        with transaction.atomic():
            if task_form.is_valid() and sorting_task_form.is_valid():
                task = task_form.save()
                process_edit_task_request(request, task, task_form)
                sorting_task_form.save()

                for pair_form in pair_formset:
                    if pair_form.has_changed():
                        if pair_form.is_valid():
                            pair = pair_form.save(commit=False)
                            pair.sorting_task = sorting_task
                            pair.save()
                        else:
                            pair_form.cleaned_data['id'].delete()

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS,
                                     f'The task {task.name} was altered!')

                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect("course:view", course_id=course_id, active_tab='tasks')

        return redirect('task:list')

    else:
        task_form = TaskForm(instance=context['task'],
                             initial={'organ_tags': context['task'].tags.get(is_organ=True),
                                      'other_tags': context['task'].tags.filter(is_stain=False, is_organ=False)},
                             )
        sorting_task_form = SortingTaskForm(instance=sorting_task)
        pair_formset = PairFormSet(queryset=sorting_pair,
                                   initial=[{'fixed': chr(97 + sorting_pair.count() + x)} for x in
                                            range(PairFormSet.extra)])

        context['taskForm'] = task_form
        context['sortingForm'] = sorting_task_form
        context['PairFormSet'] = pair_formset

    return render(request, 'sorting/new.html', context)


def get_pair_formset(num_extra_fields=5):
    PairFormSet = modelformset_factory(Pair, form=PairForm, extra=num_extra_fields)
    pair_formset = PairFormSet(queryset=Pair.objects.none(),
                               initial=[{'fixed': chr(97 + x)} for x in range(PairFormSet.extra)])
    return pair_formset
