import random
import json

from django.contrib import messages
from django.db import transaction
from django.forms import formset_factory, modelformset_factory
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404

from slide.models import Slide, Pointer, AnnotatedSlide, BoundingBox
from slide.views import slide_cache, save_boundingbox_annotation, save_pointer_annotation
from task.models import Task
from task.forms import TaskForm
from one_to_one.models import OneToOne, SortingPair
from one_to_one.forms import OneToOneForm, SortingPairForm
from course.models import Course
from user.decorators import teacher_required


def do(request, task_id, course_id=None):
    """
    Student form for answering/viewing a one-to-one sorting task
    """
    print(task_id)
    task = OneToOne.objects.get(task_id=task_id)
    mode = 'get'
    id_order = [1,2,3]

    answer_order = []
    if request.method == 'POST':
        print('POST')
        # Process form

        id_order = request.POST.get('item_ids', None).split(',')
        id_order =[int(x) for x in id_order]
        for i, item in enumerate(id_order):
            if item == i + 1:
                answer_order.append(True)
            else:
                answer_order.append(False)

        print(answer_order)
        mode = 'post'

    print(answer_order)
    slide_cache.load_slide_to_cache(task.task.annotated_slide.slide.id)
    return render(request, 'one_to_one/do.html', {
        'task': task,
        'answer_order': json.dumps(answer_order),
        'course_id': course_id,
        'mode': mode,
        'id_order': json.dumps(id_order),


    })


@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a one-to-one sorting task
    """

    # Get slide
    slide = Slide.objects.get(pk=slide_id)
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms
    SortingPairFormSet = formset_factory(SortingPairForm, extra=5)
    if request.method == 'POST':  # Form was submitted
        print("POST")
        task_form = TaskForm(request.POST)
        one_to_one_form = OneToOneForm(request.POST)
        sorting_pair_formset = SortingPairFormSet(request.POST)

        with transaction.atomic():
         # Make save operation atomic
            if one_to_one_form.is_valid() and task_form.is_valid() and sorting_pair_formset.is_valid():
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

                # Create one to one sorting task
                one_to_one_task = one_to_one_form.save(commit=False)
                one_to_one_task.task = task
                one_to_one_task.save()

                for pairForm in sorting_pair_formset:
                    pair = pairForm.save(commit=False)
                    if len(pair.fixed) > 0 and len(pair.draggable) > 0:
                        pair.task = one_to_one_task
                        pair.save()

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
        one_to_one_form = OneToOneForm()
        sorting_pair_formset = SortingPairFormSet()

    return render(request, 'one_to_one/new.html', {
        'slide': slide,
        'oneToOneForm': one_to_one_form,
        'taskForm': task_form,
        'sortingPairFormSet': sorting_pair_formset,
    })


@teacher_required
def edit(request, task_id,course_id=None):
    """
    Teacher form for editing a one-to-one sorting task
    """

    SortingPairFormSet = modelformset_factory(SortingPair, form=SortingPairForm, extra=5)

    # Get model instances from database
    task = get_object_or_404(Task, id=task_id)
    one_to_one = get_object_or_404(OneToOne, task=task)
    sorting_pair = SortingPair.objects.filter(task=one_to_one)

    # Get slide and pointers
    annotated_slide = task.annotated_slide
    slide = annotated_slide.slide
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        # Get submitted forms
        task_form = TaskForm(request.POST or None, instance=task)
        one_to_one_form = OneToOneForm(request.POST or None, instance=one_to_one)
        sorting_pair_formset = SortingPairFormSet(request.POST)

        # pointers = Pointer.objects.filter(annotated_slide=task.annotated_slide)

        with transaction.atomic():  # Make save operation atomic
            if task_form.is_valid() and one_to_one_form.is_valid() and sorting_pair_formset.is_valid():

                # Save instance data to database
                task = task_form.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                one_to_one = one_to_one_form.save()

                for pairForm in sorting_pair_formset:
                    pair = pairForm.save(commit=False)
                    if len(pair.fixed) > 0 and len(pair.draggable) > 0:
                        pair.task = one_to_one
                        pair.save()

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

        one_to_one_form = OneToOneForm(instance=task.onetoone)
        sorting_pair_formset = SortingPairFormSet(queryset=sorting_pair)

    context = {
        'slide': slide,
        'annotated_slide': annotated_slide,
        'oneToOneForm': one_to_one_form,
        'taskForm': task_form,
        'sortingPairFormSet': sorting_pair_formset,
        'pointers': Pointer.objects.filter(annotated_slide=annotated_slide),
        'boxes': BoundingBox.objects.filter(annotated_slide=annotated_slide),
    }
    return render(request, 'one_to_one/edit.html', context)
