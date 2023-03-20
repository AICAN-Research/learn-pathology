import random
import json
from crispy_forms.helper import FormHelper

from django.contrib import messages
from django.db import transaction
from django.forms import formset_factory, modelformset_factory, inlineformset_factory
from django.shortcuts import render, redirect, HttpResponse, get_object_or_404

from slide.models import Slide, Pointer, AnnotatedSlide, BoundingBox
from slide.views import slide_cache, save_boundingbox_annotation, save_pointer_annotation
from task.models import Task
from task.forms import TaskForm
from many_to_one.models import ManyToOne, TableColumn, TableRow
from many_to_one.forms import ManyToOneForm, TableColumnForm, TableRowForm
from course.models import Course
from user.decorators import teacher_required


def do(request, task_id, course_id=None):
    """
    Student form for answering/viewing a many-to-one sorting task
    """

    task = ManyToOne.objects.get(task_id=task_id)
    mode = 'get'
    indices = [1, 2, 3]

    answer_order = []
    if request.method == 'POST':
        print('POST')
        # Process form

        indices = {k: v for k, v in request.POST.items() if 'indices-sortable-list-' in k}
        for column_string, index_string in indices.items():
            answer_list = []
            column_id = column_string.split('-')[-1]
            if column_id != 'all':
                column = TableColumn.objects.get(id=column_id)
            else: column = None
            item_list = index_string.split(',')
            for item_string in item_list:
                if 'blank-space' in item_string:
                    answer_list.append(None)
                    continue
                item_id = item_string.split('-')[-1]
                item = TableRow.objects.get(id=item_id)
                if not column:
                    answer_list.append(None)
                    continue
                if item.column.caption == column.caption:
                    answer_list.append(True)
                else:
                    answer_list.append(False)

            answer_order.append(answer_list)

        mode = 'post'

    slide_cache.load_slide_to_cache(task.task.annotated_slide.slide.id)
    return render(request, 'many_to_one/do.html', {
        'task': task,
        'answer_order': json.dumps(answer_order),
        'course_id': course_id,
        'mode': mode,
        'indices': json.dumps(indices),

    })


TableRowFormSet = inlineformset_factory(TableColumn, TableRow, fields=('answer',), extra=5, max_num=5)
TableColumnFormSet = inlineformset_factory(ManyToOne, TableColumn, formset=TableRowFormSet, fields=('caption',),
                                           extra=5, max_num=5)

TableColumnFormSet = inlineformset_factory(ManyToOne, TableColumn, form=TableColumnForm, formset=TableColumnFormSet,
                                           extra=5, max_num=5)


@teacher_required
def new(request, slide_id, course_id=None):
    """
    Teacher form for creating a many-to-one sorting task
    """

    # Get slide

    slide = Slide.objects.get(pk=slide_id)
    slide_cache.load_slide_to_cache(slide.id)

    if request.method == 'POST':
        task_form = TaskForm(request.POST)
        many_to_one_form = ManyToOneForm(request.POST)
        column_formset = TableColumnFormSet(request.POST or None, prefix='column')
        with transaction.atomic():  # Make save operation atomic
            if many_to_one_form.is_valid() and task_form.is_valid() and column_formset.is_valid():

                annotated_slide = AnnotatedSlide()
                annotated_slide.slide = slide
                annotated_slide.save()

                task = task_form.save(commit=False)
                task.annotated_slide = annotated_slide
                task.save()

                many_to_one_task = many_to_one_form.save(commit=False)
                many_to_one_task.task = task
                many_to_one_task.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                for column_form in column_formset:
                    column = column_form.save(commit=False)

                    if len(column.caption) > 0:
                        column.task = many_to_one_task
                        column.save()

                        for row_form in column_form.nested.forms:
                            row = row_form.save(commit=False)
                            answer = request.POST.get(f"{row_form.prefix}-answer")

                            if len(answer) > 0:
                                row.answer = answer
                                row.save()

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
                    return redirect('course:view', course_id=course_id, active_tab='tasks')
                return redirect('task:list')

    else:
        many_to_one_form = ManyToOneForm()
        column_formset = TableColumnFormSet(instance=ManyToOne(), prefix='column')
        task_form = TaskForm()

        context = {
            'manyToOneForm': many_to_one_form,
            'column_formset': column_formset,
            'slide': slide,
            'taskForm': task_form,

        }
    return render(request, 'many_to_one/new.html', context)


@teacher_required
def edit(request, task_id, course_id=None):
    """
    Teacher form for editing a many-to-one sorting task
    """

    # Get model instances from database
    task = get_object_or_404(Task, id=task_id)
    many_to_one = get_object_or_404(ManyToOne, task=task)
    column = TableColumn.objects.filter(task=many_to_one)

    # Get slide and pointers
    annotated_slide = task.annotated_slide
    slide = annotated_slide.slide
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        # Get submitted forms
        task_form = TaskForm(request.POST or None, instance=task)
        many_to_one_form = ManyToOneForm(request.POST or None, instance=many_to_one)
        column_formset = TableColumnFormSet(request.POST or None)

        # pointers = Pointer.objects.filter(annotated_slide=task.annotated_slide)

        with transaction.atomic():  # Make save operation atomic
            if task_form.is_valid() and many_to_one_form.is_valid():

                # Save instance data to database
                task = task_form.save()

                organ_tags = task_form.cleaned_data['organ_tags']
                other_tags = [tag for tag in task_form.cleaned_data['other_tags']]
                task.tags.set([organ_tags] + other_tags)

                many_to_one_task = many_to_one_form.save()

                table_columns = TableColumn.objects.filter(task=many_to_one)
                for table_column in table_columns:
                    table_column.tablerow_set.all().delete()
                table_columns.delete()

                for column_form in column_formset:
                    column = TableColumn()
                    caption = request.POST.get(f"{column_form.prefix}-caption")

                    if len(caption) > 0:
                        column.task = many_to_one_task
                        column.caption = caption
                        column.save()

                        for row_form in column_form.nested.forms:

                            row = TableRow()
                            answer = request.POST.get(f"{row_form.prefix}-answer")

                            if len(answer) > 0:
                                row.column = column
                                row.answer = answer
                                row.save()

                # Store annotations (pointers)
                # Delete old pointers first
                Pointer.objects.filter(annotated_slide=annotated_slide).delete()
                BoundingBox.objects.filter(annotated_slide=annotated_slide).delete()
                # Add all current pointers
                for key in request.POST:

                    if key.startswith('right-arrow-overlay-') and key.endswith('-text'):
                        save_pointer_annotation(request, key, annotated_slide)

                    if key.startswith('boundingbox-') and key.endswith('-text'):
                        save_boundingbox_annotation(request, key, annotated_slide)

                messages.add_message(request, messages.SUCCESS,
                                     f'The task {task.name} was altered!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')

        return redirect('task:list')

    else:  # GET
        task_form = TaskForm(instance=task)
        task_form.fields['organ_tags'].initial = task.tags.filter(is_organ=True)
        task_form.fields['other_tags'].initial = task.tags.filter(is_stain=False, is_organ=False)

        many_to_one_form = ManyToOneForm(instance=task.manytoone)
        column_formset = TableColumnFormSet(instance=many_to_one)

    context = {
        'slide': slide,
        'annotated_slide': annotated_slide,
        'manyToOneForm': many_to_one_form,
        'taskForm': task_form,
        'column_formset': column_formset,
        'pointers': Pointer.objects.filter(annotated_slide=annotated_slide),
        'boxes': BoundingBox.objects.filter(annotated_slide=annotated_slide),
    }
    return render(request, 'many_to_one/edit.html', context)
