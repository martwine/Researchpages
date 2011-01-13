import csv
import operator
import unicodedata
from urllib import urlencode

from django import forms, newforms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.validators import ValidationError
from django.db.models import Q
from django.db.models.query import QuerySet
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader, Context
from django.utils.translation import ugettext_lazy as gettext_lazy

from django.views.generic.create_update import update_object
from afternoon.views.generic.list_detail import object_list

from django.contrib.auth.models import User

from afternoon.countries import COUNTRIES
from afternoon.django.mail import send_html_mails
from afternoon.django.errors.views import error

from esmg.people.models import Person
from esmg.groups.models import Group
from esmg.comms.models import send_notification

class RequestFriendForm(newforms.Form):
    message = newforms.CharField(required=False, widget=newforms.Textarea())

def search(request, **kwargs):
    group = kwargs.get("group", False)    
    try:
        q = request.GET["q"]
    except KeyError:
        if group:
            return HttpResponseRedirect("%s/%s/people/" % settings.URLBASE, group)
        else:    
            return HttpResponseRedirect("%s/people/" % settings.URLBASE)
        
    search_fields = ['last_name', 'email', 'first_name',]
    if not q.split() == []:
        css = settings.DEFAULT_CSS
        logo = settings.DEFAULT_LOGO
        g = False
        for bit in q.split():
            or_queries = [Q(**{'%s__search' % field_name: bit}) for field_name
                in search_fields]
            qs = QuerySet(Person)
            qs = qs.filter(reduce(operator.or_, or_queries)) 
    else:
        if group:
            qs = Person.objects.filter(membership__group=group)[:0]
            g = Group.objects.get(acronym=group)
            css = g.defaultcss
            logo = g.get_logo_url()
        else:
            qs = Person.objects.all()[:0]
            css = settings.DEFAULT_CSS
            logo = settings.DEFAULT_LOGO
            g = False
    kwargs["queryset"] = qs
    kwargs["allow_empty"] = True
    
    d = request.GET.copy()
    if  "page" in d:
        del d["page"]
    if  "submit" in d:
        del d["submit"]
    if "group" in d:
        del d["group"]
        
    kwargs["extra_context"] = {"query": urlencode(d), "query_readable": d["q"],
            "css": css, "logo": logo, "group":g}

    return object_list(request, **kwargs)


@login_required
def person_edit(request, **kwargs):
    slug = kwargs["slug"]
    group = kwargs.get("group", False)
    if group:
        g = Group.objects.get(acronym=group)
    u = request.user
    try: c = Person.objects.get(slug__exact=slug)
    except Person.DoesNotExist: raise Http404
    if u.is_superuser or u.person == c or u.person.is_group_leader(c):
    
        manipulator = Person.ChangeManipulator(c.user_id)
        if request.POST:
            new_data = request.POST.copy()
            new_data.update(request.FILES)
            new_data['password'] = c.password
            errors = manipulator.get_validation_errors(new_data)
        
            # make the following fields required in the form validation even
            # though they are blank=True in the model
            if new_data['first_name'] == '':
                errors.setdefault('first_name', []).append(gettext_lazy('This \
                    field is required.'))
            if new_data['last_name'] == '':
                errors.setdefault('last_name', []).append(gettext_lazy('This \
                    field is required.'))

            if not errors:
                manipulator.do_html2python(new_data)
                manipulator.save(new_data)
                if group:
                    redirbase = g.get_absolute_url()
                else:
                    redirbase = settings.URLBASE
                return HttpResponseRedirect("%s/people/%s/" % (redirbase, slug))
        else:
            new_data = c.__dict__
            errors = {}
        form = forms.FormWrapper(manipulator, new_data, errors)
        if group:
            css = g.defaultcss
            logo = g.get_logo_url()
        elif c.css:
            css = c.css
            logo = settings.DEFAULT_LOGO
        else:
        		css = settings.DEFAULT_CSS
        		logo = settings.DEFAULT_LOGO
        
        return render_to_response('people/person_form.html', {'form': form,
                'person': c, 'name': c.name(), 'slug': slug, 'errors': errors, 'css': css, 'logo': logo}, RequestContext(request))

    else:
        return error(request, "You do not have the appropriate permissions \
                to edit this page")
    

class EditPasswordManipulator(forms.Manipulator):
    def __init__(self, request):
        self.request = request
        self.fields = (
            forms.HiddenField(field_name="username"),
            forms.PasswordField(field_name="password_old", length=30,
                    maxlength=30, is_required=True,
                    validator_list=[self.is_current_password]),
            forms.PasswordField(field_name="password", length=30,
                    maxlength=30, is_required=True,
                    validator_list=[self.is_valid_password]),
            forms.PasswordField(field_name="password_confirm", length=30,
                    maxlength=30, is_required=True,
                    validator_list=[self.matches_password])
        )

    def is_current_password(self, field_data, all_data):
        if not self.request.user.check_password(field_data):
            raise ValidationError("This does not match your current password.")

    def is_valid_password(self, field_data, all_data):
        if len(field_data) < 5:
            raise ValidationError("You did not enter a valid password.")
    
    def matches_password(self, field_data, all_data):
        if field_data != all_data["password"]:
            raise ValidationError("Your new passwords do not match.")

class ForgotPasswordManipulator(forms.Manipulator):
    def __init__(self, request):
        self.request = request
        self.fields = (
            forms.TextField(field_name="email", length=30,
                    maxlength=100, is_required=True,
                    validator_list=[self.is_recognised_email]),
        )

    def is_recognised_email(self, field_data, all_data):
        try: Person.objects.get(email=field_data)
        except: raise ValidationError("The email address you entered does not \
                match any on our records. Could you have used a different one to \
                register?")


