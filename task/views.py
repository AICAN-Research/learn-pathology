from django.shortcuts import render

from task.models import Task


def list(request):
    """
    Show list of tasks
    """
    return render(request, "task/list.html", {'tasks': Task.objects.all()})