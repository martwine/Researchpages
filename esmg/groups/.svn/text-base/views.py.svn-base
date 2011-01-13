from django import newforms as forms
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext_lazy

from esmg.people.models import Person
from esmg.groups.models import Group, Membership, Role
from esmg.comms.models import send_notification

from afternoon.django.errors.views import error


class PersonForm(forms.Form):
    people = forms.CharField(widget=forms.Textarea, help_text="<br><br> Add one person \
            per line observing the following covention: <br>Firstname Lastname,\
            Email")

class MemberForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(MemberForm, self).__init__(*args, **kwargs)
        peoplechoices=[('', '----------')] + [(person.email, person.last_name + ', ' +
                person.first_name + ' ' +  person.email) for person in Person.objects.all()]
        self.fields['people'].choices = peoplechoices
    people = forms.MultipleChoiceField(choices=[], help_text="Select multiple \
            people by holding down \"Control\" (or \"Command\" on a Mac while clicking")


class RoleForm(forms.Form):
    role = forms.CharField(widget=forms.Textarea, max_length=400)
    
@login_required
def manage(request, **kwargs):
    def linereturn(line, linereturns):
        if linereturns == "":
            linereturns = linereturns + line
        else:
            linereturns = linereturns + u'\n' + line 
        return linereturns
    group = kwargs.get("group", False)
    if group:
        g = Group.objects.get(acronym=group)
        css = g.defaultcss
        logo = g.get_logo_url()
    person = request.user.person
    permtest = group and (person == g.project_leader or person == g.editor or request.user.is_superuser)
    if not permtest:
        return error (request, "you do not have permission to change the options for this group")
    
    ManageForm = forms.form_for_instance(g, fields=('name','subtitle','acronym','preferred_name','project_leader','editor','logo','description','keywords','friends','defaultcss','forum'))
    
    if request.method == 'POST':
        new_data=request.POST.copy()
        if new_data['submit']=='save':
            mform = ManageForm(request.POST, request.FILES)
            if mform.is_valid():
                mform.save()
                return HttpResponseRedirect('../')
            else:
                pform = PersonForm()
                mbform = MemberForm()
        elif new_data['submit']=='add':
            mbform = MemberForm(request.POST)
            r = Role.objects.get(role="")
            if mbform.is_valid():
                memberlist = mbform.cleaned_data['people']
                for email in memberlist:
                    p = Person.objects.get(email=email)
                    if Membership.objects.filter(person=p, group=g).count() > 0:
                        pass
                    else:
                        m = Membership(person=p,group=g,role=r)
                        m.save()
                return HttpResponseRedirect('../people/')
            else:
                pform = PersonForm()
                mform = MemberForm()
                
        elif new_data['submit']=='subscribe':
            pform = PersonForm(request.POST)
            personlist = new_data['people']
            personlist = personlist.split('\n')
            errorlist=[]
            linereturns = u""
            r = Role.objects.get(role="")
            for line in personlist:
                items=line.split(',')
                if not len(items) == 2:
                    erroritem= items[0] + u': Line not formatted correctly'
                    errorlist.append(erroritem)
                    linereturns = linereturn(line,linereturns)
                elif not len(items[1].split('@')) == 2:
                    erroritem= items [0] + u': Invalid email address'
                    errorlist.append(erroritem)
                    linereturns = linereturn(line,linereturns)
                else:
                    firstname = items[0].split()[0]
                    lastname = ' '.join(items[0].split()[1:])
                    email = items[1].strip()
                    emailclash = Person.objects.filter(email=email).count() > 0
                    if emailclash:
                        erroritem = items[0] + u': Email already exists on the \
                                database. Find the user in the Existing Users \
                                form (above) and subscribe them that way'
                        errorlist.append(erroritem)
                        linereturns = linereturn(line,linereturns)
                    else:
                        p = Person(first_name=firstname,last_name=lastname, email=email)
                        p.save()
                        m = Membership(person=p,group=g,role=r)
                        m.save()
            if not errorlist == []:
                erroroutput = [u"The following people were not added, for the \
                        reasons stated:"]
                for erroritem in errorlist:
                    erroroutput.append(erroritem)
                pform._errors={"people": erroroutput}
                formdata = {'people': linereturns}
            if pform.is_valid():
                return HttpResponseRedirect('../people/')
            else:
                mform=ManageForm()
                mbform=MemberForm()
                pform = PersonForm(formdata)
                pform._errors={"people": erroroutput}
    else:
        pform = PersonForm()
        mform = ManageForm() 
        mbform = MemberForm()
    
    return render_to_response('groups/group_form.html',{"logo": logo, "group":g,
            "css":css, "manageform":mform, "pform":pform, "mbform":mbform})


@login_required
def role(request, **kwargs):
    subject = kwargs.get("slug", False)
    group = kwargs.get("group", False)
    g = Group.objects.get(acronym=group)
    css = g.defaultcss
    logo = g.get_logo_url()
    person = request.user.person
    permtest = group and subject and (person == g.project_leader \
            or person == g.editor or request.user.is_superuser \
            or person.slug==subject)
    if not permtest:
        return error (request, "you do not have permission to edit this \
                person's role in this group")
    if subject and group:
        try: 
            membership = Membership.objects.filter(group__acronym=group,
                    person__slug=subject)[0]
        except Membership.DoesNotExist: raise Http404
    else:
        return error (request, "Somehow, you got to this page without specifing \
                a person whose role you wish to define, or which group to define \
                it for. That doesn't work.  Nobody should ever see this \
                message...")
                
    if request.method == 'POST':
        new_data = request.POST.copy()
        rform = RoleForm(request.POST)
        new_role = new_data['role']
        try:
            r = Role.objects.get(role=new_role)
        except:
            r = Role(role=new_role,preferred_name='name')
            r.save()
        if rform.is_valid():
            membership.role = r
            membership.save()
            return HttpResponseRedirect('../../')
        else:
            rform = RoleForm(initial={'role': membership.role},)
        
    else:
        rform = RoleForm(initial={'role': membership.role},)
    subj = Person.objects.get(slug=subject)
    return render_to_response('groups/role_form.html',{"logo": logo, "group":g,
            "css":css, "roleform":rform, "subject":subj})
        
    
