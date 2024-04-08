import os.path
import json

import django.urls
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.uploadedfile import UploadedFile

from tag.models import Tag
from task.models import Task
from user.decorators import student_required, teacher_required
from slide.models import Slide, AnnotatedSlide, Pointer, BoundingBox, Annotation
from slide.forms import SlideForm, SlideDescriptionForm


GENERAL_PATHOLOGY_TAGS = (
    'inflammation', 'squamous cell carcinoma', 'adenocarcinoma', 'necrosis'
)


class SlideCache:
    """
    A class to keep a cache of slides in memory.
    """

    def __init__(self):
        # TODO load FAST once
        import fast
        # fast.Reporter.setGlobalReportMethod(fast.Reporter.COUT)
        test = fast.WholeSlideImageImporter.New() # Just to initialize FAST..
        self.slides = {}

    def load_slide_to_cache(self, slide_id):
        slide = Slide.objects.get(pk=slide_id)
        slide.load_image() # This will load slide with FAST, so it is ready to use
        self.slides[slide_id] = slide
        return slide

    def get_slide(self, slide_id):
        return self.slides[slide_id]


# Initialize global slide cache as a global variable. This should only happen once..
slide_cache = SlideCache()


def index(request):
    slides = Slide.objects.all()

    # Filters
    organs = request.GET.getlist('organ[]')
    if len(organs) > 0: slides = slides.filter(tags__in=organs)
    stains = request.GET.getlist('stain[]')
    if len(stains) > 0: slides = slides.filter(tags__in=stains)
    tags = request.GET.getlist('tag[]')
    if len(tags) > 0: slides = slides.filter(tags__in=tags)
    selected_pathology = request.GET.get('pathology', False)
    selected_histology = request.GET.get('histology', False)
    if not selected_pathology and not selected_histology:
        selected_pathology = True
        selected_histology = True
    if selected_pathology and not selected_histology:
        slides = slides.filter(pathology=True)
    elif not selected_pathology and selected_histology:
        slides = slides.filter(pathology=False)

    # Handle search and search results
    if request.GET.get('submit_button') == 'Clear search':
        search_query = None
        search_result = None
    else:
        search_query = request.GET.get('search')
        if search_query is not None and len(search_query) > 0:
            filter_result = Slide.objects.filter(
                Q(name__contains=search_query) | Q(description__contains=search_query)
            )
            search_result = filter_result
        else:
            search_query = None
            search_result = None

    return render(request, 'slide/index.html', {
        'slides': slides,
        'search_query': search_query,
        'search_result': search_result,
        'organ_tags': Tag.objects.filter(is_organ=True),
        'stain_tags': Tag.objects.filter(is_stain=True),
        'other_tags': Tag.objects.filter(is_organ=False, is_stain=False),
        'selected_organ_tags': organs,
        'selected_stain_tags': stains,
        'selected_other_tags': tags,
        'selected_pathology': selected_pathology,
        'selected_histology': selected_histology,
    })


