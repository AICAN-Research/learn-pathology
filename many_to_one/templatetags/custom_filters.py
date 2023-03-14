import django.db.models
from django import template
from math import ceil


register = template.Library()


# @register.filter
# def get_form_by_prefix(formset, prefix):
#     return next(form for form in formset.forms if form.prefix == prefix)
#
# @register.filter
# def make_list(num):
#     return range(1, int(num) + 1)
#
