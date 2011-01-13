from django.utils.encoding import smart_unicode
from django import template

register = template.Library()

@register.filter
def has_viewable_entries(resources,user=None):
    count = 0
    if not user.is_anonymous():
        p = user.person
    else:
        user = False
    for resource in resources:
        if resource.permissions == 'pblc':
            count = count + 1
        elif resource.permissions == 'rstrc' and user:
            count = count + 1
        elif resource.permissions == 'prvt' and user: 
            if (p == resource.person or resource.group in p.groups()):
                count = count + 1
    if count > 0:
        return True
    return False