def image_browser(request):
    """
    Set up the context for the image browser.

    The logic here is to find the relevant slides based on the currently active filters,
    and if search has been applied to search only among those relevant slides.
    """

    last_url = request.META.get('HTTP_REFERER', '')
    prev_context = {} if ('slide/browser/' not in last_url) else request.session.get('image_browser_context', {})
    request.session['image_browser_context'] = {}
    # Initialize empty context dictionary
    context = {}

    # ==================================================================
    # Set up variables for which filtering options have been applied
    # ==================================================================
    organ_changed = ('organ-system' in request.GET)                     # Organ selection changed
    general_path_changed = ('general_pathology_button' in request.GET)  # General pathology changed
    hist_path_changed = (general_path_changed or ('histology-pathology' in request.GET))   # Hist/path changed
    search_button_clicked = ('submit_button' in request.GET)            # Search query entered
    clear_search_clicked = ('clear_button' in request.GET)              # Search cleared

    # ==================================================================
    # Find selections for filtering options
    # ==================================================================
    # ORGAN FILTER
    if organ_changed:
        selected_organ_tag_id = [request.GET.get('organ-system')]
    else:
        selected_organ_tag_id = prev_context['selected_organ_tag_ids'] if ('selected_organ_tag_ids' in prev_context) else ['all']
    if 'all' in selected_organ_tag_id:
        organ_tags = Tag.objects.filter(is_organ=True)
    else:
        organ_tags = Tag.objects.filter(is_organ=True, id__in=selected_organ_tag_id)

    # HISTOLOGY/PATHOLOGY FILTER
    if hist_path_changed:
        if general_path_changed:
            histology_pathology = 'pathology'
            general_path_selected = True
        else:
            histology_pathology = request.GET.get('histology-pathology')
            general_path_selected = False

        selected_histology = (histology_pathology == 'histology')
        selected_pathology = (histology_pathology == 'pathology')
        selected_both = (not selected_histology and not selected_pathology)
    else:
        selected_both = prev_context['selected_both'] if 'selected_both' in prev_context else True
        selected_histology = prev_context['selected_histology'] if 'selected_histology' in prev_context else False
        selected_pathology = prev_context['selected_pathology'] if 'selected_pathology' in prev_context else False

        general_path_selected = ('selected_general_pathology_ids' in prev_context)

    # SEARCH
    if search_button_clicked:
        search_query = request.GET.get('search')
        if search_query is None or len(search_query) == 0:
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
    if general_path_selected:
        if general_path_changed:
            gen_path_tag_id = int(request.GET.get('general_pathology_button').split('-')[-1])
        elif 'selected_general_pathology_ids' in prev_context:
            gen_path_tag_id = prev_context['selected_general_pathology_ids'][0]
        gen_path_tag = Tag.objects.get(id=gen_path_tag_id)
        slides = slides.filter(tags__in=[gen_path_tag])
        context['selected_general_pathology'] = gen_path_tag
        request.session['image_browser_context']['selected_general_pathology_ids'] = queryset_to_id_list(Tag.objects.filter(id=gen_path_tag_id))  # function takes queryset
    if search_query is not None:    # If search was updated, search among applicable_slides
        slides = slides.filter(Q(name__contains=search_query) | Q(description__contains=search_query))

    # ==================================================================
    # Update context
    # ==================================================================
    context['slides'] = sorted(slides, key=lambda s: s.name)
    context['selected_organ_tag'] = ['all'] if 'all' in selected_organ_tag_id else Tag.objects.filter(id__in=selected_organ_tag_id)
    context['selected_both'] = selected_both
    context['selected_histology'] = selected_histology
    context['selected_pathology'] = selected_pathology
    context['search_query'] = search_query
    context['organ_tags'] = Tag.objects.filter(is_organ=True).order_by('name')
    general_pathology_tags = [tag for tag in Tag.objects.filter(is_organ=False, is_stain=False) if tag.name.lower() in GENERAL_PATHOLOGY_TAGS]
    context['general_pathology_tags'] = sorted(general_pathology_tags, key=lambda tag: tag.name)

    for key, val in prev_context.items():
        if key not in context and key not in ('selected_organ_tag_ids', 'selected_general_pathology_ids'):
            context[key] = prev_context[key]

    # ==================================================================
    # Update session variable to store selection
    # ==================================================================
    keys_that_contain_querysets = ('slides', 'selected_organ_tag', 'organ_tags', 'general_pathology_tags', 'selected_general_pathology', 'selected_general_pathology_ids')
    for key, val in context.items():
        if key not in request.session['image_browser_context'] and key not in keys_that_contain_querysets:
            request.session['image_browser_context'][key] = context[key]
    request.session['image_browser_context']['selected_organ_tag_ids'] = queryset_to_id_list(context['selected_organ_tag'])
    request.session.modified = True

    return render(request, 'slide/image_browser.html', context)


def reset_image_browser(request):
    if 'image_browser_context' in request.session:
        del request.session['image_browser_context']
    return redirect('slide:browser')


def queryset_to_id_list(queryset):
    if isinstance(queryset, django.db.models.query.QuerySet):
        id_list = [i[0] for i in queryset.values_list('id')]
        return id_list
    return queryset


def organ_tag_id_list_to_queryset(id_list):
    if 'all' in id_list:
        return id_list

    queryset = Tag.objects.filter(is_organ=True, id__in=id_list)
    return queryset


