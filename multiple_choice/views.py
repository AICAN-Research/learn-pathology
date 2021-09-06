from django.shortcuts import render
from multiple_choice.models import MultipleChoice, Choice
from slide.models import Slide
from slide.views import slide_cache
from user.decorators import teacher_required


def do(request, task_id):
    """
    Student form for answering/viewing a multiple choice task
    """
    task = MultipleChoice.objects.get(task=task_id)

    answered = 'no'
    if request.method == 'POST':
        print('POST')
        # Process form
        print(request.POST['choice'])
        try:
            choice = Choice.objects.get(task=task, id=request.POST['choice'])
            if choice.correct:
                answered = 'correct'
            else:
                answered = 'incorrect'
        except Choice.DoesNotExist:
            raise ValueError

    slide_cache.load_slide_to_cache(task.annotated_slide.slide.id)
    return render(request, 'multiple_choice/do.html', {
        'task': task,
        'answered': answered,
    })

@teacher_required
def new(request):
    """
    Teacher form for creating a multiple choice task
    """
    if request.method == 'POST': # Form was submitted
        # TODO Validate form
        # TODO Create Task
        # TODO Create MultipleChoice, connect it to task
        # TODO Create all the Choice (s)
        # Give a message back to the user
        pass

    slides = Slide.objects.all() # Get all slides, so the teacher can choose which slide to use
    return render(request, 'multiple_choice/new.html', {
        'slides': slides
    })