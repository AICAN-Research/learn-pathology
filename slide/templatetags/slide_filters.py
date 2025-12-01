import django.db.models
from django import template
from math import ceil


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
def get_pixels_per_meter(slide):
    if slide.scale_factor is None:
        return 0    # Setting pixelsPerMeter to 0 will hide scalebar
    return 1./(slide.scale_factor/1000.)  # FAST returns in mm, need in meter
