import Image

from django.utils.encoding import smart_unicode
from django import forms
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect

from esmg.resources.models import Resource, RESOURCE_TYPE_CHOICES, RESOURCE_PERMISSION_CHOICES
from esmg.people.models import Person
from esmg.groups.models import Group
from esmg.apparatus.models import Tree, Page

from afternoon.views.generic.list_detail import object_list
from afternoon.django.errors.views import error


def info(request, object_id):
    r = get_object_or_404(Resource, id=object_id)
    
    ctx = {"object": r}

    if r.type == "pic":
        try:
            i = Image.open(settings.MEDIA_ROOT + r.file)
            i.thumbnail((320, 240))
            ctx["image_width"], ctx["image_height"] = i.size
        except IOError:
            pass
    
    return render_to_response("resources/resource_info.html", ctx,
        RequestContext(request))

def list(request, **kwargs):
    #find out type and get base list
    type = kwargs["type"]
    list = Resource.objects.exclude(file="")
    group = kwargs.get("group", False)
    if group:
            g = Group.objects.get(acronym=group)
    if type == 'group_list':
        logo = g.get_logo_url()
        list = list.filter(group=g)
        person = None
        css=g.defaultcss
        children = Page.objects.get(is_tree_top=True,
                tree__group=g).child_set.all()
    elif type == 'person_list':
        person = Person.objects.get(slug=kwargs["slug"])
        list = list.filter(person=person)            
        if not group:
            g = None
            logo = settings.DEFAULT_LOGO
            css = person.get_css()
        else:
            logo = g.get_logo_url
            css = g.defaultcss
        children = Page.objects.get(is_tree_top=True,
                tree__person=person).child_set.filter(disabled=False)
    else:
        pass
        css = settings.DEFAULT_CSS
        g = None
        person = None
        chilren = None
        logo = settings.DEFAULT_LOGO
    
    if type == 'popup_list':
        popup=True
        list = request.user.person.get_resources()
            
    else:
        popup=False
        
    #from list, find those objects which the current user is allowed to see
    #u = request.user
    #results = []
    #for l in list:
    #    if l.is_viewable(u, type, group, person):
    #        results.append(l)
    if group and not request.user.is_anonymous():
        #make sure person is a group member for piravte resources
        grouptest = g.membership_set.filter(person=request.user.person).count() > 0
    else:
        grouptest = False
   
    if not person:
        person = False

    def needs_updating(resource):
        valid_types=['apos','bpre','cdoc','ddat','epic','fres']
        if not resource.type in valid_types:
            return True
        return False

    def update_type(resource):
        if resource.type == 'pos':
            resource.type = 'apos'
        elif resource.type == 'pre':
            resource.type = 'bpre'
        elif resource.type == 'doc':
            resource.type = 'cdoc'
        elif resource.type == 'dat':
            resource.type = 'ddat'
        elif resource.type == 'pic':
            resource.type = 'epic'
        else:
            resource.type = 'fres'
        resource.save()
    # fix list types if they haven't been already
    for resource in list:
        if needs_updating(resource):
            update_type(resource)

    kwargs["queryset"] = list
    kwargs["allow_empty"] = True
    kwargs["paginate_by"] = 25
    del kwargs["type"]
    try:
        del kwargs["group"]
    except: 
        pass
    try:
        del kwargs["slug"]
    except:
            pass

    if popup:
        kwargs["template_name"] = 'resources/popup_list.html'
    
    kwargs["extra_context"] = {"group": g, "logo": logo, "css":css, "grouptest": grouptest, 
                "person": person}
    return object_list(request, **kwargs)    
        
        
def delete_resource(request, **kwargs):
    if request.user.is_anonymous():
        return HttpResponseRedirect(settings.URLBASE +'/accouns/login/')
    object_id = kwargs.get("object_id", False)
    person = request.user.person
    membership = person.membership_set.all()
    resource = Resource.objects.get(id=object_id)
    if resource.group:
        group_ed = person == resource.group.editor
    else:
        group_ed = False
    if not (group_ed or person == resource.person):
        return error(request, "You do not have the appropriate permissions \
                to edit this resource")
    if request.POST:
        new_data=request.POST.copy()
        #do we really want to delete?
        if new_data['submit']=='Confirm':
            resource.delete()
        return HttpResponseRedirect('../../')
    else:
        return render_to_response('resources/deleteform.html',
                {'resource':resource,},RequestContext(request))
            
    
def create_resource(request, **kwargs):
    if request.user.is_anonymous():
        return HttpResponseRedirect(settings.URLBASE +'/accouns/login/')
    object_id = kwargs.get("object_id", False)
    edit = kwargs.get("edit", False)
    person = request.user.person
    membership = person.membership_set.all()
    if edit:
        manipulator = Resource.ChangeManipulator(object_id)
        resource = manipulator.original_object
        if resource.group:
            group_ed = person == resource.group.editor
        else:
            group_ed = False
        if not (group_ed or person == resource.person):
            return error(request, "You do not have the appropriate permissions \
                    to edit this resource")
        
    else:
        manipulator = Resource.AddManipulator()
        resource = False
    if request.POST:
        if object_id:
            del kwargs["object_id"]
        if edit:
            del kwargs["edit"]
        new_data = request.POST.copy()
        new_data.update(request.FILES)
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            new_resource = manipulator.save(new_data)
            return HttpResponseRedirect(settings.URLBASE + '/resources/' + \
                    smart_unicode(new_resource.id) + '/info')
    else:
        errors = {}
        if edit:
            new_data = manipulator.flatten_data()
        else:
            new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('resources/resource_form.html', {'form': form,
            'css':settings.DEFAULT_CSS, 'membership':membership, 'edit':edit,
            'resource':resource},RequestContext(request))
