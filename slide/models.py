import os
from io import BytesIO
import json
import fast
import numpy as np
from PIL import Image
from pathlib import Path
import xml.etree.ElementTree as ET
from django.db import models
from django.conf import settings
from slide.timing import Timer
from tag.models import Tag

if settings.USE_TURBOJPEG:
    from turbojpeg import TurboJPEG, TJPF_RGB
    jpeg = TurboJPEG()


class Slide(models.Model):
    """
    Model for whole slide image
    """
    name = models.CharField(max_length=255)
    path = models.CharField(max_length=1024)
    description = models.TextField()  # short description
    long_description = models.TextField(null=True, blank=True)  # (optional) longer description
    pathology = models.BooleanField(default=False, help_text='Does the slide show pathology or histology')
    tags = models.ManyToManyField(Tag)

    def __str__(self):
        return self.name

    def load_image(self):
        if not hasattr(self, '_image'):
            self.timers = {
                'import': Timer('Importing WSI'),
                'getPatchImage': Timer('getPatchImage function'),
                'sharpening': Timer('Tile sharpening'),
                'conversion': Timer('Tile FAST->NUMPY conversion'),
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

            self.find_image_scale_factor()

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

    @property
    def scale_factor(self):
        """
        Returns the scale factor of the slide (in um/px).

        Note
        ----
        For now only the x scale is returned since this is used for displaying
        the scalebar. If the Slide._scale_factor is to be used for another
        purpose, this function should be updated.

        If Slide._slide_factor is not found (or another error occurs), None
        will be returned and the scalebar will not be displayed.
        """
        self.load_image()
        try:
            return self._scale_factor[0]
        except:
            return None  # Returning None will display slide without scalebar

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
        tile_width = width
        tile_height = height
        if x*width + tile_width >= self._image.getLevelWidth(fast_level):
            tile_width = self._image.getLevelWidth(fast_level) - x*width - 1
        if y*height + tile_height >= self._image.getLevelHeight(fast_level):
            tile_height = self._image.getLevelHeight(fast_level) - y*height - 1

        self.timers['getPatchImage'].start()
        access = self._image.getAccess(fast.ACCESS_READ)
        image = access.getPatchAsImage(fast_level, x*width, y*height, tile_width, tile_height)
        del access # Free access to other threads
        self.timers['getPatchImage'].stop()

        if settings.USE_IMAGE_SHARPENING:
            self.timers['sharpening'].start()
            image = fast.ImageSharpening.create(1.5).connect(image).runAndGetOutputData()
            self.timers['sharpening'].stop()

        # TODO DO we really need this?:
        #if tile_width != self._tile_width or tile_height != self._tile_height:
        #    self.timers['resize'].start()
        #    image = fast.ImageResizer.create(self._tile_width, self._tile_height).connect(image).runAndGetOutputData()
        #    self.timers['resize'].stop()

        self.timers['conversion'].start()
        image = np.asarray(image)
        self.timers['conversion'].stop()

        # Convert PIL image to JPEG byte buffer and send back
        self.timers['jpeg'].start()
        buffer = BytesIO()
        if settings.USE_TURBOJPEG:
            # Use turbo jpeg to compress image since it is quite fast
            buffer.write(jpeg.encode(image, pixel_format=TJPF_RGB, quality=75))
        else:
            # Use pillow to compress which is slow
            tile = Image.fromarray(image, mode='RGB')
            tile.save(buffer, 'jpeg', quality=75)  # TODO Set quality
        self.timers['jpeg'].stop()

        if settings.PRINT_RUNTIME:
            print('Runtimes')
            print('==============================')
            for timer in self.timers.values():
                timer.print()

        return buffer

    def find_image_scale_factor(self):
        """
        Finds the slide scale (in um/px) from the WSI's metadata.xml file.
        The scale is given for the highest level (lowest resolution) of the
        image pyramid.
        """
        try:
            slide_folder = os.path.dirname(self.path)
            path_to_metadata = os.path.join(slide_folder, 'metadata.xml')

            # Parse XML tree
            tree = ET.parse(Path(path_to_metadata))
            root = tree.getroot()

            # Find the scale property
            property_elem = root.find(".//Property[@ID='20007']")   # ImagePlaneScale property
            cdvec2_elem = property_elem.find('CdVec2')
            scale_xy = [float(d.text) for d in cdvec2_elem.findall('double')]

            self._scale_factor = scale_xy   # scale factor in um/px

        except Exception as err:
            print(f"An error occurred: The requested metadata.xml file for {self.path} was not found. Setting scale factor None")
            self._scale_factor = None


class AnnotatedSlide(models.Model):
    """
    Model for an annotated slide.
    A slide can have multiple annotations.
    A task uses an annotated slide.
    """
    slide = models.ForeignKey(Slide, on_delete=models.CASCADE)


class Annotation(models.Model):
    annotated_slide = models.ForeignKey(AnnotatedSlide, on_delete=models.CASCADE)
    json_string = models.TextField(blank=False, help_text='The annotation in W3C format (JSON) stored as a string')

    def deserialize(self):
        return json.loads(self.json_string)

    @property
    def text(self):
        """
        The text/comment of the annotation
        """
        raise NotImplementedError('Annotation property "text" has not been implemented yet')

    @property
    def type(self):
        """
        Human-readable annotation type (point, box, ellipse, ...)
        """
        raise NotImplementedError('Annotation property "type" has not been implemented yet')






