import json

from django.db import transaction
from django.contrib import messages
from django.forms import modelformset_factory
from django.shortcuts import get_object_or_404, redirect, render

from task.models import Task
from task.forms import TaskForm
from course.models import Course
from user.decorators import teacher_required
from sorting.models import SortingTask, Pair
from sorting.forms import SortingTaskForm, PairForm
from slide.models import Slide, AnnotatedSlide, Pointer, BoundingBox
from slide.views import slide_cache, save_pointer_annotation, save_boundingbox_annotation, delete_existing_annotations


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
    task = get_object_or_404(Task, id=task_id)
    sorting_task = get_object_or_404(SortingTask, task=task)

    if course_id and course_id in Course.objects.values_list('id', flat=True):
        all_tasks = Task.objects.filter(course=course_id)
    else:
        all_tasks = Task.objects.all()

    # Get the next task
    task_index = list(all_tasks).index(task)
    if task_index < len(all_tasks) - 1:
        next_task_id = all_tasks[task_index + 1].id
    else:
        next_task_id = all_tasks[0].id

    next_task = Task.objects.get(id=next_task_id)

    mode = 'get'
    id_order = []
    is_correct_order = []
    if request.method == 'POST':
        # Get and check answers
        id_order = request.POST.get('item_ids', None).split(',')
        id_order = list(map(int, id_order))
        is_correct_order = [True if item == i + 1 else False for i, item in enumerate(id_order)]

        mode = 'post'

    slide = slide_cache.load_slide_to_cache(task.annotated_slide.slide.id)

    return render(request, 'sorting/do.html', {
        'task': task,
        'sorting_task': sorting_task,
        'slide': slide,
        'id_order': json.dumps(id_order),
        'is_correct_order': json.dumps(is_correct_order),
        'mode': mode,
        'course_id': course_id,
        'next_task': next_task,
    })


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
    slide = get_object_or_404(Slide, pk=slide_id)
    slide_cache.load_slide_to_cache(slide_id=slide.id)

    PairFormSet = modelformset_factory(Pair, form=PairForm, extra=5)

    if request.method == 'POST':
        task_form = TaskForm(request.POST)
        sorting_task_form = SortingTaskForm(request.POST)
        pair_formset = PairFormSet(request.POST,
                                   initial=[{'fixed': chr(97 + x)} for x in range(PairFormSet.extra)])

        with transaction.atomic():
            if task_form.is_valid() and sorting_task_form.is_valid() and pair_formset.is_valid():
                # Create annotated slide
                annotated_slide = AnnotatedSlide(slide=slide)
                annotated_slide.save()

                # Create task
                task = task_form.save(commit=False)
                task.annotated_slide = annotated_slide
                task.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

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

                # Create annotations (pointers and bounding box)
                for key in request.POST:

                    if key.startswith('right-arrow-overlay-') and key.endswith('-text'):
                        save_pointer_annotation(request, key, annotated_slide)

                    if key.startswith('boundingbox-') and key.endswith('-text'):
                        save_boundingbox_annotation(request, key, annotated_slide)

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')

                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    course = Course.objects.get(id=course_id)
                    course.task.add(task)
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
    # Get model instances from database
    task = get_object_or_404(Task, id=task_id)
    sorting_task = get_object_or_404(SortingTask, task=task)
    sorting_pair = Pair.objects.filter(sorting_task=sorting_task)
    annotated_slide = get_object_or_404(AnnotatedSlide, task=task)

    slide_cache.load_slide_to_cache(slide_id=annotated_slide.slide_id)

    PairFormSet = modelformset_factory(Pair, form=PairForm, extra=5)

    if request.method == "POST":
        task_form = TaskForm(request.POST, instance=task)
        sorting_task_form = SortingTaskForm(request.POST, instance=sorting_task)
        pair_formset = PairFormSet(request.POST,
                                   queryset=sorting_pair,
                                   initial=[{'fixed': chr(97 + sorting_pair.count() + x)} for x in
                                            range(PairFormSet.extra)])

        with transaction.atomic():
            if task_form.is_valid() and sorting_task_form.is_valid():
                task = task_form.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                sorting_task_form.save()

                for pair_form in pair_formset:
                    if pair_form.has_changed():
                        if pair_form.is_valid():
                            pair = pair_form.save(commit=False)
                            pair.sorting_task = sorting_task
                            pair.save()
                        else:
                            pair_form.cleaned_data['id'].delete()

                # Delete all existing annotations
                delete_existing_annotations(annotated_slide)

                # Create new annotations (pointers and bounding box)
                for key in request.POST:

                    if key.startswith('right-arrow-overlay-') and key.endswith('-text'):
                        save_pointer_annotation(request, key, annotated_slide)

                    if key.startswith('boundingbox-') and key.endswith('-text'):
                        save_boundingbox_annotation(request, key, annotated_slide)

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS,f'The task {task.name} was altered!')

                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect("course:view", course_id=course_id, active_tab='tasks')

        return redirect('task:list')

    else:
        task_form = TaskForm(instance=task)
        task_form.fields['other_tags'].initial = task.tags.filter(is_organ=False, is_stain=False)
        try:
            task_form.fields['organ_tags'].initial = task.tags.get(is_organ=True)
        except:
            pass

        sorting_task_form = SortingTaskForm(instance=sorting_task)
        pair_formset = PairFormSet(queryset=sorting_pair,
                                   initial=[{'fixed': chr(97 + sorting_pair.count() + x)} for x in
                                            range(PairFormSet.extra)])

    return render(request, 'sorting/edit.html', {
        'task_form': task_form,
        'sorting_task_form': sorting_task_form,
        'pair_formset': pair_formset,
        'slide': annotated_slide.slide,
        'pointers': Pointer.objects.filter(annotated_slide=annotated_slide),
        'boxes': BoundingBox.objects.filter(annotated_slide=annotated_slide)
    })
