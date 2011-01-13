from django import template

register = template.Library()

def truncatemid(value, arg):
    n = int(arg)
    if len(value) < 2*n + 3:
        return value
    else:
        return value[:n] + "..." + value[-n:]
        
register.filter('truncatemid',truncatemid)

def get_link_html(person, group):
    if person.membership_set.filter(group=group).count() != 0:
        return '<a href="' + group.get_absolute_url() + '/people/' + person.slug + '"/>'
    else:
        return '<a href="' + person.get_absolute_url() + '"/>'
register.filter('get_link_html', get_link_html)
