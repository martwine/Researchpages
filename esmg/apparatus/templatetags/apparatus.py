from django.utils.encoding import smart_unicode
from django import template

register = template.Library()

@register.filter
def id2label(value):
    return smart_unicode(value).replace("_", " ").replace("-", " ").capitalize()
