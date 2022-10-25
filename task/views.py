from django.contrib import messages
from django.shortcuts import render, redirect
from task.models import Task
from tag.models import Tag
from user.decorators import teacher_required


def list(request):
    """
    Show list of tasks
    """

    tasks = Task.objects.all()

    # Filters
    organs = request.GET.getlist('organ[]')
    if len(organs) > 0:
        tasks = tasks.filter(tags__in=organs)
    stains = request.GET.getlist('stain[]')
    if len(stains) > 0:
        tasks = tasks.filter(tags__in=stains)
    tags = request.GET.getlist('tag[]')
    if len(tags) > 0:
        tasks = tasks.filter(tags__in=tags)

    selected_pathology = request.GET.get('pathology', False)
    selected_histology = request.GET.get('histology', False)
    if not selected_pathology and not selected_histology:
        selected_pathology = True
        selected_histology = True
    if selected_pathology and not selected_histology:
        tasks = tasks.filter(pathology=True)
    elif not selected_pathology and selected_histology:
        tasks = tasks.filter(pathology=False)

    return render(request, "task/list.html", {
        'tasks': tasks.order_by('-id'),
        'organ_tags': Tag.objects.filter(is_organ=True),
        'stain_tags': Tag.objects.filter(is_stain=True),
        'other_tags': Tag.objects.filter(is_stain=False, is_organ=False),
        'selected_organ_tags': organs,
        'selected_stain_tags': stains,
        'selected_other_tags': tags,
        'selected_pathology': selected_pathology,
        'selected_histology': selected_histology,
    })


@teacher_required
def delete(request, task_id):
    task = Task.objects.get(pk=task_id)
    task.type_model.delete()
    task.delete()
    messages.add_message(request, messages.SUCCESS, 'Task deleted.')
    return redirect(list)
