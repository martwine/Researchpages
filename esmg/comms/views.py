from django import newforms as forms
from django.newforms import form_for_model, widgets, form_for_instance
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponseRedirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

from esmg.people.models import Person
from esmg.groups.models import Group
from esmg.comms.models import Item, Comment, Notification

from afternoon.views.generic.list_detail import object_list, object_detail
from afternoon.django.errors.views import error

ItemForm = form_for_model(Item)
CommentForm = form_for_model(Comment)

class RecipientsForm(forms.Form):
    def __init__(self, post, ms=None, p=None):
        super(RecipientsForm, self).__init__(post)
        gquery = Group.objects.filter(membership__in=ms) if ms else Group.objects.all()
        gchoices = [(g.id,unicode(g)) for g in gquery]
        if p and p.user.is_superuser:
            gchoices.append(('everyone','All site members'))
        if p:
            pquery = p.friends.all()
        else:
            pquery = []
        pchoices = [(p.user_id,unicode(p)) for p in pquery]
        self.fields['friends'].choices=pchoices
        self.fields['groups'].choices=gchoices
    groups = forms.MultipleChoiceField(choices=(), required=False)
    friends = forms.MultipleChoiceField(choices=(), required=False)

class MessageForm(forms.Form):
    title = forms.CharField(required=True)
    body = forms.CharField(widget=forms.Textarea(), required=True) 
    

NEWSEVENT_PERMISSION_CHOICES = (
    ('prvt', 'Private - visible only to group members'),
    ('pblc', 'Public - visible to everyone'),
)

BLOG_PERMISSION_CHOICES = (
    ('prvt', 'Private - visible only to you'),
    ('rstrc', 'Restricted - Visible only to people connected to you i.e. friends and group members'),
    ('pblc', 'Public - visible to everyone'),
)

def deleteitem(request, **kwargs):
    """added to stop django complaining. Something to actually implement in the
    future perhaps?"""
    return error(request,"This feature isn't yet available. Try again soon.")

def group_overlap(p1,p2):
    if p1 and p2:
        m1 = p1.membership_set.all()
        m2 = p2.membership_set.all()
        s1 = set([x.group.acronym for x in m1])
        s2 = set([x.group.acronym for x in m2])
        intersection = list(s1&s2)
        if len(intersection)>0:
            return True
    else:
        return False

def itemtest(item,person,type):
    if person:
        if item.permissions == 'prvt':
            return item.person == person or type=="group" and person.membership_set.filter(group=item.group) > 0
        elif item.permissions == 'rstrc':
            return item.person == person or person in item.person.friends.all() or group_overlap(item.person,person)
        else:
            return True
    else:
        if item.permissions == 'pblc':
            return True
        else:
            return False
    
def itemlist(request, **kwargs):
    #what type of items are we looking at?
    type = kwargs.get("type", False)
    #are these associated with a group?
    group = kwargs.get("group", False)
    #or is this a poersonal blog?
    person = kwargs.get("slug", False)
    
    grouptest=False
    persontest=False
   
    if person:
        p = Person.objects.get(slug=person)
        list = Item.objects.filter(person=p)
        titletype="Blog"
        if not group:
            g = None
            logo = settings.DEFAULT_LOGO
            css = p.get_css()
    if group:
        g = Group.objects.get(acronym=group)
        logo = g.get_logo_url()
        css = g.defaultcss
        if not person:
            p = None
            list  = Item.objects.filter(group=g)
            if type == "newsblog":
                list = list.filter(type="News")
                titletype="News"
            else:
                list = list.filter(type="Event")
                titletype="Events"
                
    #filter list based on permisions settings 
    if request.user.is_anonymous():
        list = list.filter(permissions="pblc")
    #supersuer can see evrything
    elif request.user.is_staff or request.user.is_superuser:
        if request.user.person == p:
            persontest=True
        if group and (not person) and request.user.person.membership_set.filter(group=g).count() > 0:
            grouptest=True
    #if group news / events there is no 'restricted' permissions option - only
    #private or public. To view private you must be member if group
    elif group and not person:
        if request.user.person.membership_set.filter(group=g).count() > 0:
            grouptest=True
        else:
            list = list.filter(permissions="pblc")
    #in the case of personal blogs things are a little more complicated:
    else:
        #if you're looking at your own blog you can see everything
        if request.user.person == p:
            persontest=True
        #do some tests to determine whether you're an 'associate' of the person
        #who's blog you're looking at:
        elif request.user.person in p.friends.all() or group_overlap(request.user.person,p):
            list = list.exclude(permissions="prvt")
        else:
            list = list.filter(permissions="pblc")

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
    
    kwargs["extra_context"] = {"group":g, "logo":logo, "css":css, "person":p,
        "type":titletype, "persontest":persontest, "grouptest":grouptest,}
    return object_list(request, **kwargs)

