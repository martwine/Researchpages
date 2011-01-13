from django import template

from esmg.groups.models import Membership

register = template.Library()

@register.filter(name='get_roles')
def get_roles(person,group):
    bits=[]
    for m in Membership.objects.filter(person=person, group=group):
        bits.append('<p>' + m.role.role + '</p>')
    return "".join(bits)


