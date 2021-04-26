from io import BytesIO
import time
import PIL.Image
from django.http import HttpResponse, Http404
from django.shortcuts import render
import fast
from PIL import Image
import numpy as np


class SlideCache:
    """
    A class to keep a cache of slides in memory.
    """

    def __init__(self):
        self.slides = {}
        fast.Reporter.setGlobalReportMethod(fast.Reporter.COUT)
        importer = fast.WholeSlideImageImporter.New()
        #importer.setFilename('/home/smistad/FAST/data/WSI/A05.svs')
        importer.setFilename('/home/smistad/Downloads/OS-1.tiff')
        image = importer.updateAndGetOutputImagePyramid()

        # Count how many OSD levels we need: OSD requires that every level is downsampled by a factor of 2
        # TODO This assumes that every level size of WSI in FAST is a multiple of 2
        current_width = image.getFullWidth()
        current_height = image.getFullHeight()
        levels = image.getNrOfLevels()
        smallest_width = image.getLevelWidth(levels-1)
        smallest_height = image.getLevelHeight(levels-1)
        osd_level = 0
        tile_width = 256 #image.getLevelTileWidth(0)
        tile_height = 256 #image.getLevelTileHeight(0)
        osd_tile_width = {0: tile_width}
        osd_tile_height = {0: tile_height}
        osd_to_fast_level_map = {0: 0}
        print('Smallest width', smallest_width)
        while abs(current_width - smallest_width/2) > 1:
            print(osd_level, current_width, current_height)
            current_width /= 2
            current_height /= 2
            osd_level += 1
            # If current_width is closer to previous FAST level width, than the next FAST level width, then use that.
            if osd_to_fast_level_map[osd_level-1] < levels-1 and abs(current_width - image.getLevelWidth(osd_to_fast_level_map[osd_level-1]+1)) < 1:
                osd_tile_width[osd_level] = tile_width
                osd_tile_height[osd_level] = tile_height
                osd_to_fast_level_map[osd_level] = osd_to_fast_level_map[osd_level - 1] + 1
                print('Map to next: ', osd_to_fast_level_map[osd_level])
            else:
                osd_tile_width[osd_level] = osd_tile_width[osd_level-1]*2
                osd_tile_height[osd_level] = osd_tile_height[osd_level-1]*2
                osd_to_fast_level_map[osd_level] = osd_to_fast_level_map[osd_level - 1]
                print('Map to previous', osd_to_fast_level_map[osd_level])
        print('Total OSD levels', osd_level+1)
        self.slides['A05'] = {
            'fast_image_pyramid': image,
            'fast_levels': image.getNrOfLevels(),
            'osd_levels': osd_level+1,
            'osd_to_fast_level': osd_to_fast_level_map,
            'width': image.getFullWidth(),
            'height': image.getFullHeight(),
            'tile_width': tile_width,
            'tile_height': tile_height,
            'osd_tile_width': osd_tile_width,
            'osd_tile_height': osd_tile_height,
        }

    def get_slide(self, slide_name):
        return self.slides[slide_name]

    def get_tile(self, slide_name, level, x, y, width, height):
        slide = self.slides[slide_name]['fast_image_pyramid']
        access = slide.getAccess(fast.ACCESS_READ)
        tile_width = width
        tile_height = height
        if x*width + tile_width >= slide.getLevelWidth(level):
            tile_width = slide.getLevelWidth(level) - x*width - 1
        if y*height + tile_height >= slide.getLevelHeight(level):
            tile_height = slide.getLevelHeight(level) - y*height - 1

        start = time.time()
        image = access.getPatchAsImage(level, x*width, y*height, tile_width, tile_height)
        runtime = (time.time() - start) * 1000
        print('getPatchAsImage took:', runtime, 'ms')

        start = time.time()
        sharpening = fast.ImageSharpening.New()
        sharpening.setStandardDeviation(1.5)
        sharpening.setInputData(image)
        image = sharpening.updateAndGetOutputImage()
        runtime = (time.time() - start) * 1000
        print('Sharpening took:', runtime, 'ms')

        #tileAccess = image.getImageAccess(fast.ACCESS_READ)
        #return Image.frombytes(size=(tile_width, tile_height), data=tileAccess.get(), mode='RGB')

        # TODO get rid of asarray conversion, and read directly from bytes instead somehow
        start = time.time()
        image = np.asarray(image)
        pil_image = Image.fromarray(image, mode='RGB')
        runtime = (time.time() - start) * 1000
        print('FAST->numpy->PIL took:', runtime, 'ms')
        return pil_image


slide_cache = SlideCache()

def view_wsi(request):
    slide = slide_cache.get_slide('A05')
    return render(request, 'viewer/index.html', {
        'levels': slide['osd_levels'],
        'width': slide['width'],
        'height': slide['height'],
        'tile_width': slide['tile_width'],
        'tile_height': slide['tile_height'],
    })


def tile(request, level, x, y):
    # Go from OSD level to FAST level
    slide = slide_cache.get_slide('A05')
    fast_level = slide['osd_to_fast_level'][level]
    width = slide['osd_tile_width'][level]
    height = slide['osd_tile_height'][level]
    target_width = slide['tile_width']
    target_height = slide['tile_height']
    try:
        tile = slide_cache.get_tile('A05', fast_level, x, y, width, height)
        if tile.width != target_width: # TODO What about edges cases here.
            start = time.time()
            tile.thumbnail((target_height, target_width), resample=PIL.Image.BILINEAR)
            runtime = (time.time() - start) * 1000
            print('Resize took:', runtime, 'ms')
    except Exception as e:
        print(e)
        return HttpResponse(status=404)
    except:
        print('An error occured while loading a tile', level, x, y, width, height)
        return HttpResponse(status=404)

    print(fast_level, level, x, y, tile.width, tile.height)
    # Convert PIL image to JPEG byte buffer and send back
    start = time.time()
    buffer = BytesIO()
    tile.save(buffer, 'jpeg') # Set quality
    runtime = (time.time() - start)*1000
    print('JPEG conversion took:', runtime, 'ms')
    return HttpResponse(buffer.getvalue(), content_type='image/jpeg')
