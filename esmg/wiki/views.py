from time import time

from django import newforms as forms
from django.newforms import form_for_model, form_for_instance
from django.utils.encoding import smart_unicode
from django.views.generic.list_detail import object_detail
from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response

from esmg.people.models import Person
from esmg.groups.models import Group
from esmg.wiki.models import *

from afternoon.django.errors.views import error

def wikipageview(request, **kwargs):
    #is this a group wiki?
    group=kwargs.get("group", False)
    if not group:
        #if we want non-group wikis (i.e. top level) put stuff jere
        raise Http404
    try:
        g = Group.objects.get(acronym=group)
    except:
        return error(request, "Couldn't find a group called " + group +". Please check the group name.")

    slug = kwargs.get("slug", False)
    if not slug:
        try:
            wikipage = WikiPage.objects.get(disabled=False, group=g,
                    groupwikihome=True)
        except:
            return HttpResponseRedirect('edit/')
    else:
        try:
            wikipage = WikiPage.objects.get(disabled=False, slug=slug, group=g)
        except:
            return HttpResponseRedirect('edit/')
    if wikipage.read_private and request.user.is_anonymous():
        permission = False
    elif wikipage.read_private:
        permission = request.user.person in g.members()
    else:
        permission = True

    if not permission:
        return error(request, "You do not have the necessary permissions to view this wiki page.")
    
    if wikipage.write_private and not request.user.is_anonymous():
        wpermission = request.user.person in g.members()
    else:
        wpermission = not request.user.is_anonymous()
    try:
        kwargs.delete("slug")
    except:
        pass
    try:
        kwargs.pop("group")
    except:
        pass
    kwargs["queryset"] = WikiPage.objects.filter(group=g)
    kwargs["object_id"] = wikipage.id
    kwargs["extra_context"] = { "group": g, 
                                "logo":g.get_logo_url(),
                                "css":wikipage.get_css(),
                                "edit":wpermission,
                              }
    return object_detail(request, **kwargs)

@login_required
def editwiki(request, **kwargs):
    wikipagecontent=False
    #is this a group wiki?
    group=kwargs.get("group", False)
    if not group:
        #if we want non-group wikis (i.e. top level) put stuff jere
        raise Http404
    try:
        g = Group.objects.get(acronym=group)
    except:
        return error(request, "Couldn't find a group called " + group +". Please check the group name.")

    slug = kwargs.get("slug", False)
    groupwikihome = False
    if not slug:
        slug = ""
        groupwikihome = True
    try:
        wikipage = WikiPage.objects.get(group=g, slug=slug)
        create = False
        try:
            wikipagecontent = wikipage.wpcontent.latest()
        except:
            pass
    except:
        #we're creating a page
        create = True
        wikipage = None
    if create: 
        WikiForm = form_for_model(WikiPage)
        ContentForm = form_for_model(WikiPageContent)
    else:
        WikiForm = form_for_instance(wikipage)
        if wikipagecontent:
            ContentForm = form_for_instance(wikipagecontent)
        else:
            ContentForm = form_for_model(WikiPageContent)

    if request.method == 'POST':
        wform = WikiForm(request.POST)
        wikipage = wform.save(commit=False)
        if not wikipage.id:
            #we're creating not editing
            wikipage.groupwikihome = groupwikihome
            wikipage.slug=slug
            wikipage.group=g
            wikipage.disabled=False
            wikipage.locked_time=0
            wikipage.locked_by=request.user.person
        wikipage.save()
        cform = ContentForm(request.POST)
        content = cform.save(commit=False)
        if content.version:
            new_version = WikiPageContent(page=wikipage)
            new_version.title = content.title
            new_version.body = content.body
            new_version.version = content.version+1
            new_version.last_editor = request.user.person
            new_version.page = wikipage
            new_version.save()
        else:
            content.last_editor = request.user.person
            content.page = wikipage
            content.save()
        return HttpResponseRedirect('../')

    else:
        if not create:
            if not wikipage.locked_by or time() - float(wikipage.locked_time) > 200 or (wikipage.locked_by and wikipage.locked_by == request.user.person):
                wikipage.locked_by = request.user.person
                wikipage.locked_time = int(time())
                wikipage.save()
            else:
                return error(request,"This wiki page is currently being edited by"
                        + smart_unicode(wikipage.locked_by) + ". Please try again \
                        in a few minutes")
        wform = WikiForm()
        cform = ContentForm()
    return render_to_response('wiki/wiki_form.html',
                {
                "create": create,
                "wform": wform,
                "cform": cform,
                "group":g,
                "wikipage":wikipage,
                "logo":g.get_logo_url(),
                })
@login_required
def versions(request, **kwargs):
    group = kwargs.get("group", False)
    if not group:
        #if we want non-group wikis (i.e. top level) put stuff jere
        raise Http404
    try:
        g = Group.objects.get(acronym=group)
    except:
        return error(request, "Couldn't find a group called " + group +". Please check the group name.")

    slug = kwargs.get("slug", False)
    if not slug:
        try:
            wikipage = WikiPage.objects.get(groupwikihome=True, group=g,
                    disabled=False)
        except:
            return error(request, "This group doesn't appear to have a wiki yet.  Why not <a href=\"" + group.get_absolute_url() + "wiki/edit/\">click here</a> to get started on one?")
    else:
        try:
            wikipage = WikiPage.objects.get(group=g, slug=slug, disabled=False)
        except:
            return error(request, "No such wiki page")

    version = kwargs.get("version", False)
    if not version:
        return error(request, "No version specified")
    try:
        wpc = wikipage.wpcontent.get(version=version)
    except WikiPageContent.DoesNotExist:
        return error(request, "No such version")
    
    if (wikipage.write_private and request.user.person in g.members()) or not (wikipage.write_private and request.user.is_anonymous()): 
        if request.method=="POST":
            wpagecontent = WikiPageContent(page=wikipage, title=wpc.title,
                    body=wpc.body, last_editor=request.user.person)
            wpagecontent.save()
            return HttpResponseRedirect('../../')
        else:
            css = wikipage.get_css()
            logo = g.get_logo_url()
            
        return render_to_response('wiki/versionconfirm.html', 
                    {
                    "css":css,
                    "logo":logo,
                    "group":g,
                    "wpc":wpc,
                    })
    else:
        return error(request, "You do not have the appropriate persmissions")
        
            
            
            
