import threading
from io import BytesIO
from django.db import models
import fast
import time
import numpy as np
from PIL import Image
from django.conf import settings
from slide.timing import Timer
from tag.models import Tag


class Slide(models.Model):
    """
    Model for whole slide image
    """
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=1024)
    description = models.TextField()  # short description
    long_description = models.TextField(null=True, blank=True)  # (optional) longer description
    pathology = models.BooleanField(default=False, help_text='Does the slide show pathology or not')
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.name

    def load_image(self):
        if not hasattr(self, '_image'):
            self.timers = {
                'import': Timer('Importing WSI'),
                'getPatchImage': Timer('getPatchImage function'),
                'sharpening': Timer('Tile sharpening'),
                'conversion': Timer('Tile FAST->PIL conversion'),
                'resize': Timer('Tile resize'),
                'jpeg': Timer('JPEG Conversion'),
            }

            self.timers['import'].start()
            importer = fast.WholeSlideImageImporter.create(self.path)
            try:
                image = importer.runAndGetOutputData()
            except:
                raise RuntimeError('Failed to load slide image pyramid from ' + self.path)
            self._image = image
            self.timers['import'].stop()

            # Count how many OSD levels we need: OSD requires that every level is downsampled by a factor of 2
            # TODO This assumes that every level size of WSI in FAST is a multiple of 2
            current_width = image.getFullWidth()
            current_height = image.getFullHeight()
            levels = image.getNrOfLevels()
            smallest_width = image.getLevelWidth(levels-1)
            smallest_height = image.getLevelHeight(levels-1)
            osd_level = 0
            tile_width = 256
            tile_height = 256
            if self.path.endswith('.vsi'):  # TODO Hack for now
                tile_width = image.getLevelTileWidth(0)
                tile_height = image.getLevelTileHeight(0)
            osd_tile_width = {0: tile_width}
            osd_tile_height = {0: tile_height}
            osd_to_fast_level_map = {0: 0}
            print('Smallest width', smallest_width)
            while abs(current_width - smallest_width/2) > 1:

                current_width = int(current_width/2)
                current_height = int(current_height/2)
                #if self.path.endswith('.vsi'): # TODO Hack for now
                #    current_width += current_width % tile_width
                #    current_height += current_height % tile_height
                osd_level += 1
                # If current_width is closer to previous FAST level width, than the next FAST level width, then use that.
                if osd_to_fast_level_map[osd_level-1] < levels-1 and abs(current_width - image.getLevelWidth(osd_to_fast_level_map[osd_level-1]+1)) < 1:
                    osd_tile_width[osd_level] = tile_width
                    osd_tile_height[osd_level] = tile_height
                    osd_to_fast_level_map[osd_level] = osd_to_fast_level_map[osd_level - 1] + 1

                else:
                    osd_tile_width[osd_level] = osd_tile_width[osd_level-1]*2
                    osd_tile_height[osd_level] = osd_tile_height[osd_level-1]*2
                    osd_to_fast_level_map[osd_level] = osd_to_fast_level_map[osd_level - 1]

                if current_width < 1024:
                    break

            self._fast_levels = image.getNrOfLevels()
            self._osd_levels = osd_level+1
            self._width = image.getFullWidth()
            self._height = image.getFullHeight()
            self._tile_width = tile_width
            self._tile_height = tile_height
            self._osd_tile_width = osd_tile_width
            self._osd_tile_height = osd_tile_height
            self._osd_to_fast_level = osd_to_fast_level_map

            self.get_scale_factor()

    @property
    def image(self):
        self.load_image()
        return self._image

    @property
    def width(self):
        self.load_image()
        return self._width

    @property
    def height(self):
        self.load_image()
        return self._height

    @property
    def osd_levels(self):
        self.load_image()
        return self._osd_levels

    @property
    def tile_width(self):
        self.load_image()
        return self._tile_width

    @property
    def tile_height(self):
        self.load_image()
        return self._tile_height

    def get_fast_level(self, osd_level):
        """
        Get FAST image pyramid level from OSD level
        """
        self.load_image()
        return self._osd_to_fast_level[osd_level]

    def get_osd_tile_size(self, osd_level):
        self.load_image()
        return self._osd_tile_width[osd_level], self._osd_tile_height[osd_level]

    def get_fast_tile_size(self):
        self.load_image()
        return self._tile_width, self._tile_height

    def get_osd_tile_as_buffer(self, osd_level, x, y):
        fast_level = self.get_fast_level(osd_level)
        width, height = self.get_osd_tile_size(osd_level)
        access = self._image.getAccess(fast.ACCESS_READ)
        tile_width = width
        tile_height = height
        if x*width + tile_width >= self._image.getLevelWidth(fast_level):
            tile_width = self._image.getLevelWidth(fast_level) - x*width - 1
        if y*height + tile_height >= self._image.getLevelHeight(fast_level):
            tile_height = self._image.getLevelHeight(fast_level) - y*height - 1

        self.timers['getPatchImage'].start()
        image = access.getPatchAsImage(fast_level, x*width, y*height, tile_width, tile_height)
        self.timers['getPatchImage'].stop()

        self.timers['sharpening'].start()
        sharpening = fast.ImageSharpening.create(1.5).connect(image)
        image = sharpening.runAndGetOutputData()
        self.timers['sharpening'].stop()

        #tileAccess = image.getImageAccess(fast.ACCESS_READ)
        #return Image.frombytes(size=(tile_width, tile_height), data=tileAccess.get(), mode='RGB')

        # TODO get rid of asarray conversion, and read directly from bytes instead somehow
        self.timers['conversion'].start()
        image = np.asarray(image)
        tile = Image.fromarray(image, mode='RGB')
        self.timers['conversion'].stop()

        if tile.width != self._tile_width: # TODO What about edges cases here.
            self.timers['resize'].start()
            tile.thumbnail((self._tile_height, self._tile_width), resample=Image.BICUBIC)
            self.timers['resize'].stop()

        # Convert PIL image to JPEG byte buffer and send back
        self.timers['jpeg'].start()
        buffer = BytesIO()
        tile.save(buffer, 'jpeg', quality=75)  # TODO Set quality
        self.timers['jpeg'].stop()

        if settings.PRINT_RUNTIME:
            print('Runtimes')
            print('==============================')
            for timer in self.timers.values():
                timer.print()

        return buffer

    def get_scale_factor(self):
        #TODO Implement

        self.scale_factor = None


