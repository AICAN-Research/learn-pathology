from io import BytesIO
import time
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.conf import settings
from .models import Slide


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


def view_whole_slide(request, slide_id):
    slide = slide_cache.load_slide_to_cache(slide_id)
    return render(request, 'slide/view_wsi.html', {
        'slides': Slide.objects.all(),
        'slide': slide,
    })


def tile(request, slide_id, osd_level, x, y):
    """
    Gets OSD tile from slide, converts to JPEG and sends to client
    """
    slide = slide_cache.get_slide(slide_id)
    try:
        tile = slide.get_osd_tile(osd_level, x, y)
    except Exception as e:
        print(e)
        return HttpResponse(status=404)
    except:
        print('An error occured while loading a tile', osd_level, x, y)
        return HttpResponse(status=404)

    # Convert PIL image to JPEG byte buffer and send back
    if settings.PRINT_RUNTIME:
        start = time.time()
    buffer = BytesIO()
    tile.save(buffer, 'jpeg', quality=75)  # TODO Set quality
    if settings.PRINT_RUNTIME:
        runtime = (time.time() - start)*1000
        print('JPEG conversion took:', runtime, 'ms')
    return HttpResponse(buffer.getvalue(), content_type='image/jpeg')
