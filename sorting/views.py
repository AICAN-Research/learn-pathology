from django.db import transaction
from django.shortcuts import render, get_object_or_404, redirect
from django.forms import modelformset_factory
from django.contrib import messages

from slide.models import Slide, AnnotatedSlide, Pointer, BoundingBox
from task.forms import TaskForm
from .forms import SortingTaskForm, PairForm
from .models import SortingTask, Pair
from slide.views import slide_cache, save_pointer_annotation, save_boundingbox_annotation, delete_existing_annotations
from course.models import Course
from user.decorators import teacher_required
from task.models import Task


def do(request, task_id, course_id):
    return redirect('task:list')


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
        pair_formset = PairFormSet(request.POST, initial=[{'fixed': chr(97 + x)} for x in range(PairFormSet.extra)])

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
        'task_form': task_form,
        'sorting_task_form': sorting_task_form,
        'pair_formset': pair_formset,
        'slide': slide
    })


@teacher_required
def edit(request, task_id, course_id=None):
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
                messages.add_message(request, messages.SUCCESS,
                                     f'The task {task.name} was altered!')

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