class AnnotatedSlide(models.Model):
    """
    Model for an annotated slide.
    A slide can have multiple annotations.
    A task uses an annotated slide.
    """
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE)

    def get_html(self):
        """
        Get HTML for all annotations
        """
        html = ''
        for pointer in Pointer.objects.filter(annotated_slide=self):
            html += pointer.get_html()
        for bb in BoundingBox.objects.filter(annotated_slide=self):
            html += bb.get_html()
        return html

    def get_js(self):
        """
        Get JS for all annotations
        """
        js = ''
        for pointer in Pointer.objects.filter(annotated_slide=self):
            js += pointer.get_js()
        for bb in BoundingBox.objects.filter(annotated_slide=self):
            js += bb.get_js()
        return js


class Pointer(models.Model):
    """
    A pointer on a slide consisting of a position (x,y) and a text
    """
    annotated_slide = models.ForeignKey(AnnotatedSlide, on_delete=models.CASCADE)
    position_x = models.FloatField()
    position_y = models.FloatField()
    text = models.CharField(max_length=256)

    class Meta:
        unique_together = [
            ['annotated_slide', 'position_x', 'position_y', 'text']
        ]

    def get_html(self):
        html = ''
        # Add pointer container
        html += f'<div id="right-arrow-overlay-{self.id}" class="overlay transparentBackground border-0">' \
                f'&#x2192; ' \
                f'</div>'
        html += f'<div id="arrow-text-overlay-{self.id}" class=" textOverlay border-primary"> ' \
                f'{self.text}</div>'
        return html

    def get_js(self):
        js = ''
        # Add arrow
        js += f"{{" \
             f"id: 'right-arrow-overlay-{self.id}'," \
             f"x: {self.position_x}," \
             f"y: {self.position_y}," \
             f"placement: 'RIGHT'," \
             f"checkResize: false" \
             f"}},"
        # Add text
        js += f"{{" \
             f"id: 'arrow-text-overlay-{self.id}'," \
             f"x: {self.position_x}," \
             f"y: {self.position_y}," \
             f"placement: 'RIGHT'," \
             f"checkResize: false," \
              f"}},"
        return js


class BoundingBox(models.Model):
    """
    A bounding box annotation on a slide consisting of a top/bottom left
    position (x,y), width and height, and a text.
    """


    annotated_slide = models.ForeignKey(AnnotatedSlide, on_delete=models.CASCADE)
    position_x = models.FloatField()
    position_y = models.FloatField()
    width = models.FloatField()
    height = models.FloatField()
    text = models.CharField(max_length=256)

    class Meta:
        unique_together = [
            ['annotated_slide', 'position_x', 'position_y', 'width', 'height', 'text']
        ]

    def get_html(self):
        html=''
        html += f'<div id="boundingbox-{self.id}" class="overlay"><div </div>'
        print('Got BoundingBox html')

        html += f'<div id="boundingbox-text-overlay-{self.id}" ><div class="textOverlay"' \
                f'>{self.text}</div></div>'
        print('Got BoundingBox Text html')
        return html

    def get_js(self):
        js = ''
        js += f"{{" \
             f"id: 'boundingbox-{self.id}', " \
             f"x: {self.position_x}, " \
             f"y: {self.position_y}, " \
             f"width: {self.width}, " \
             f"height: {self.height}, " \
             f"placement: 'TOPLEFT', " \
             f"checkResize: true, " \
             f"className: 'card LPBoundingBox' }},"

        js += f"{{" \
              f"id: 'boundingbox-text-overlay-{self.id}', " \
              f"x: {self.position_x}, " \
              f"y: {self.position_y}, " \
              f"placement: 'TOPLEFT', " \
              f"checkResize: true, " \
              f"}},"
        print('Got BoundingBox js')
        return js