@login_required
def notificationdetail(request, **kwargs):
    object_id = kwargs.get("object_id",False)
    if not object_id:
            return error(request, "Couldn't find item, please go back and try again") 
    try:
        note = Notification.objects.get(id=object_id)
    except: 
        return error(request, "No such item. Please go back and try again")
    if not request.user in note.recipients.all():
        return error(request, "Sorry, you are not an authorsied recipient of this message")
    note.unread_recipients.remove(request.user)
    kwargs['queryset'] = Notification.objects.all()
    kwargs["extra_context"] = {"logo":settings.DEFAULT_LOGO}
    return object_detail(request,**kwargs)

@login_required
def messages(request, **kwargs):
    recipient = request.user
    person = request.user.person
    n = Notification.objects.filter(notification_type="Message")
    unread = n.filter(unread_recipients=recipient)
    read = n.filter(recipients=recipient)
    message_count = read.count() + unread.count() > 0
    
    return render_to_response('comms/message_list.html',
            {'messagecount':message_count, 'unread': unread, 'read': read,
            'person':person, 'logo':settings.DEFAULT_LOGO}, 
           RequestContext(request)) 

@login_required
def send_message(request, **kwargs):
    from esmg.groups.models import Membership
    from esmg.comms.models import send_notification
    sender = request.user.person
    ms = sender.membership_set.all()
    if request.method== 'POST':
        recipient_form = RecipientsForm(request.POST, ms, sender)
        message_form = MessageForm(request.POST)
        if message_form.is_valid() and recipient_form.is_valid():
            grouplist = recipient_form.cleaned_data['groups']
            friendlist = recipient_form.cleaned_data['friends']
            if 'everyone' in grouplist:
                recipients = Person.objects.all()
            elif grouplist == [] and friendlist == []:
                recipients = Person.objects.none()
            else:
                groups = Group.objects.filter(id__in=grouplist)
                membship = Membership.objects.filter(group__in=groups)
                grecipients = Person.objects.filter(membership__in=membship) 
            
                frecipients = Person.objects.filter(user__id__in=friendlist)

                recipients = grecipients.__or__(frecipients).distinct()
            
            title = message_form.cleaned_data['title']
            body = message_form.cleaned_data['body']
            
            send_notification(unicode(sender),unicode(sender.email), "Message",
                    recipients, recipients, title, body, settings.URLBASE +
                    "/messages",True)
            
            return HttpResponseRedirect('../')
        
    else:
        recipient_form = RecipientsForm(request.POST, ms, sender)
        message_form = MessageForm()
    
    logo = settings.DEFAULT_LOGO
    
    return render_to_response('comms/message_form.html',
            {
            'rform': recipient_form,
            'mform': message_form,
            'logo':logo,
            'person':sender,},
            RequestContext(request))


        
def itemdetail(request, **kwargs):
    group = kwargs.get("group", False)
    person = kwargs.get("slug", False)
    type = kwargs.get("type", False)
    form = False
    object_id = kwargs.get("object_id",False)
    if not object_id:
            return error(request, "Couldn't find item, please go back and try again") 
    try:
        item = Item.objects.get(id=object_id)
    except:
        return error(request, "Sorry, no such item exists")
    if request.user.is_anonymous():
        testperson = None
    else: testperson = request.user.person
    type = ''
    if group:
        type = "group"
    if itemtest(item,testperson,type):
        kwargs["queryset"] = Item.objects.all()
        if person:
            p = Person.objects.get(slug=person)
            if not item in Item.objects.filter(person=p):
                return error(request, "Sorry, no such item exists")
            titletype = "Blog"
            if not group:
                g = None
                logo = settings.DEFAULT_LOGO
                css = p.get_css()
        if group:
            g = Group.objects.get(acronym=group)
            logo = g.get_logo_url()
            css = g.defaultcss
            if not person:
                if not item in Item.objects.filter(group=g):
                    return error(request, "Sorry, no such item exists")
                p = None
                if type == "newsblog":
                    titletype = "News"
                else:
                    titletype = "Events"
        del kwargs["type"]
        try:
            del kwargs["group"]
        except:
            pass
        try:
            del kwargs["slug"]
        except:
            pass
        editlink = False
        if item.is_item_editor(request.user):
            editlink = True
        if not request.user.is_anonymous():    
            if request.method == 'POST':
                form = CommentForm(request.POST)
                if form.is_valid():
                    new_comment = form.save(commit=False)
                    new_comment.person = request.user.person
                    new_comment.item = item
                    new_comment.save()
                    form = CommentForm()
            else:
                form = CommentForm()
        kwargs["extra_context"] = {"form":form, "css":css, "group":g, "person":p,"logo":logo,
            "type":titletype, "editlink": editlink}
        return object_detail(request, **kwargs)
    else:
        return error(request, "You do not have the apropriate permissions to view this item")
        
        

