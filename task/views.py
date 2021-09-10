from django.contrib import messages
from django.shortcuts import render, redirect
from task.models import Task


def list(request):
    """
    Show list of tasks
    """
    return render(request, "task/list.html", {'tasks': Task.objects.all().order_by('-id')})


def delete(request, task_id):
    task = Task.objects.get(pk=task_id)
    task.type_model.delete()
    task.delete()
    messages.add_message(request, messages.SUCCESS, 'Task deleted.')
    return redirect(list)