def whole_slide_view_full(request, slide_id):
    slide = slide_cache.load_slide_to_cache(slide_id)
    stain = slide.tags.get(is_stain=True)
    selected_general_pathology_tags = [tag for tag in slide.tags.filter(is_organ=False, is_stain=False)
                              if tag.name.lower() in GENERAL_PATHOLOGY_TAGS]

    other_tags = Tag.objects.filter(is_organ=False, is_stain=False)
    all_general_pathology_tags = []
    for tag in other_tags:
        if tag.name.lower() in GENERAL_PATHOLOGY_TAGS:
            all_general_pathology_tags.append(tag)



    context = {
        'slide': slide,
        'stain_name': stain.name,
        'general_pathology_tags': selected_general_pathology_tags,
        'all_general_pathology_tags' : all_general_pathology_tags
    }

    try:
        annotated_slide = AnnotatedSlide.objects.get(slide_id=slide.id, task__isnull=True)
    except MultipleObjectsReturned as err:
        print("Multiple descriptive AnnotatedSlide objects found. Clean up DB!")  # Using last slide for now")
        raise MultipleObjectsReturned(err)
    except ObjectDoesNotExist as err:
        print(f"Did not find descriptive AnnotatedSlide for slide with id {slide.id}.")
        annotated_slide = None

    context['annotated_slide'] = annotated_slide
    # Add annotations to context
    context['pointers'] = Pointer.objects.filter(annotated_slide=annotated_slide)
    context['boxes'] = BoundingBox.objects.filter(annotated_slide=annotated_slide)

    annotations = Annotation.objects.filter(annotated_slide=annotated_slide)
    context['annotations'] = []
    for ann in annotations:
        context['annotations'].append(ann.deserialize())

    return render(request, 'slide/view_wsi_accordion.html', context)



def whole_slide_viewer(request, slide_id):
    slide = slide_cache.load_slide_to_cache(slide_id)
    return render(request, 'slide/view_wsi.html', {
        'slide': slide,
    })


def tile(request, slide_id, osd_level, x, y):
    """
    Gets OSD tile from slide, converts to JPEG and sends to client
    """
    slide = slide_cache.get_slide(slide_id)
    try:
        buffer = slide.get_osd_tile_as_buffer(osd_level, x, y)
    except Exception as e:
        print(e)
        return HttpResponse(status=404)
    except:
        print('An error occured while loading a tile', osd_level, x, y)
        return HttpResponse(status=404)

    return HttpResponse(buffer.getvalue(), content_type='image/jpeg')


def create_thumbnail(slide_id):
    import fast
    slide = slide_cache.load_slide_to_cache(slide_id)
    access = slide.image.getAccess(fast.ACCESS_READ)
    image = access.getLevelAsImage(slide.image.getNrOfLevels()-1)
    scale = float(image.getWidth())/image.getHeight()
    resize = fast.ImageResizer.create(round(512*scale), 512).connect(image)
    fast.ImageFileExporter\
        .create(f'thumbnails/{slide_id}.jpg')\
        .connect(resize)\
        .run()


@teacher_required
def add(request):
    if request.method == 'POST':
        form = SlideForm(request.POST, request.FILES)
        with transaction.atomic():
            if form.is_valid():
                # Save form and create thumbnail
                file_path = store_file_in_db(form.files['image_file'])
                slide = form.save(file_path)
                create_thumbnail(slide.id)

                organ_tags = form.cleaned_data['organ_tags']
                stain_tags = form.cleaned_data['stain_tags']
                other_tags = form.cleaned_data['other_tags']
                slide.tags.set(organ_tags | stain_tags | other_tags)

                messages.add_message(request, messages.SUCCESS, 'Image added to database')
                return redirect('slide:view_full', slide.id)
    else:
        form = SlideForm()

    return render(request, 'slide/add.html', {'form': form})


