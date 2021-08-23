from django.shortcuts import render
from multiple_choice.models import MultipleChoice
from slide.models import Slide
from slide.views import slide_cache


def do(request, task_id):
    task = MultipleChoice.objects.get(task=task_id)
    slide_cache.load_slide_to_cache(task.slide.id)
    return render(request, 'multiple_choice/do.html', {
        'task': task,
    })