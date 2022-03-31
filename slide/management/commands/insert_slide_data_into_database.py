import csv
import os
from django.core.management import BaseCommand
from django.db import transaction

from slide.models import Slide
from tag.models import Tag
from slide.views import create_thumbnail


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

    with open(filename, newline='') as csvfile:
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
    for sample in samples:  # For each row
        entry = {}
        for idx, header in enumerate(headers):  # Iterate over headers
            entry[str(header)] = sample[idx]
        d[str(sample[0])] = entry

    return d


def match_file_name_to_wsi(slide_name, slide_folder):
    for filename in os.listdir(slide_folder):
        if filename == slide_name:
            return os.path.join(slide_folder, filename)

    raise NoMatchingFileError(f"No WSI file matching {slide_name} was found")


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

    TODO:
      - Implement tagging of WSIs from csv file
      - Handle WSI already existing in database
      - Handle changing/updating of tags

    """

    help = "Load slide metadata from CSV file into database and add tags"

    def add_arguments(self, parser):
        parser.add_argument("file_path", type=str)
        parser.add_argument("slide_folder", type=str)

    def handle(self, *args, **options):

        file_path = options["file_path"]
        slide_folder = options["slide_folder"]
        data = read_csv_file(file_path)
        data_dict = sort_data_by_row(data)

        new_paths = []
        for file_name, slide_data in data_dict.items():

            try:
                path_to_slide = match_file_name_to_wsi(file_name, slide_folder)
            except NoMatchingFileError as exc:
                print(f"{exc.__class__.__name__}: {exc.msg}")
                continue

            # Check if path_to_slide is a new path
            existing_slide_paths = list(Slide.objects.all().values_list('path', flat=True))

            if (path_to_slide not in existing_slide_paths) \
                    and (path_to_slide not in new_paths):

                if slide_data['is_pathology'] == 'Yes':
                    is_pathology = True
                elif slide_data['is_pathology'] == 'No':
                    is_pathology = False
                else:
                    # Not valid, skip entry
                    continue

                slide_name = slide_data['slide_name']           # get name from slide_data (csv file)
                description = slide_data['description']

                # Insert new slide into database
                with transaction.atomic():
                    slide = Slide(
                        name=slide_name,
                        path=path_to_slide,
                        description=description,
                        pathology=is_pathology,
                    )
                    slide.save()
                    create_thumbnail(slide.id)  # TODO: Generates an error -- fix
                    new_paths.append(path_to_slide)  # to ensure duplicates aren't added

            else:  # Path already exists, retrieve existing entry
                #try:
                slide = Slide.objects.get(path=path_to_slide)
                #except Exception as exc:
                #    # TODO: Catch exception if > 1 entry with same path exists
                #    pass

            # ==== Add tags to slide (and to DB where missing) ====
            organ = slide_data['organ']
            tissue = slide_data['tissue']
            staining = slide_data['staining']

            # Handle tags not existing in the DB yet
            if organ not in list(Tag.objects.filter(is_organ=True).values_list('name', flat=True)):
                tag = Tag(name=organ, is_organ=True, is_tissue=False, is_staining=False)
                tag.save()
            if tissue not in list(Tag.objects.filter(is_tissue=True).values_list('name', flat=True)):
                tag = Tag(name=tissue, is_organ=False, is_tissue=True, is_staining=False)
                tag.save()
            if staining not in list(Tag.objects.filter(is_staining=True).values_list('name', flat=True)):
                tag = Tag(name=staining, is_organ=False, is_tissue=False, is_staining=True)
                tag.save()

            # Retrieve querysets for tags and add to slide
            organ_tag = Tag.objects.filter(name=organ, is_organ=True,
                                           is_tissue=False, is_staining=False)
            tissue_tag = Tag.objects.filter(name=tissue, is_organ=False,
                                            is_tissue=True, is_staining=False)
            staining_tag = Tag.objects.filter(name=staining, is_organ=False,
                                              is_tissue=False, is_staining=True)
            # NB: Overwrites existing Slide-Tag relationships
            slide.tags.set(organ_tag | tissue_tag | staining_tag)
