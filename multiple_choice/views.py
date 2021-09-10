from django.shortcuts import render, redirect, HttpResponse
from multiple_choice.models import MultipleChoice, Choice, MultipleChoiceForm
from slide.models import Slide
from slide.views import slide_cache
from user.decorators import teacher_required
from task.models import Task


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
        print("POST")
        form = MultipleChoiceForm(request.POST)

        if form.is_valid():

            task = Task()

            task.save()

            multiple_choice = form.save(commit=False)
            multiple_choice.task = task
            # Insert into DB
            multiple_choice.save()

            # TODO Create all the Choice (s)
            # for each entry box in form_data:
            #   if box is used --> create Choice
            #       if Choice is correct --> mark as correct
            #   else
            #       discard box


            # Give a message back to the user
            print("added multiple choice")
            return redirect('multiple_choice:added_task')

        else:
            form = MultipleChoiceForm()

    else:
        form = MultipleChoiceForm()

    slides = Slide.objects.all() # Get all slides, so the teacher can choose which slide to use

    return render(request, 'multiple_choice/new.html', {
        'form': form,
        'slides': slides
    })


def added_task(request):
    return HttpResponse("Successfully added task")