def store_file_in_db(f: UploadedFile):
    destination_path = os.path.join(os.getcwd(), 'uploaded_images', f.name)  # TODO: improve destination path according to future DB
    # TODO: Ask the user if to substitute or keep both files
    if os.path.exists(destination_path):
        os.remove(destination_path)

    with open(destination_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return destination_path


@teacher_required
def edit_description(request, slide_id):
    """
    Form for editing a slide's long_description field
    """

    slide = slide_cache.load_slide_to_cache(slide_id)
    new_description = request.POST.get('new_description')

    try:
        slide.long_description = new_description
        slide.save()
        return JsonResponse({'success': True})
    except Slide.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slide not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@teacher_required
def edit_general_pathology_tags(request, slide_id):
    """
    Form for adding/removing general pathology tags for a slide
    """

    slide = slide_cache.load_slide_to_cache(slide_id)
    selected_tags_ids = request.POST.getlist('selected_tags[]')

    if not slide.pathology:
        messages.add_message(request, messages.ERROR, 'This slide is not a pathology slide. Cannot add general pathology tags.')
        return redirect('slide:view_full', slide_id=slide.id)

    # remove existing tags first
    selected_general_pathology_tags = [tag for tag in slide.tags.filter(is_organ=False, is_stain=False)
                                       if tag.name.lower() in GENERAL_PATHOLOGY_TAGS]
    if selected_general_pathology_tags:
        for tag in selected_general_pathology_tags:
            slide.tags.remove(tag)

    tag_names = []

    try:
        for tag_id in selected_tags_ids:
            tag_to_add = Tag.objects.get(id=tag_id)
            slide.tags.add(tag_to_add)
            # tag_names.append({'id': tag_to_add.id, 'name': tag_to_add.name})

        slide.save()

        return JsonResponse({'success': True})
    except Slide.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Slide not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)




@teacher_required
def add_tag(request):
    """
    View to handle button for adding general pathology tag to a slide
    """
    print('Adding tag to slide')

    slide_id = int(request.GET.get('slide_id'))
    slide = Slide.objects.get(id=slide_id)
    tag_id = int(request.GET.get('tag_id'))

    if request.method == 'GET':
        tag_to_add = Tag.objects.get(id=tag_id)
        slide.tags.add(tag_to_add)
        slide.save()

    return JsonResponse(data={})


@teacher_required
def remove_tag(request):
    """
    View to handle button for removing general pathology tag from a slide
    """
    print('Removing tag from slide')

    slide_id = int(request.GET.get('slide_id'))
    slide = Slide.objects.get(id=slide_id)
    tag_id = int(request.GET.get('tag_id'))

    if request.method == 'GET':
        tag_to_remove = Tag.objects.get(id=tag_id)
        slide.tags.remove(tag_to_remove)
        slide.save()

    return JsonResponse(data={})


@teacher_required
def add_or_edit_descriptive_annotation(request, slide_id):
    """
    View to handle descriptive/basic annotations of a Slide.
    (Annotations that are not connected to Courses or Tasks)
    """
    context = {}

    # Get slide
    slide = Slide.objects.get(pk=slide_id)
    slide_cache.load_slide_to_cache(slide.id)
    context['slide'] = slide

    # Get annotated slide
    try:
        annotated_slide = AnnotatedSlide.objects.get(slide_id=slide.id, task__isnull=True)
    except MultipleObjectsReturned as err:
        print("Multiple descriptive AnnotatedSlide objects found. Clean up DB!")  # Using last slide for now")
        raise MultipleObjectsReturned(err)
    except ObjectDoesNotExist as err:
        print("Did not find descriptive AnnotatedSlide. Making a new object")
        annotated_slide = AnnotatedSlide()
        annotated_slide.slide = slide

    if request.method == 'POST':  # Form was submitted
        with transaction.atomic():  # Make save operation atomic
            # Delete all existing annotations
            delete_existing_annotations(annotated_slide)
            annotated_slide.save()

            # Store annotations (pointers)
            for key in request.POST:

                if key.startswith('right-arrow-overlay-') and key.endswith('-text'):
                    save_pointer_annotation(request, key, annotated_slide)
                elif key.startswith('boundingbox-') and key.endswith('-text'):
                    save_boundingbox_annotation(request, key, annotated_slide)

            # Give a message back to the user
            messages.add_message(request, messages.SUCCESS, 'Annotations added successfully!')
            return redirect('slide:view_full', slide_id=slide_id)

    else:
        context['annotated_slide'] = annotated_slide
        context['pointers'] = Pointer.objects.filter(annotated_slide=annotated_slide)
        context['boxes'] = BoundingBox.objects.filter(annotated_slide=annotated_slide)

        print('Annotated slide id:', annotated_slide.id)

    context['annotation_types'] = [
        Pointer, BoundingBox
    ]
    return render(request, 'slide/add_edit_descriptive_annotations.html', context)


