import django.db.models
from django import template
from math import ceil
import xml.etree.ElementTree as ET
from pathlib import Path
import os


register = template.Library()


@register.filter
def to_range(number):
    return range(number)


@register.filter
def index(indexable, idx):
    if isinstance(indexable, django.db.models.QuerySet):
        indexable = list(indexable)
    return indexable[idx]


@register.filter
def get(queryset, item_id):
    return queryset.get(item_id)


@register.filter
def as_chunks(indexable, chunk_size):
    if isinstance(indexable, django.db.models.QuerySet):
        indexable = list(indexable)
    limit = ceil(len(indexable) / chunk_size)
    for idx in range(limit):
        yield indexable[chunk_size*idx:chunk_size*(idx+1)]


@register.filter
def model_name(model):
    return model.__class__.__name__


@register.filter
def get_scale(slide):
    slide_folder = os.path.dirname(slide.path)
    path_to_metadata = os.path.join(slide_folder, 'metadata.xml')

    tree = ET.parse(Path(path_to_metadata))
    root = tree.getroot()

    property_elem = root.find(".//Property[@ID='20007']")
    cdvec2_elem = property_elem.find('CdVec2')
    values = [float(d.text) for d in cdvec2_elem.findall('double')]
    return values[0]
