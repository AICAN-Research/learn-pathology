import os.path
import json
import shutil
import string
import random
from os.path import join

import django.urls
import fast
from django.conf import settings
from django.contrib import messages
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.core.files.uploadedfile import UploadedFile
from django.views.decorators.cache import cache_page
from tag.models import Tag
from user.decorators import teacher_required, uploader_required
from slide.models import Slide, AnnotatedSlide, Annotation, SlideUpload
from slide.forms import SlideMetadataForm

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
        if slide_id not in self.slides:
            slide = Slide.objects.get(pk=slide_id)
            slide.load_image() # This will load slide with FAST, so it is ready to use
            self.slides[slide_id] = slide
        return self.slides[slide_id]

    def get_slide(self, slide_id):
        return self.slides[slide_id]

    def remove(self, slide_id):
        if slide_id in self.slides:
            del self.slides[slide_id]


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
                Q(name__contains=search_query) | Q(description__contains=search_query) | Q(long_description__contains=search_query)
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
    Set up the context for the image browser page.

    The logic here is to find the relevant slides based on the currently active filters,
    and if search has been applied to search only among those relevant slides.
    """

    last_url = request.headers.get('referer', '')
    prev_context = {} if ('slide/browser/' not in last_url) else request.session.get('image_browser_context', {})
    request.session['image_browser_context'] = {}
    # Initialize empty context dictionary
    context = {}

    # ==================================================================
    # Set up variables for which filtering options have been applied
    # ==================================================================
    organ_changed = ('organ-system' in request.GET)                     # Organ selection changed
    other_changed = ('other-tag' in request.GET)                     # Other tag selection changed
    general_path_changed = ('general_pathology_button' in request.GET)  # General pathology changed
    hist_path_changed = ('histology-pathology' in request.GET)          # Histology/pathology changed
    search_button_clicked = ('submit_button' in request.GET)            # Search query entered
    clear_search_clicked = ('clear_button' in request.GET)              # Search cleared

    # ==================================================================
    # Find selections for filtering options
    # ==================================================================
    # ORGAN FILTER
    if organ_changed:
        # Update the organ selection from the GET request
        selected_organ_tag_id = [request.GET.get('organ-system')]
    else:
        # Retrieve the previous organ selection or set to 'all'
        selected_organ_tag_id = prev_context['selected_organ_tag_ids'] if ('selected_organ_tag_ids' in prev_context) else ['all']
    if 'all' in selected_organ_tag_id:
        organ_tags = Tag.objects.filter(is_organ=True)
    else:
        organ_tags = Tag.objects.filter(is_organ=True, id__in=selected_organ_tag_id)

    # OTHER FILTER
    if other_changed:
        # Update the organ selection from the GET request
        selected_other_tag_id = [request.GET.get('other-tag')]
    else:
        # Retrieve the previous other selection or set to 'all'
        selected_other_tag_id = prev_context['selected_other_tag_ids'] if (
                    'selected_other_tag_ids' in prev_context) else ['all']
    if 'all' in selected_other_tag_id:
        other_tags = None
    else:
        other_tags = Tag.objects.filter(is_organ=False, is_stain=False, id__in=selected_other_tag_id)

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
    if other_tags is not None:
        slides = slides.filter(tags__in=other_tags)
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
            request.session['image_browser_context']['selected_general_pathology_ids'] = queryset_to_id_list(Tag.objects.filter(id=gen_path_tag_id))  # function takes queryset
    if search_query is not None:    # If search was updated, search among applicable_slides
        slides = slides.filter(Q(name__contains=search_query) | Q(description__contains=search_query) | Q(long_description__contains=search_query))

    # ==================================================================
    # Update context
    # ==================================================================
    context['slides'] = sorted(slides, key=lambda s: s.name)
    context['selected_organ_tag'] = ['all'] if 'all' in selected_organ_tag_id else Tag.objects.filter(id__in=selected_organ_tag_id)
    context['selected_other_tag'] = ['all'] if 'all' in selected_other_tag_id else Tag.objects.filter(id__in=selected_other_tag_id)
    context['selected_both'] = selected_both
    context['selected_histology'] = selected_histology
    context['selected_pathology'] = selected_pathology
    context['search_query'] = search_query
    context['organ_tags'] = Tag.objects.filter(is_organ=True).order_by('name')
    context['other_tags'] = Tag.objects.filter(is_organ=False, is_stain=False).order_by('name')
    general_pathology_tags = [tag for tag in Tag.objects.filter(is_organ=False, is_stain=False) if tag.name.lower() in GENERAL_PATHOLOGY_TAGS]
    context['general_pathology_tags'] = sorted(general_pathology_tags, key=lambda tag: tag.name)

    for key, val in prev_context.items():
        if key not in context and key not in ('selected_organ_tag_ids', 'selected_general_pathology_ids', 'selected_other_tag_ids'):
            context[key] = prev_context[key]

    # ==================================================================
    # Update session variable to store selection
    # ==================================================================
    keys_that_contain_querysets = ('slides', 'selected_organ_tag', 'organ_tags', 'other_tags', 'selected_other_tag', 'general_pathology_tags', 'selected_general_pathology', 'selected_general_pathology_ids')
    for key, val in context.items():
        if key not in request.session['image_browser_context'] and key not in keys_that_contain_querysets:
            request.session['image_browser_context'][key] = context[key]
    request.session['image_browser_context']['selected_organ_tag_ids'] = queryset_to_id_list(context['selected_organ_tag'])
    request.session['image_browser_context']['selected_other_tag_ids'] = queryset_to_id_list(context['selected_other_tag'])
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


def whole_slide_view_full(request, slide_id, course_id=None):
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
        'all_general_pathology_tags' : all_general_pathology_tags,
        'course_id': course_id,
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


@cache_page(60 * 30)
def tile(request, slide_id, osd_level, x, y):
    """
    Gets OSD tile from slide, converts to JPEG and sends to client
    """
    slide = slide_cache.load_slide_to_cache(slide_id)
    try:
        buffer = slide.get_osd_tile_as_buffer(osd_level, x, y)
    except Exception as e:
        print(e)
        return HttpResponse(status=404)
    except:
        print('An error occured while loading a tile', osd_level, x, y)
        return HttpResponse(status=404)

    return HttpResponse(buffer.getvalue(), content_type='image/jpeg')


def create_thumbnail(wsi, path):
    import fast
    access = wsi.getAccess(fast.ACCESS_READ)
    # Select best level
    thumbnail_level = None
    for level in range(wsi.getNrOfLevels() - 1, 0, -1):
        if wsi.getLevelHeight(level) >= 1024 and wsi.getLevelHeight(level) < 16000 and wsi.getLevelWidth(level) < 16000:
            thumbnail_level = level
            break
    if thumbnail_level is None:
        raise ValueError('Unable to find a level to create a thumbnail from in the WSI. Are you sure it is pyramidal?')
    else:
        image = access.getLevelAsImage(thumbnail_level)
        scale = float(image.getWidth()) / image.getHeight()
        resize = fast.ImageResizer.create(round(512 * scale), 512).connect(image)
        fast.ImageFileExporter \
            .create(path) \
            .connect(resize) \
            .run()


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
            tag_names.append({'id': tag_to_add.id, 'name': tag_to_add.name})

        slide.save()

        return JsonResponse({'success': True, 'tag_names': tag_names})
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


@teacher_required
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


@teacher_required
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


@uploader_required
def upload_slides(request):
    if request.method == 'POST':
        file = request.FILES['file'].read()
        upload_id = request.POST['upload_id']
        finished = request.POST['finished'] == 'true'

        filename = request.POST['filename']
        if upload_id == 'null': # New upload
            path = os.path.join(settings.TEMP_UPLOADED_SLIDE_DIR, request.user.username, filename)
            # Check if filename exists before uploading, if so try to add random prefix
            while os.path.exists(path):
                characters = string.ascii_letters + string.digits  # Pool of possible characters
                random_string = ''.join(random.choice(characters) for _ in range(5))
                filename = random_string + '_' + filename
                path = os.path.join(settings.TEMP_UPLOADED_SLIDE_DIR, request.user.username, filename)
            upload = SlideUpload()
            upload.uploaded_by = request.user
            upload.name = filename
            upload.finished = False
            upload.path = path
            upload.save()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'wb+') as destination:
                destination.write(file)
            if finished:
                upload.finished = True
                upload.save()
                res = JsonResponse({'data': 'Uploaded Successfully', 'upload_id': upload.id})
            else:
                res = JsonResponse({'upload_id': upload.id})
            return res
        else: # existing upload
            try:
                upload = SlideUpload.objects.get(uploaded_by=request.user, id=upload_id)
            except SlideUpload.DoesNotExist:
                return JsonResponse({'data': 'No such upload exists'})

            if not upload.finished:
                with open(upload.path, 'ab+') as destination:
                    destination.write(file)
                if finished:
                    upload.finished = True
                    upload.save()
                    return JsonResponse({'data': 'Uploaded Successfully', 'upload_id': upload.id})
                else:
                    return JsonResponse({'upload_id': upload.id})
            else:
                return JsonResponse({'data': 'Upload is already finished'})
    else: # If not POST
        # Remove old (failed) downloads
        slides = SlideUpload.objects.filter(uploaded_by=request.user, finished=False)
        for slide in slides:
            try:
                os.remove(slide.path)
            except Exception as e:
                print('Error deleting file:', str(e))
            try:
                os.remove(join(settings.TEMP_UPLOADED_SLIDE_DIR, 'thumbnails' + slide.id + '.jpg'))
            except Exception as e:
                print('Error deleting file:', str(e))
            slide.delete()
    existing_slide_upload_count = SlideUpload.objects.filter(uploaded_by=request.user, finished=True).count()
    return render(request, 'slide/upload_slides.html', {'existing_slide_upload_count': existing_slide_upload_count})


@uploader_required
def process_uploaded_slides(request):
    # TODO only do this once?
    # Process the slides uploaded by this user
    uploads = SlideUpload.objects.filter(uploaded_by=request.user, finished=True, checked=False).order_by('name')
    progress = 0
    currentUpload = 0
    dicom_seriesUID = {}
    uploads_to_move = {}

    # Correct dicom files if needed
    for upload in uploads:
        path = upload.path
        # Check if dicom
        if path.endswith('.dcm'):
            import pydicom
            from pydicom.datadict import tag_for_keyword
            with pydicom.dcmread(path) as ds:
                tag = tag_for_keyword('ICCProfile')
                if tag not in ds:
                    icc_profile_data = b"ICC Profile Data"
                    ds.ICCProfile = icc_profile_data
                    ds.save_as(path)
                    print('Corrected')

    seriesUID = ''
    for upload in uploads:
        # For each uploaded file
        path = upload.path
        try:
            # 1. Try to open it:
            wsi = fast.WholeSlideImageImporter.create(path).runAndGetOutputData()

            try:
                # Dicom is stored in multiple files, but they should all have the same series instance UID
                seriesUID = wsi.getMetadata('dicom.SeriesInstanceUID')
                print(seriesUID)
                if seriesUID in dicom_seriesUID.keys():
                    # Skip this file
                    uploads_to_move[dicom_seriesUID[seriesUID]][2].append(upload.path)
                    upload.delete()
                    currentUpload += 1
                    continue
                else:
                    dicom_seriesUID[seriesUID] = upload.id
                    print(seriesUID, 'stored', dicom_seriesUID[seriesUID], seriesUID in dicom_seriesUID.keys())
            except Exception as e:
                seriesUID = ''

            # 2. Create thumbnail
            os.makedirs(join(settings.TEMP_UPLOADED_SLIDE_DIR, 'thumbnails'), exist_ok=True)
            create_thumbnail(wsi, join(settings.TEMP_UPLOADED_SLIDE_DIR, 'thumbnails', f'{upload.id}.jpg'))
            del wsi

            upload.checked = True
            upload.save()
            uploads_to_move[upload.id] = (
                upload,
                os.path.join(os.path.dirname(upload.path), str(upload.id), upload.name),
                [upload.path]
            )
        except Exception as e:
            # 4. Remove invalid files
            print('Error: ' + str(e))
            messages.error(request, f'The file upload {upload.name} was invalid and removed because: {str(e)}')
            os.remove(path)
            if seriesUID:
                del dicom_seriesUID[seriesUID]
            upload.delete()

        progress = int(round((currentUpload/len(uploads))*100))
        currentUpload += 1
        print(progress)

    # 3. Group and move files to subfolders
    for upload, new_path, filepaths in uploads_to_move.values():
        upload.path = new_path
        upload.save()
        os.makedirs(os.path.dirname(new_path), exist_ok=True)
        for filepath in filepaths:
            shutil.move(
                filepath,
                os.path.dirname(new_path)
            )

    return redirect('slide:view_uploads')


@uploader_required
def view_uploaded_slides(request):
    unprocessedSlides = SlideUpload.objects.filter(uploaded_by=request.user, finished=True, checked=False).count()
    if unprocessedSlides > 0:
        return redirect('slide:process_uploads')

    if request.method == 'POST':
        upload = SlideUpload.objects.get(uploaded_by=request.user, id=request.POST['upload_file_id'])
        slide_path = upload.path
        thumbnail_path = os.path.join(settings.TEMP_UPLOADED_SLIDE_DIR, 'thumbnails', str(upload.id) + '.jpg')
        if 'action' not in request.POST: # If action not set, user wants to delete
            error = ''
            try:
                # Delete entire slide upload folder
                shutil.rmtree(os.path.dirname(slide_path))
            except Exception as e:
                error = 'Failed to delete slide: ' + str(e)
            try:
                os.remove(thumbnail_path)
            except Exception as e:
                error += 'Failed to delete thumbnail: ' + str(e)
            upload.delete()
            if len(error) > 0:
                messages.error(request, f'Error occured while deleting slide upload {upload.name}: ' + error)
            else:
                messages.success(request, f'Slide upload {upload.name} was deleted.')
        else:
            form = SlideMetadataForm(request.POST)
            if form.is_valid():
                slide = form.save(commit=False)
                slide.uploaded_by = request.user
                slide.save()
                organ_tags = form.cleaned_data['organ_tags']
                stain_tags = form.cleaned_data['stain_tags']
                other_tags = form.cleaned_data['other_tags']
                slide.tags.set(organ_tags | stain_tags | other_tags)
                new_slide_path = os.path.join(settings.UPLOADED_SLIDE_DIR, str(slide.id), os.path.basename(upload.path))
                os.makedirs(settings.UPLOADED_SLIDE_DIR, exist_ok=True)
                slide.path = new_slide_path
                slide.save()
                # Move thumbnail
                shutil.move(
                    thumbnail_path,
                    os.path.join(settings.SLIDE_THUMBNAILS_DIR, str(slide.id) + '.jpg')
                )
                # Move slide folder
                os.rename(
                    os.path.dirname(slide_path),
                    os.path.dirname(new_slide_path)
                )
                upload.delete()
                messages.success(request, f'Slide {slide.name} was saved to the database.')
            else:
                messages.error(request, f'Invalid metadata.')
                # TODO

    # Create form for each slide allowing user to insert metadata, and display thumbnail created
    files = SlideUpload.objects.filter(uploaded_by=request.user, finished=True, checked=True)
    for file in files:
        form = SlideMetadataForm()
        file.form = form

        # Get some metainfo from file
        wsi = fast.WholeSlideImageImporter.create(file.path).runAndGetOutputData()
        file.levels = wsi.getNrOfLevels()
        file.width = wsi.getFullWidth()
        file.height = wsi.getFullHeight()
        if wsi.getSpacing()[0] != 1 and wsi.getSpacing()[1] != 1:
            file.physical_width = round(wsi.getFullWidth()*wsi.getSpacing()[0], 2)
            file.physical_height = round(wsi.getFullHeight() * wsi.getSpacing()[1], 2)
        else:
            file.physical_width = -1
            file.physical_height = -1
        try:
            file.magnification = wsi.getMagnification()
        except:
            file.magnification = -1
        del wsi

    return render(request, 'slide/view_uploaded_slides.html', {'files': files})


@uploader_required
def edit_slide_metadata(request, slide_id):
    try:
        slide = Slide.objects.get(pk=slide_id)
    except Slide.DoesNotExist:
        return HttpResponseNotFound()

    if request.method == 'POST':
        form = SlideMetadataForm(request.POST, instance=slide)
        if form.is_valid():
            slide = form.save(commit=False)
            organ_tags = form.cleaned_data['organ_tags']
            stain_tags = form.cleaned_data['stain_tags']
            other_tags = form.cleaned_data['other_tags']
            slide.tags.set(organ_tags | stain_tags | other_tags)
            slide.save()
            slide_cache.remove(slide.id) # Have to this to get updated information
            messages.success(request, f'Slide {slide.name} was updated.')
            return redirect('slide:browser')
    else:
        form = SlideMetadataForm(instance=slide)

    return render(request, 'slide/edit_slide_metadata.html', {'form': form, 'slide': slide})

