from django.contrib import messages
from django.db import transaction
from django.forms import formset_factory
from django.shortcuts import render, redirect, HttpResponse
from multiple_choice.models import MultipleChoice, Choice
from multiple_choice.forms import MultipleChoiceForm, ChoiceForm, TaskForm
from slide.models import Slide, Pointer, AnnotatedSlide
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

    slide_cache.load_slide_to_cache(task.task.annotated_slide.slide.id)
    return render(request, 'multiple_choice/do.html', {
        'task': task,
        'answered': answered,
    })

@teacher_required
def new(request, slide_id):
    """
    Teacher form for creating a multiple choice task
    """

    # Get slide
    slide = Slide.objects.get(pk=slide_id)
    slide_cache.load_slide_to_cache(slide.id)

    # Process forms
    ChoiceFormset = formset_factory(ChoiceForm, extra=5)
    if request.method == 'POST': # Form was submitted
        print("POST")
        taskForm = TaskForm(request.POST)
        form = MultipleChoiceForm(request.POST)
        choiceFormset = ChoiceFormset(request.POST)

        with transaction.atomic():  # Make save operation atomic
            if form.is_valid() and taskForm.is_valid() and choiceFormset.is_valid():
                # Create annotated slide
                annotated_slide = AnnotatedSlide()
                annotated_slide.slide = slide
                annotated_slide.save()

                # Create task
                task = taskForm.save(commit=False)
                task.annotated_slide = annotated_slide
                task.save()

                # Create multiple choice
                multiple_choice = form.save(commit=False)
                multiple_choice.task = task
                multiple_choice.save()

                for choiceForm in choiceFormset:
                    choice = choiceForm.save(commit=False)
                    if len(choice.text) > 0:
                        choice.task = multiple_choice
                        choice.save()

                # Store annotations (pointers)
                for key in request.POST:
                    print(key, request.POST[key])
                    if key.startswith('pointer-') and key.endswith('-text'):
                        prefix = key[:-len('text')]
                        pointer = Pointer()
                        pointer.text = request.POST[key]
                        pointer.position_x = float(request.POST[prefix+'x'])
                        pointer.position_y = float(request.POST[prefix+'x'])
                        pointer.annotated_slide = annotated_slide
                        pointer.save()

                # Give a message back to the user
                messages.add_message(request, messages.SUCCESS, 'Task added successfully!')
                return redirect('task_list')
    else:
        taskForm = TaskForm()
        form = MultipleChoiceForm()
        choiceFormset = ChoiceFormset()

    return render(request, 'multiple_choice/new.html', {
        'slide': slide,
        'form': form,
        'taskForm': taskForm,
        'choiceFormset': choiceFormset,
    })


def added_task(request):
    return HttpResponse("Successfully added task")
