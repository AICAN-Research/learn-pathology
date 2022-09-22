import os.path

import django.urls
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.uploadedfile import UploadedFile

from tag.models import Tag
from user.decorators import student_required, teacher_required
from slide.models import Slide
from slide.forms import SlideForm, SlideDescriptionForm


class SlideCache:
    """
    A class to keep a cache of slides in memory.
    """

    def __init__(self):
        # TODO load FAST once
        import fast
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
    TODO:   - CLEAN UP FUNCTION
    """

    prev_context = request.session.get('image_browser_context', None)
    if prev_context is None:
        # First entry to image browser? Initialize new empty dictionary
        request.session['image_browser_context'] = {}

    organ_changed = ('organ-system' in request.GET)
    hist_path_changed = ('histology-pathology' in request.GET)
    context = {}

    if organ_changed:
        selected_organ = request.GET.get('organ-system')
        if selected_organ == 'all':
            slides = Slide.objects.all()
            selected_organ_tag = ['all']
            # Store changes in session
            request.session['image_browser_context']['selected_organ_tag_ids'] = selected_organ_tag
        else:
            selected_organ_tag = Tag.objects.filter(id=selected_organ)
            slides = Slide.objects.filter(tags__in=selected_organ_tag)
            # Store changes in session
            request.session['image_browser_context']['selected_organ_tag_ids'] = queryset_to_id_list(selected_organ_tag)

        # Add to context
        context['slides'] = slides
        context['selected_organ_tag'] = selected_organ_tag

    elif hist_path_changed:
        # Use previously selected organ slides
        selected_organ_tag = organ_tag_id_list_to_queryset(
            prev_context['selected_organ_tag_ids']
        )
        if 'all' in selected_organ_tag:
            slides = Slide.objects.all()
        else:
            slides = Slide.objects.filter(tags__in=selected_organ_tag)

        histology_pathology = request.GET.get('histology-pathology')
        if histology_pathology == 'histology':
            selected_both = False
            selected_histology = True
            selected_pathology = False
            slides = slides.filter(pathology=False)
        elif histology_pathology == 'pathology':
            selected_both = False
            selected_histology = False
            selected_pathology = True
            slides = slides.filter(pathology=True)
        else:
            selected_both = True
            selected_histology = False
            selected_pathology = False
            # do not filter slides

        # Add to context
        context['slides'] = slides
        context['selected_organ_tag'] = selected_organ_tag
        context['selected_both'] = selected_both
        context['selected_histology'] = selected_histology
        context['selected_pathology'] = selected_pathology

    else:
        slides = Slide.objects.all()
        selected_organ_tag = ['all']
        # Store changes in session
        request.session['image_browser_context']['selected_organ_tag_ids'] = queryset_to_id_list(selected_organ_tag)
        request.session['image_browser_context']['selected_both'] = True
        request.session['image_browser_context']['selected_histology'] = False
        request.session['image_browser_context']['selected_pathology'] = False
        # Add to context
        context['slides'] = slides
        context['selected_organ_tag'] = selected_organ_tag

    # Final updates to context
    context['organ_tags'] = Tag.objects.filter(is_organ=True).order_by('name')
    for key, val in request.session['image_browser_context'].items():
        if key not in context and key not in ('slide_ids', 'selected_organ_tag_ids'):
            context[key] = request.session['image_browser_context'][key]

    request.session.modified = True
    return render(request, 'slide/image_browser.html', context)


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
    return render(request, 'slide/view_wsi_full.html', {
        'slide': slide,
    })


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
    scale = float(image.getHeight())/image.getWidth()
    resize = fast.ImageResizer.create(128, round(128*scale)).connect(image)
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

    slide = get_object_or_404(Slide, id=slide_id)
    form = SlideDescriptionForm(request.POST or None, instance=slide)

    if request.method == 'POST':  # Form was submitted
        if form.is_valid():
            form.save()
            messages.add_message(request, messages.SUCCESS,
                 f'The slide description of {slide.name} was altered!')
            return redirect('slide:browser')

    return render(request, 'slide/edit_description.html', {
        'slide': slide,
        'form': form
    })




