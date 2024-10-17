from django.shortcuts import render
from slide.views import *
from django.shortcuts import render, redirect
from django.urls import reverse

# Create your views here.

def index(request):
    last_url = request.META.get('HTTP_REFERER', '')
    prev_context = {} if ('comparison/index' not in last_url) else request.session.get('image_browser_context',
                                                                                              {})
    request.session['image_browser_context'] = {}
    # Initialize empty context dictionary
    context = {}

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


    context['course'] = None
    context['slides_in_course'] = None



    return render(request, 'comparison/image_browser.html', context)



def comparision_view(request, slide_1=None, slide_2=None):
    # Check if the request is a POST and contains the 'selected_slides' data
    if request.method == 'POST' and 'selected_slides' in request.POST:
        # Get the selected slide IDs from the form
        selected_slides = request.POST.get('selected_slides')

        if selected_slides:  # Make sure selected_slides is not empty
            # Split the string to get a list of slide IDs
            slide_ids = selected_slides.split(',')

    elif slide_1 and slide_2:
        slide_ids =[slide_1,slide_2]

    else:
        return redirect(reverse('comparison:index'))

    # Initialize context dictionary to hold data for each slide
    slides_data = {}

    # Iterate over each slide ID and gather the necessary information
    for index, slide_id in enumerate(slide_ids):
        # Load the slide from the cache
        slide = slide_cache.load_slide_to_cache(slide_id)

        # Get stain tag
        stain = slide.tags.get(is_stain=True)

        # Filter general pathology tags
        selected_general_pathology_tags = [
            tag for tag in slide.tags.filter(is_organ=False, is_stain=False)
            if tag.name.lower() in GENERAL_PATHOLOGY_TAGS
        ]

        # Collect other general pathology tags
        other_tags = Tag.objects.filter(is_organ=False, is_stain=False)
        all_general_pathology_tags = [
            tag for tag in other_tags if tag.name.lower() in GENERAL_PATHOLOGY_TAGS
        ]

        # Attempt to get the annotated slide
        try:
            annotated_slide = AnnotatedSlide.objects.get(slide_id=slide.id, task__isnull=True)
        except MultipleObjectsReturned as err:
            print(f"Multiple descriptive AnnotatedSlide objects found for slide {slide.id}. Clean up DB!")
            raise MultipleObjectsReturned(err)
        except ObjectDoesNotExist:
            print(f"Did not find descriptive AnnotatedSlide for slide with id {slide.id}.")
            annotated_slide = None

        # Get annotations for the slide
        annotations = Annotation.objects.filter(annotated_slide=annotated_slide)
        serialized_annotations = [ann.deserialize() for ann in annotations]

        # Store each slide's data in the context dictionary with individual keys
        slides_data[f'slide_{index + 1}'] = slide
        slides_data[f'stain_name_{index + 1}'] = stain.name if stain else None
        slides_data[f'general_pathology_tags_{index + 1}'] = selected_general_pathology_tags
        slides_data[f'all_general_pathology_tags_{index + 1}'] = all_general_pathology_tags
        slides_data[f'annotated_slide_{index + 1}'] = annotated_slide
        slides_data[f'annotations_{index + 1}'] = serialized_annotations

    # Render the comparison page with the collected slide data
    return render(request, 'comparison/comparison_page.html', slides_data)



def reset_image_browser(request):
    if 'image_browser_context' in request.session:
        del request.session['image_browser_context']
    return redirect('comparison:index')