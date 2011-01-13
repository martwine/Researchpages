from django import template
from esmg.textify import textify
from esmg.people.models import Person
from django.utils.encoding import smart_unicode

register = template.Library()

def is_manager(group, person):
    return person==group.editor or person==group.project_leader
register.filter('is_manager', is_manager)

def is_group_leader(leader, person):
    return leader.is_group_leader(person) 
register.filter('is_group_leader', is_group_leader)

def dehtmlise(htmlsnippet, maxwords=50):
    return smart_unicode(textify(htmlsnippet, maxwords))
register.filter('dehtmlise', dehtmlise)

def isnt_friend(person,user):
    if person in user.person.friends.all():
        return False
    return True
register.filter('isnt_friend', isnt_friend)

def is_member(group,person):
    if person in Person.objects.filter(membership__group=group):
        return True
    return False
register.filter('is_member', is_member)
