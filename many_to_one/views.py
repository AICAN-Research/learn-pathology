import json

from django.contrib import messages
from django.db import transaction
from django.forms import inlineformset_factory
from django.shortcuts import render, redirect, get_object_or_404

from task.common import process_new_task_request, process_edit_task_request, \
    setup_common_new_task_context, setup_common_edit_task_context
from slide.views import slide_cache
from task.models import Task
from task.forms import TaskForm
from many_to_one.models import ManyToOne, TableColumn, TableRow
from many_to_one.forms import ManyToOneForm, TableColumnForm
from course.models import Course
from user.decorators import teacher_required


def do(request, task_id, course_id=None):
    """
    Student form for answering/viewing a many-to-one sorting task

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

    # ======== Many-to-one specific ========
    many_to_one = context['task'].manytoone

    mode = 'get'
    indices = [1, 2, 3]
    answer_order = []
    if request.method == 'POST':
        # Process form
        indices = {k: v for k, v in request.POST.items() if 'indices-sortable-list-' in k}
        for column_string, index_string in indices.items():
            answer_list = []
            column_id = column_string.split('-')[-1]
            if column_id != 'all':
                column = TableColumn.objects.get(id=column_id)
            else:
                column = None
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

    context['many_to_one'] = many_to_one
    context['answer_order'] = json.dumps(answer_order)
    context['mode'] = mode
    context['indices'] = json.dumps(indices)
    return render(request, 'many_to_one/do.html', context)


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
    slide = slide_cache.load_slide_to_cache(slide_id)

    if request.method == 'POST':

        task_form = TaskForm(request.POST)
        many_to_one_form = ManyToOneForm(request.POST)
        column_formset = TableColumnFormSet(request.POST or None, prefix='column')

        with transaction.atomic():  # Make save operation atomic
            if many_to_one_form.is_valid() and task_form.is_valid() and column_formset.is_valid():

                task = process_new_task_request(request, slide_id, course_id)

                many_to_one_task = many_to_one_form.save(commit=False)
                many_to_one_task.task = task
                many_to_one_task.save()

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

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                if course_id is not None and course_id in Course.objects.values_list('id', flat=True):
                    return redirect('course:view', course_id=course_id, active_tab='tasks')
                return redirect('task:list')

    else:
        many_to_one_form = ManyToOneForm()
        column_formset = TableColumnFormSet(instance=ManyToOne(), prefix='column')
        task_form = TaskForm()

    return render(request, 'many_to_one/new.html', {
        'manyToOneForm': many_to_one_form,
        'column_formset': column_formset,
        'slide': slide,
        'taskForm': task_form,
    })


@teacher_required
def edit(request, task_id, course_id=None):
    """
    Teacher form for editing a many-to-one sorting task
    """

    context = setup_common_edit_task_context(task_id, course_id)

    many_to_one = get_object_or_404(ManyToOne, task=context['task'])
    column = TableColumn.objects.filter(task=many_to_one)

    # Process forms
    if request.method == 'POST':  # Form was submitted

        task_form = TaskForm(request.POST or None, instance=context['task'])
        many_to_one_form = ManyToOneForm(request.POST or None, instance=many_to_one)
        column_formset = TableColumnFormSet(request.POST or None)

        with transaction.atomic():  # Make save operation atomic
            if task_form.is_valid() and many_to_one_form.is_valid():

                # Save instance data to database
                task = task_form.save()
                process_edit_task_request(request, task, task_form)
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
        many_to_one_form = ManyToOneForm(instance=context['task'].manytoone)
        column_formset = TableColumnFormSet(instance=many_to_one)

        context['taskForm'] = task_form
        context['manyToOneForm'] = many_to_one_form
        context['column_formset'] = column_formset

    return render(request, 'many_to_one/edit.html', context)
