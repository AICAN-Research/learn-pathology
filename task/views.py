
from django.contrib import messages
from django.shortcuts import render, redirect

from course.models import Course
from slide.models import Slide
from slide.views import *
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


def list(request, slide_id=None):
    """
    Show list of tasks
    """


    if slide_id:
        tasks = Task.objects.filter(annotated_slide__slide=slide_id)
    else:
        tasks = Task.objects.all()
        slide_id = 0



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
        'slide_id': slide_id,
    })

@teacher_required
def new1(request, course_id=None):
    context = {}

    if course_id:
        context['course_id']= course_id

    return render(request, 'task/new_or_edit_select_type.html', context)

@teacher_required
def new3(request, course_id=None):
    context = {}
    context['course_id'] = course_id
    return render(request, 'task/new_or_edit_step2_add_info_and_annotate.html', context)

@teacher_required
def new2(request, course_id=None):
    last_url = request.META.get('HTTP_REFERER', '')
    prev_context = {} if ('task/new2/' not in last_url) else request.session.get('image_browser_context',
                                                                                              {})
    request.session['image_browser_context'] = {}
    context = {}
    if 'task_type' in request.GET:
        # If task_type is present in the GET request, use it
        task_type = request.GET.get('task_type')

        # Store task_type in session to persist across requests
        request.session['task_type'] = task_type
        context['task_type'] = task_type
        if course_id:
            request.session['course_id'] = course_id
        else :
            request.session['course_id'] = None
    else:
        # If this is not the first request, retrieve task_type from session
        context['task_type'] = request.session.get('task_type', None)
        course_id = request.session.get('course_id', None)


    # ==================================================================
    # Set up variables for which filtering options have been applied
    # ==================================================================
    organ_changed = ('organ-system' in request.GET)  # Organ selection changed
    general_path_changed = ('general_pathology_button' in request.GET)  # General pathology changed
    hist_path_changed = ('histology-pathology' in request.GET)  # Histology/pathology changed
    search_button_clicked = ('submit_button' in request.GET)  # Search query entered
    clear_search_clicked = ('clear_button' in request.GET)  # Search cleared

    # ==================================================================
    # Find selections for filtering options
    # ==================================================================
    # ORGAN FILTER
    if organ_changed:
        # Update the organ selection from the GET request
        selected_organ_tag_id = [request.GET.get('organ-system')]
    else:
        # Retrieve the previous organ selection or set to 'all'
        selected_organ_tag_id = prev_context['selected_organ_tag_ids'] if (
                'selected_organ_tag_ids' in prev_context) else ['all']
    if 'all' in selected_organ_tag_id:
        organ_tags = Tag.objects.filter(is_organ=True)
    else:
        organ_tags = Tag.objects.filter(is_organ=True, id__in=selected_organ_tag_id)

    # HISTOLOGY/PATHOLOGY FILTER
    if hist_path_changed:
        # Update the histology_pathology variable from the GET request
        histology_pathology = request.GET.get('histology-pathology')

        selected_histology = (histology_pathology == 'histology')
        selected_pathology = (histology_pathology == 'pathology')
    else:
        # Retrieve the previous values or set to False
        selected_histology = prev_context['selected_histology'] if 'selected_histology' in prev_context else False
        selected_pathology = prev_context['selected_pathology'] if 'selected_pathology' in prev_context else False

    selected_both = (not selected_histology and not selected_pathology)

    # SEARCH FILTER
    if search_button_clicked:
        search_query = request.GET.get('search')
        if len(search_query) == 0:
            search_query = None
    elif clear_search_clicked:
        search_query = None
    else:
        try:
            search_query = prev_context['search_query']
        except KeyError as err:
            search_query = None

    # ==================================================================
    # Filter slides, and apply search if the search button was clicked
    # ==================================================================
    if course_id :
        slides = Slide.objects.filter(course=course_id)
        context['course_id'] = course_id
    else:
        slides = Slide.objects.all()
    slides = slides.filter(tags__in=organ_tags)
    if not selected_both:
        slides = slides.filter(pathology=selected_pathology)
    if not (hist_path_changed and 'selected_general_pathology_ids' in prev_context):
        gen_path_tag_id = None
        if search_button_clicked and 'selected_general_pathology_ids' in prev_context:
            gen_path_tag_id = prev_context['selected_general_pathology_ids'][0]
        elif general_path_changed:
            gen_path_tag_id = int(request.GET.get('general_pathology_button').split('-')[-1])
        if gen_path_tag_id is not None:
            gen_path_tag = Tag.objects.get(id=gen_path_tag_id)
            slides = slides.filter(tags__in=[gen_path_tag])
            context['selected_general_pathology'] = gen_path_tag
            request.session['image_browser_context']['selected_general_pathology_ids'] = queryset_to_id_list(
                Tag.objects.filter(id=gen_path_tag_id))  # function takes queryset
    if search_query is not None:  # If search was updated, search among applicable_slides
        slides = slides.filter(Q(name__contains=search_query) | Q(description__contains=search_query))

    # ==================================================================
    # Update context
    # ==================================================================


    context['slides'] = sorted(slides, key=lambda s: s.name)
    context['selected_organ_tag'] = ['all'] if 'all' in selected_organ_tag_id else Tag.objects.filter(
        id__in=selected_organ_tag_id)
    context['selected_both'] = selected_both
    context['selected_histology'] = selected_histology
    context['selected_pathology'] = selected_pathology
    context['search_query'] = search_query
    context['organ_tags'] = Tag.objects.filter(is_organ=True).order_by('name')
    general_pathology_tags = [tag for tag in Tag.objects.filter(is_organ=False, is_stain=False) if
                              tag.name.lower() in GENERAL_PATHOLOGY_TAGS]
    context['general_pathology_tags'] = sorted(general_pathology_tags, key=lambda tag: tag.name)

    for key, val in prev_context.items():
        if key not in context and key not in ('selected_organ_tag_ids', 'selected_general_pathology_ids'):
            context[key] = prev_context[key]

    # ==================================================================
    # Update session variable to store selection
    # ==================================================================
    keys_that_contain_querysets = (
        'slides', 'selected_organ_tag', 'organ_tags', 'general_pathology_tags', 'selected_general_pathology',
        'selected_general_pathology_ids')
    for key, val in context.items():
        if key not in request.session['image_browser_context'] and key not in keys_that_contain_querysets:
            request.session['image_browser_context'][key] = context[key]
    request.session['image_browser_context']['selected_organ_tag_ids'] = queryset_to_id_list(
        context['selected_organ_tag'])
    request.session.modified = True

    if request.POST:


        task_type = context['task_type']
        context = {}
        selected_slide_id = request.POST.get('selected_slide_id')
        slide = Slide.objects.get(pk=selected_slide_id)
        slide_cache.load_slide_to_cache(slide.id)

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

        if course_id:
            context['course_id']= course_id
        return (request, 'task/new_or_edit_step_add_info_and_annotate', context)

    return render(request, 'task/new_or_edit_select_slide.html', context)




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


def reset_image_browser(request):
    # Save the task_type before resetting
    task_type = request.session.get('task_type', None)
    course_id = request.session.get('course_id', None)

    # Reset the image_browser_context if it exists
    if 'image_browser_context' in request.session:
        del request.session['image_browser_context']

    request.session['task_type'] = task_type

    if course_id:
        return redirect('task:new2', course_id)
    else:
        return redirect('task:new2')