@login_required
def password_edit(request, **kwargs):
    slug = kwargs["slug"]
    u = request.user
    p = u.person
    if slug != u.person.slug or u.is_anonymous():
        raise Http404("You may only edit your own password.")

    manipulator = EditPasswordManipulator(request)
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            password = new_data['password_confirm']
            #u.set_password(password)
            #u.save()
            p.password = password
            p.save()
            return render_to_response('accounts/password_form_saved.html',
                    {'slug': slug}, RequestContext(request))
    else:
        new_data = {'username': u.username}
        errors = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('accounts/password_form.html', {'form': form}, 
            RequestContext(request))


def _send_password_reminder(email):
    c = Person.objects.get(email=email)

    subject = "Password reminder"
    text = "people/password_reminder_mail.txt"
    html = "people/password_reminder_mail.html"

    ctx = {"person": c}
    ctx.update(settings.GLOBAL_CONTEXT)

    def reminder_gen():
        yield (c.email, settings.DEFAULT_FROM_EMAIL, subject, text, html, 
                Context(ctx), None)

    send_html_mails(settings.EMAIL_HOST, settings.EMAIL_HOST_USER,
            settings.EMAIL_HOST_PASSWORD, reminder_gen)


def password_forgot(request, **kwargs):
    manipulator = ForgotPasswordManipulator(request)
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            _send_password_reminder(new_data["email"])
            return render_to_response('accounts/forgot.html', {'sent': True},
                    RequestContext(request))
    else:
        new_data = errors = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('accounts/forgot.html', {'form': form},
                RequestContext(request))

        
@login_required
def person_export(request):
    if not request.user.is_staff:
        raise Http404("People export is available to staff only.")
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=personlist.csv'
    
    def asciify(detail):
        if detail:
            return unicodedata.normalize('NFKD',detail).encode('utf8')
        return ' ' 
    
    people = Person.objects.all()
    writer = csv.writer(response)
    writer.writerow(["Email", "Title", "First name", "Last name", "Department","Address line 1","Address line 2","Address line 3",
            "City", "Post code", "Country", "Phone", ])
    for person in people:
        writer.writerow([asciify(person.email), asciify(person.title),
                asciify(person.first_name), asciify(person.last_name),
                asciify(person.subdepartmentchar), asciify(person.address_line_1),
                asciify(person.address_line_2), asciify(person.city),
                asciify(person.post_code), asciify(person.phone)])
    
    return response
    
def list(request, **kwargs):
    people = Person.objects.all()
    group = kwargs.get("group", False)
    if group:
        g = get_object_or_404(Group, acronym=group)
        query = people.filter(membership__group=g)
    else:
   	    query = people
    kwargs["queryset"] = query
    kwargs["allow_empty"] = True
    
    if group:
        del kwargs["group"]
        kwargs["extra_context"] = {"group":g, "css":g.defaultcss,
                "logo":g.get_logo_url(), "latest_people": query.order_by("-user_id")[:5]}
    else:
        kwargs["extra_context"] = {"css": settings.DEFAULT_CSS,
                "logo":settings.DEFAULT_LOGO, "latest_people": people.order_by("-user_id")[:5]}
    
    return object_list(request, **kwargs)   

@login_required
def home(request, **kwargs):
    from esmg.comms.models import Notification
    person = request.user.person
    n = Notification.objects.filter(recipients=request.user)
    nlatest = n[0:10] 
    return render_to_response('people/home.html',
            {'person':person, 'latest':nlatest, 'logo':settings.DEFAULT_LOGO},
            RequestContext(request))

@login_required
def friend_request(request, **kwargs):
    requester = request.user.person
    slug = kwargs.get('slug', False)
    if slug:
        friend = get_object_or_404(Person, slug=slug)
    else:
        return error(reqest, "something went wrong here. Please report this to admin@researchpages.net")
    
    #request freind form
    if request.method == "POST":
        requestform = RequestFriendForm(request.POST)
        if requestform.is_valid():
            request.user.person.requested_friends.add(friend)
            recipients = Person.objects.filter(slug=friend.slug)
            title = 'Friend request from ' + str(requester)
            body = requestform.cleaned_data['message']
            send_notification(str(request.user.person),
                    'friend_request@researchpages.net','Friend request',
                    recipients, recipients, title, body, settings.URLBASE +
                    '/friend_requests/', True)
            return HttpResponseRedirect(friend.get_absolute_url())
    else:
        requestform = RequestFriendForm()

    logo = settings.DEFAULT_LOGO
    
    return render_to_response('people/friend_request.html',
            {'logo':logo, 'rform': requestform, 'friend':friend},RequestContext(request))

@login_required
def friend_confirms(request,**kwargs):
    person = request.user.person
    requesters = person.friend_requesters.all()
    
    if request.method =='POST':
        new_data=request.POST.copy()
        for req in requesters:
            status = new_data[str(req.user_id)]
            if status == 'confirm':
                person.friends.add(req)
                person.friend_requesters.remove(req)
            elif status == 'deny':
                person.friend_requesters.remove(req)
            else:
                pass
        return HttpResponseRedirect(settings.URLBASE + '/home/')
        
    return render_to_response('people/friend_confirms.html',
            {person: person, 'requesters':requesters},
            RequestContext(request))