def create_annotation(request):
    """
    Async saving of annotorious annotations
    """
    print('Creating new annotation')

    slide_id = int(request.GET.get('slide_id'))
    slide = Slide.objects.get(id=slide_id)

    # Get descriptive AnnotatedSlide
    try:
        annotated_slide = AnnotatedSlide.objects.get(slide=slide, task__isnull=True)
    except ObjectDoesNotExist as err:
        annotated_slide = AnnotatedSlide(slide=slide)
        annotated_slide.save()
    except MultipleObjectsReturned as err:
        print("Multiple descriptive AnnotatedSlide objects found. Clean up DB!")  # Using last slide for now")
        raise MultipleObjectsReturned(err)

    # Create annotation
    annotation = Annotation(annotated_slide=annotated_slide,
                            json_string=request.GET.get('annotation'))
    annotation.save()

    return JsonResponse(data={})


def update_annotation(request):
    """
    Async updating of annotorious annotations
    """
    print('Updating annotation')

    slide_id = int(request.GET.get('slide_id'))
    slide = Slide.objects.get(id=slide_id)

    # Get descriptive AnnotatedSlide
    annotated_slide = AnnotatedSlide.objects.get(slide=slide, task__isnull=True)

    # Get correct annotation (matching Annotorious/W3C id)
    annotations_this_slide = Annotation.objects.filter(annotated_slide=annotated_slide)
    annotation_json_old = request.GET.get('previous_annotation')
    annotation_id = json.loads(annotation_json_old)['id']

    # Find the corresponding annotation using the ID given by Annotorious
    annotation = None
    for annotation in annotations_this_slide:
        if annotation_id in annotation.deserialize()['id']:
            break

    # Replace old JSON with new
    annotation.json_string = request.GET.get('annotation')
    annotation.save()

    return JsonResponse(data={})


def delete_annotation(request):
    """
    Async deleting of annotorious annotations
    """
    print('Deleting annotation')

    slide_id = int(request.GET.get('slide_id'))
    slide = Slide.objects.get(id=slide_id)

    # Get descriptive AnnotatedSlide
    annotated_slide = AnnotatedSlide.objects.get(slide=slide, task__isnull=True)

    # Get correct annotation (matching Annotorious/W3C id)
    annotations_this_slide = Annotation.objects.filter(annotated_slide=annotated_slide)
    annotation_json = request.GET.get('annotation')
    annotation_id = json.loads(annotation_json)['id']

    # Find the corresponding annotation using the ID given by Annotorious
    annotation = None
    for annotation in annotations_this_slide:
        if annotation_id in annotation.deserialize()['id']:
            break

    annotation.delete()

    return JsonResponse(data={})


def delete_existing_annotations(annotated_slide):
    """
    Before saving new annotations, delete all existing to prevent duplicates
    and simplify handling (don't need to check if objects are unique, etc.)
    """
    Pointer.objects.filter(annotated_slide=annotated_slide).delete()
    BoundingBox.objects.filter(annotated_slide=annotated_slide).delete()


@teacher_required
def save_pointer_annotation(request, key, annotated_slide):
    prefix = key[:-len('text')]
    text = request.POST[key]
    position_x = float(request.POST[prefix + 'x'])
    position_y = float(request.POST[prefix + 'y'])

    # Using get_or_create matches pointers and retrieves identical one if it exists
    pointer, pointer_was_created = Pointer.objects.get_or_create(
        annotated_slide=annotated_slide,
        text=text,
        position_x=position_x,
        position_y=position_y
    )
    if pointer_was_created:
        try:
            pointer.save()
        except IntegrityError as err:
            print(f"{err.__class__.__name__}: Could not save pointer. {err}")


@teacher_required
def save_boundingbox_annotation(request, key, annotated_slide):
    prefix = key[:-len('text')]
    text = request.POST[key]
    position_x = float(request.POST[prefix + 'x'])
    position_y = float(request.POST[prefix + 'y'])
    width = round(float(request.POST[prefix + 'width']), ndigits=5)
    height = round(float(request.POST[prefix + 'height']), ndigits=5)

    # Using get_or_create matches pointers and retrieves identical one if it exists
    box, box_was_created = BoundingBox.objects.get_or_create(
        annotated_slide=annotated_slide,
        text=text,
        position_x=position_x,
        position_y=position_y,
        width=width,
        height=height
    )
    if box_was_created:
        try:
            box.save()
        except IntegrityError as err:
            print(f"{err.__class__.__name__}: Could not save box. {err}")
