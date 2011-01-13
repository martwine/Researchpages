from django import template

from esmg.groups.models import Membership

register = template.Library()

@register.filter(name='get_other_groups')
def get_other_groups(person,group):
    if group:
        return person.membership_set.exclude(group=group)
    else:
        return person.membership_set.all()

@register.filter(name='count_other_groups')
def count_other_groups(person,group):
    if group:
        return person.membership_set.exclude(group=group).count()
    else:
        return person.membership_set.all().count()


@register.filter(name='get_role')
def get_role(person,group):
    bits=[]
    for m in Membership.objects.filter(person=person, group=group):
        bits.append(m.role.role)
    return "".join(bits)


