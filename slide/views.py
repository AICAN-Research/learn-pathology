from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect
from django.conf import settings
from user.decorators import student_required, teacher_required
from .models import Slide, SlideForm


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
    return render(request, 'slide/index.html', {
        'slides': Slide.objects.all(),
    })


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
        form = SlideForm(request.POST)
        if form.is_valid():
            # Save form and create thumbnail
            slide = form.save()
            create_thumbnail(slide.id)
            # TODO add success message
            return redirect('slide:view_full', slide.id)
    else:
        form = SlideForm()

    return render(request, 'slide/add.html', {'form': form})