@login_required
def postitem(request, **kwargs):
    type = kwargs.get("type", False)
    group = kwargs.get("group", False)
    person = kwargs.get("slug", False)

    if person:
        p = Person.objects.get(slug=person)
        if not (request.user.person == p or request.user.is_superuser):
            return error(request, "You do not have the appropriate permissions to add an item here") 
        titletype="Blog"
        ItemForm.base_fields['permissions'].widget = widgets.Select(choices=BLOG_PERMISSION_CHOICES)
        if not group:
            g = None
            logo = settings.DEFAULT_LOGO
            css = p.get_css()
    if group:
        g = Group.objects.get(acronym=group)
        if not request.user.person.membership_set.filter(group=g).count() > 0:
            return error(request, "You do not have the appropriate permissions to add an item here") 
        logo = g.get_logo_url()
        css = g.defaultcss
        if not person:
            ItemForm.base_fields['permissions'].widget = widgets.Select(choices=NEWSEVENT_PERMISSION_CHOICES)
            p = None
            if type == "newsblog":
                titletype="News"
            else:
                titletype="Event"
    
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.type = titletype
            if titletype == "News" or titletype == "Event":
                new_item.group = g
            else:
                new_item.person = p
            new_item.creator = request.user.person
            new_item.save()
            return HttpResponseRedirect('../')
    else:
        form = ItemForm()
    
    del kwargs["type"]
    try:
        del kwargs["group"]
    except:
        pass
    try:
        del kwargs["slug"]
    except:
        pass
    

    return render_to_response('comms/item_form.html',{"group":g, "logo":logo, "css":css, "person":p,
        "type":titletype, "form":form,} )

    
@login_required
def edititem(request, **kwargs):
    type = kwargs.get("type", False)
    group = kwargs.get("group", False)
    person = kwargs.get("slug", False)
    object_id = kwargs.get("object_id",False)
    item = Item.objects.get(id=object_id)
    ItemInstanceForm = form_for_instance(item)

    if person:
        p = Person.objects.get(slug=person)
        if not item.is_item_editor(request.user):
            return error(request, "You do not have the appropriate permissions to edit this item") 
        titletype="Blog"
        ItemInstanceForm.base_fields['permissions'].widget = widgets.Select(choices=BLOG_PERMISSION_CHOICES)
        if not group:
            g = None
            logo = settings.DEFAULT_LOGO
            css = p.get_css()
    if group:
        g = Group.objects.get(acronym=group)
        if not item.is_item_editor(request.user):
            return error(request, "You do not have the appropriate permissions to edit this item") 
        logo = g.get_logo_url()
        css = g.defaultcss
        if not person:
            ItemInstanceForm.base_fields['permissions'].widget = widgets.Select(choices=NEWSEVENT_PERMISSION_CHOICES)
            p = None
            if type == "newsblog":
                titletype="News"
            else:
                titletype="Event"
    
    if request.method == 'POST':
        form = ItemInstanceForm(request.POST)
        if form.is_valid():
            form.save(commit=False)
            #item.type = titletype
            #if titletype == "News" or titletype == "Event":
            #    item.group = g
            #else:
            #    item.person = p
            #item.creator = request.user.person
            item.save()
            return HttpResponseRedirect('../../')
    else:
        form = ItemInstanceForm()
    
    del kwargs["type"]
    try:
        del kwargs["group"]
    except:
        pass
    try:
        del kwargs["slug"]
    except:
        pass
    

    return render_to_response('comms/item_form.html',{"group":g, "logo":logo, "css":css, "person":p,
        "type":titletype, "form":form,} )
