
from django.contrib import messages
from django.shortcuts import render, redirect

from course.models import Course
from slide.models import Slide
from slide.views import slide_cache
from user.decorators import teacher_required
from task.models import Task
from tag.models import Tag

from task.forms import TaskForm
from multiple_choice.forms import MultipleChoiceForm
from multiple_choice.views import get_choice_formset
from free_text.forms import FreeTextForm
from click_question.forms import ClickQuestionForm
from one_to_one.forms import OneToOneForm
from one_to_one.views import get_sorting_pair_formset
from annotation_task.views import AnnotationTaskForm


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
        tasks = tasks.filter(tags__in=tags).distinct()

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
def new(request, slide_id=None, course_id=None):
    """
    Teacher form for creating a  task
    """
    context = {}

    if request.method == 'POST':

        # Either, the form with question type and slide selection is submitted
        if 'task_type' in request.POST:
            task_type = request.POST.get('task_type')
            selected_slide_id = request.POST.get('selected_slide_id')
            slide = Slide.objects.get(pk=selected_slide_id)
            slide_cache.load_slide_to_cache(slide.id)

            context['slide_id'] = slide_id
            context['slide'] = slide
            context['taskForm'] = TaskForm()

            if course_id is not None:
                context['course_id'] = course_id
                context['slides'] = Slide.objects.filter(course__id__in=[course_id])
            else:
                context['slides'] = Slide.objects.all()

            # Get empty forms and display page depending on which task type was selected
            if task_type == 'multiple_choice':
                context['new_url'] = '/multiple_choice/new'
                context['multipleChoiceForm'] = MultipleChoiceForm()
                context['choiceFormset'] = get_choice_formset()
                return render(request, 'multiple_choice/new.html', context)
            elif task_type == 'free_text':
                context['new_url'] = '/free_text/new'
                context['freeTextForm'] = FreeTextForm()
                return render(request, 'free_text/new.html', context)
            elif task_type == 'click_question':
                context['new_url'] = '/click_question/new'
                context['clickQuestionForm'] = ClickQuestionForm()
                return render(request, 'click_question/new.html', context)
            elif task_type == 'one_to_one_sort':
                context['new_url'] = '/one_to_one/new'
                context['oneToOneForm'] = OneToOneForm()
                context['sortingPairFormSet'] = get_sorting_pair_formset()
                return render(request, 'one_to_one/new.html', context)
            elif task_type == 'annotation_task':
                context['new_url'] = '/annotation_task/new'
                context['annotationTaskForm'] = AnnotationTaskForm()
                return render(request, 'annotation_task/new.html', context)
            else:
                raise ValueError(f"'{task_type}' is not a valid question type")

        # Or, the form with question information and annotations is submitted
        # TODO: Handle this directly using <form action="specific/task/url/" ...>

        if slide_id is not None:
            # Get slide
            slide_id = slide_id
            slide = Slide.objects.get(pk=slide_id)
            slide_cache.load_slide_to_cache(slide.id)

            context['slide_id'] = slide_id
            context['slide'] = slide
        if course_id is not None:
            context['course_id'] = course_id
            context['slides'] = Slide.objects.filter(course__id__in=[course_id])
        else:
            context['slides'] = Slide.objects.all()

    else:  # GET
        # TODO: Update this block. Current coed is from previous function
        if slide_id is not None:
            # Get slide
            slide_id = slide_id
            slide = Slide.objects.get(pk=slide_id)
            slide_cache.load_slide_to_cache(slide.id)

            context['slide_id'] = slide_id
            context['slide'] = slide
        if course_id is not None:
            context['course_id'] = course_id
            context['slides'] = Slide.objects.filter(course__id__in=[course_id])
        else:
            context['slides'] = Slide.objects.all()

    # if slide_id is not None:
    #     return render(request, 'task/new_or_edit_step2_add_info_and_annotate.html', context)
    return render(request, "task/new_or_edit_step1_select_type_and_slide.html", context)


@teacher_required
def delete(request, task_id):
    task = Task.objects.get(pk=task_id)

    # Remove task from all courses it is added to
    courses_with_task = Course.objects.filter(task=task)
    for course in courses_with_task:
        course.task.remove(task)

    # Delete task type (e.g. multiple choice, free text) and task
    task.type_model.delete()
    task.delete()

    messages.add_message(request, messages.SUCCESS, 'Task deleted.')
    return redirect('task:list')
