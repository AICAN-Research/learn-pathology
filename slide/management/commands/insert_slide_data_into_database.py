import os
import csv
import fast
import numpy as np

from django.core.management import BaseCommand
from django.db import transaction

from learnpathology.settings import BASE_DIR
from slide.models import Slide
from slide.views import create_thumbnail
from tag.models import Tag
# from slide.views import create_thumbnail


class NoMatchingFileError(Exception):
    def __init__(self, msg=None):
        if msg is not None:
            self.msg = msg
        else:
            self.msg = "No matching file was found"


# =====================================
#   HELPER FUNCTIONS
# =====================================

def read_csv_file(filename):
    print(f"Reading {filename} as .csv")

    with open(filename, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(
            csvfile, delimiter=';', #quotechar='|',
            skipinitialspace=True,
        )

        data = []
        i = 0
        for row in reader:  # including header row
            data.append([])
            for c in row:
                data[i].append(c)
            i += 1

    return data


def sort_data_by_row(data):
    d = {}
    headers = data[0]
    samples = data[1:]  # skip header
    for i, sample in enumerate(samples):  # For each row
        entry = {}
        for j, header in enumerate(headers):  # Iterate over headers
            entry[str(header)] = sample[j]
        d[i] = entry

    return d


def match_file_name_to_wsi(file_name, slide_folder):
    for fn in os.listdir(slide_folder):
        if fn == file_name:
            #print(f'Found WSI file matching "{file_name}"')
            return os.path.join(slide_folder, fn)

    raise NoMatchingFileError(f"No WSI file matching {file_name} was found")


def match_file_in_subfolder_to_wsi(file_name, slide_folder):
    for folder in os.listdir(slide_folder):
        _path = os.path.join(slide_folder, folder)
        try:
            path_to_slide = match_file_name_to_wsi(file_name, slide_folder=_path)
            return path_to_slide
        except NoMatchingFileError as exc:
            #print(f"No WSI file matching {file_name} was found in path {_path}. Continuing search...")
            continue

    raise NoMatchingFileError(f"No WSI file matching {file_name} was found in subfolders")


# =====================================
#   DJANGO COMMAND
# =====================================

class Command(BaseCommand):
    """

    Usage
    -----
    In the console, use the command:
    ```
    python manage.py insert_slide_data_into_database <path to csv file> <path to WSI folder>
    ```

    If the files belonging to each WSIs are stored in separate folders, use the
    the flag --subfolders to parse these folders when searching for .vsi files:
    ```
    python manage.py insert_slide_data_into_database --subfolders <path to csv file> <path to WSI folder>
    ```

    TODO:
      - Implement tagging of WSIs from csv file
      - Handle WSI already existing in database
      - Handle changing/updating of tags

    """

    help = 'Load slide metadata from CSV file into database and add tags'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('file_path', type=str, help='Path to csv file with slide data')
        parser.add_argument('slide_folder', type=str, help='Path to folder containing WSIs')

        # Named (optional) arguments
        parser.add_argument(
            '-sf', '--subfolders',
            action='store_true',
            help='Flag to use to parse subfolders of "path_folder" '
                 '(e.g. each WSI is stored in its own subfolder)',
        )

    def handle(self, *args, **options):

        file_path = options['file_path']
        slide_folder = options['slide_folder']
        parse_subfolders = options['subfolders']

        data = read_csv_file(file_path)
        data_dict = sort_data_by_row(data)

        thumbnails_dir = os.path.join(BASE_DIR, 'thumbnails')
        new_paths = []
        for key, slide_data in data_dict.items():

            slide_ready = slide_data['Ready']
            if not slide_ready:  # implicit conversion: string-->bool
                continue
            organ = slide_data['organ']
            if len(organ) == 0:  # no data entered --> skip
                continue

            file_name = slide_data['file_name']

            try:
                if parse_subfolders:
                    path_to_slide = match_file_in_subfolder_to_wsi(file_name, slide_folder)
                else:
                    path_to_slide = match_file_name_to_wsi(file_name, slide_folder)
            except NoMatchingFileError as exc:
                print(f"{exc.__class__.__name__}: {exc.msg}")
                continue

            # Check if path_to_slide is a new path
            existing_slide_paths = list(Slide.objects.all().values_list('path', flat=True))

            if (path_to_slide not in existing_slide_paths) \
                    and (path_to_slide not in new_paths):

                # Histology/pathology boolean flag
                if slide_data['histology_pathology'] == 'pathology':
                    is_pathology = True
                elif slide_data['histology_pathology'] == 'histology':
                    is_pathology = False
                else:
                    # Not valid, skip entry
                    continue

                # Insert new slide into database
                with transaction.atomic():
                    slide = Slide(
                        name=slide_data['new_slide_name'],   # get new name from slide_data
                        # name=slide_data['slide_name'],   # get name from slide_data (csv file)
                        path=path_to_slide,
                        description=slide_data['description'],
                        pathology=is_pathology,
                    )
                    slide.save()

                    if path_to_slide.endswith('.vsi'):
                        try:
                            create_thumbnail(slide.id, thumbnails_dir)
                        except Exception as exc:
                            print(exc)

                    new_paths.append(path_to_slide)  # to ensure duplicates aren't added

            else:  # Path already exists, retrieve existing entry
                #try:
                slide = Slide.objects.get(path=path_to_slide)
                # Copy thumbnail.jpg file from data source to project files
                if str(slide.id) + '.jpg' not in os.listdir(thumbnails_dir) \
                        and path_to_slide.endswith('.vsi'):
                    try:
                        create_thumbnail(slide.id, thumbnails_dir)
                    except Exception as exc:
                        print(exc)

                #except Exception as exc:
                #    # TODO: Catch exception if > 1 entry with same path exists
                #    pass

            # ==== Add tags to slide (and to DB where missing) ====
            organ = slide_data['organ']
            stain = slide_data['staining']
            # TODO: Handle other tags
            #other = slide_data['other_tags']

            # Handle tags not existing in the DB yet
            if organ not in list(Tag.objects.filter(is_organ=True).values_list('name', flat=True)):
                tag = Tag(name=organ, is_organ=True, is_stain=False)
                tag.save()
            if stain not in list(Tag.objects.filter(is_stain=True).values_list('name', flat=True)):
                tag = Tag(name=stain, is_organ=False, is_stain=True)
                tag.save()
            # TODO: Handle other tags

            # Retrieve querysets for tags and add to slide
            organ_tag = Tag.objects.filter(name=organ, is_organ=True, is_stain=False)
            stain_tag = Tag.objects.filter(name=stain, is_organ=False, is_stain=True)
            #other_tags = Tag.objects.filter(name=other, is_organ=False, is_stain=False)
            # NB: Overwrites existing Slide-Tag relationships
            slide.tags.set(organ_tag | stain_tag)  # TODO: other_tags
