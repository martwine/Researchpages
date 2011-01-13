import Image
import string
import os
from django.core.validators import RequiredIfOtherFieldEquals, \
        ValidationError
from django.template import Context
from django.utils.encoding import smart_unicode
from afternoon.django.mail import send_html_mails
from afternoon.image import constrained_resize
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import User
from afternoon.countries import COUNTRIES
from django.template.defaultfilters import slugify
from django.conf import settings
from urllib import quote_plus, quote
from django.core.mail import send_mail
from esmg.institutions.models import Subdivision, Institution




TITLE_CHOICES = (
    ('Mr', 'Mr'),
    ('Ms', 'Ms'),
    ('Mrs', 'Mrs'),
    ('Miss', 'Miss'),
    ('Dr', 'Dr'),
    ('Prof', 'Prof')
)

class Person(models.Model):
    user = models.OneToOneField(User)
    title = models.CharField(maxlength=10, choices=TITLE_CHOICES, blank=True)
    desc = models.CharField(maxlength=100, blank=True)
    password = models.CharField(maxlength=20, editable=False)
    first_name = models.CharField(maxlength=50, blank=True)
    last_name = models.CharField(maxlength=100, blank=True)
    email = models.EmailField(blank=False, unique=True)    
    institution = models.ForeignKey(Institution, blank=True, null=True)
    department = models.CharField(maxlength=200, blank=True)
    subdepartmentchar = models.CharField(maxlength=200, blank=True)
    #subdepartment is a legacy name - subdepartment is actually a concatenation
    #of all institutional details into one field. For some reason it's stored in
    #a dtaabase tabel. All a bit pointless, but we're stuck with it for now 
    subdepartment = models.ForeignKey(Subdivision, blank=True, null=True,)
    address_line_1 = models.CharField(maxlength=200, blank=True)
    address_line_2 = models.CharField(maxlength=200, blank=True)
    city = models.CharField(maxlength=100, blank=True)
    post_code = models.CharField(maxlength=50, blank=True)
    country = models.CharField(maxlength=6, choices=COUNTRIES, blank=True)
    phone = models.CharField(maxlength=30, blank=True)
    slug = models.SlugField(maxlength=100, blank=True, editable=False)
    photo = models.ImageField(upload_to="people/photos/", blank=True)
    css = models.URLField(blank=True, null=True)
    friends = models.ManyToManyField('self', blank=True, null=True)
    requested_friends = models.ManyToManyField('self', blank=True, null=True,
            related_name='friend_requesters', symmetrical=False )

    class Meta:
        ordering = ["last_name", "first_name"]

    class Admin:
        #hide User entry in admin, arrange fields in Admin
        fields = (
            (None, {
                'fields':(('title', 'first_name', 'last_name'), 'email',
                    'institution', 'department',
                    'subdepartmentchar' , 'address_line_1',
                    'address_line_2', 'city', 'post_code',
                    'country', 'phone', 
                    'photo','css') 
            }),
        )

        list_display = ('last_name', 'first_name', 'subdepartment', 'country') 
        
    def save(self):
        """To get around password hash problems in admin for Person (editing
        onetoone relationship with users), hook before saving is used to
        create/update a user.  Admin thus needs only to use Person and User
        fields are kept updated. Also saves slug for people urls. An author
        entry is created for each person for the purposes of publications

        """
        
        self.email = self.email.lower()

        if self.user_id:
            # update User object
            new_user = False
            self.user.email = self.email
            self.user.set_password(self.password)
            self.user.save()
        else:
            new_user = True
            self.password = User.objects.make_random_password(length=6)
            nu = User.objects.create_user(self._make_username(),
                    self.email, self.password)
            nu.save()
            self.user_id = nu.id

        # derive slug 
        if self.first_name == '' or self.last_name == '':
            self.slug = ''
        else:
            new_slug = slugify("%s-%s" %
                    (self.first_name,self.last_name))
            c = Person.objects.filter(slug__startswith=new_slug).count()
            if c == 0:
                self.slug = new_slug
            else:
                slugtest = self.slug.startswith(new_slug)
                if (new_user or not slugtest):
                    self.slug = new_slug + "-" + smart_unicode(c+1)

        # resize person photo if required
        self._resize_photo()
        
        # send welcome email if new user
        # must be done after slug is calculated!
        if new_user:
            self._send_welcome_mail()
        
        #Author details
        from esmg.publications.models import Author
        if new_user:
            a, created = Author.objects.get_or_create(email=self.email)
            a.person=self
        else:
            a = Author.objects.get(person=self)
            a.email=self.email
        a.first_name = self.first_name
        a.last_name = self.last_name
        a.save()
        
        # Institution details: fix legacy inst details
        if self.subdepartment_id:
            self.subdepartmentchar = smart_unicode(self.subdepartment.name)
            self.department = smart_unicode(self.subdepartment.instdiv.division.name)
            self.institution = self.subdepartment.instdiv.institution
            self.subdepartment = None
            
        #save Person
        super(Person, self).save()
        
        #send internal welcome message
        body = 'Welcome to the growing community of researchers using \
                ResearchPages to promote themselves and their research and to network \
                with other researchers in similar fields. To get started, why not have a \
                look at the <a href=\"' + settings.URLBASE + '/help/welcome/\">getting \
                started guide</a>.Please let me know if you have any questions or \
                suggestions.  <br> Yours sincerely, <br> Martin Johnson'
        url = settings.URLBASE + '/messages/'
        recipients = Person.objects.filter(slug=self.slug)
        if new_user:
            from esmg.comms.models import send_notification
            send_notification('admin@researchpages','admin@researchpages.net',
                'Message', recipients, recipients,'Welcome to ResearchPages',body, url, False)

        #Create new CMS tree for each new person or update if slug has changed
        css = self.get_css()
        if new_user==True:
            from esmg.apparatus.models import treecreate
            treecreate(self.slug, 'person', None, self, self, css)
        else:
            from esmg.apparatus.models import Tree, treeupdate
            t = Tree.objects.get(person=self)
            treeupdate(self.slug, t.id, self, css)
        

    def _make_username(self):
        if self.email:
            email_account = self.email.lower().split("@")[0]
            username = base = email_account[:30]
            while User.objects.filter(username=username).count():
                username = base + User.objects.make_random_password(length=2,
                        allowed_chars=string.ascii_lowercase + string.digits)
            return username
        else:
            return User.objects.make_random_password(length=30)

    def delete(self):
        self.user.delete()
        super(Person, self).delete()

    def __unicode__(self):
        if self.first_name == '' or self.last_name == '':
            return 'Anonymous'
        else:
            full_name = u'%s %s' % (self.first_name, self.last_name)
            return full_name.strip()

    def name(self):
        bits = []
        if self.first_name:
            bits.append(self.first_name)
        if self.last_name:
            bits.append(self.last_name)
        return " ".join(bits)

    def address(self):
        bits = []
        for k in ("address_line_1", "address_line_2", "city",
                "post_code"):
            if getattr(self, k):
                bits.append(getattr(self, k))
        if self.country:
            bits.append(self.get_country_display())
        return bits

    def details(self):
        bits = []
        #if self.department:
        #    bits.append(self.department)
        #if self.institution:
        #    bits.append(self.institution)
        if self.subdepartment:
            instdetails = smart_unicode(self.subdepartment).split(',')
            instdetails.reverse()
            for bit in instdetails:
                bits.append(bit)
        return "<br>".join(bits)

    def groups(self):
        from esmg.groups.models import Group
        return Group.objects.filter(membership__person=self)
    
    def is_group_leader(self, person):
        """ find out if self is the leader or editor of any groups which person is a
                member (for editing person page priviledge)"""
        from esmg.groups.models import Group
        groups = Group.objects.filter(editor=self) | Group.objects.filter(project_leader=self) 
        grouptest = False
        for group in person.groups():
            if group in groups:
                grouptest =  True
            else:
                pass
        if grouptest:
            return True
        return False
        
    def get_absolute_url(self):
        return "%s/people/%s/" % (settings.URLBASE,
                quote_plus(self.slug))
    
    def get_edit_url(self):
        return "%s/people/%s/details/edit/" % (settings.URLBASE,
                quote_plus(self.slug))
    
    def get_admin_url(self):
        return "%s/admin/people/person/%s/" % (settings.URLBASE,
                self.id)
    
    def get_edit_password_url(self):
        return "%s/people/%s/details/password/" % (settings.URLBASE,
                quote_plus(self.slug))
    
    def get_css(self):
        if self.css:
            return self.css
        else:
            return settings.DEFAULT_CSS

    def _send_welcome_mail(self):
        
        subject = "researchpages.net account details"
        text = "people/person_welcome_mail.txt"
        html = "people/person_welcome_mail.html"

        ctx = {"person": self}
        ctx.update(settings.GLOBAL_CONTEXT)

        def welcome_gen():
            yield (self.email, settings.DEFAULT_FROM_EMAIL, subject, text, html, 
                    Context(ctx), None)

        send_html_mails(settings.EMAIL_HOST, settings.EMAIL_HOST_USER,
               settings.EMAIL_HOST_PASSWORD, welcome_gen)

        
    def _resize_photo(self):
        filename = settings.MEDIA_ROOT + smart_unicode(self.photo)
        try:
            im = Image.open(filename)
        except IOError:
            return

        if im.size != (settings.CONTACT_PHOTO_WIDTH,
                settings.CONTACT_PHOTO_HEIGHT):
            im = constrained_resize(im, settings.CONTACT_PHOTO_WIDTH,
                settings.CONTACT_PHOTO_HEIGHT)
            im.save(filename)

    def get_photo_html(self):
        src = self.get_photo_url()
        if not src:
            src = "%s/media/people/nophoto.png" % settings.URLBASE
        return """<img src="%s" alt="Photo of %s %s">""" % \
            (src, self.first_name, self.last_name)

    #really hacky thumbnail (shrink the fullsize photo in-browser)
    def get_thumbnail_html(self):
        if self.photo:
            name = self.photo.split('/')[-1]
            path = settings.MEDIA_ROOT + 'people/thumbs/' + name
            if not os.path.exists(path):
                im = settings.MEDIA_ROOT + smart_unicode(self.photo)
                try: 
                    im = Image.open(im)
                except IOError:
                    return
                thumb = constrained_resize(im,60,80)
                thumb.save(path)
            src = settings.URLBASE + '/media/people/thumbs/' + name
        else:
            src=False
        if not src:
            return ""
        else:
            return """<img src="%s" alt="Photo of %s %s">""" % \
                    (src, self.first_name, self.last_name)

    def rescount(self):
        return self.resource_set.count()
        
    def get_resources(self):
        #get all resources associated with person or group for the purposes of
        #popup lists
        from esmg.resources.models import Resource
        query = Q(person=self)|Q(group__in=self.groups)
        return Resource.objects.filter(query)
    
    def pubcount(self):
        author = self.author_set.all()[0]
        return author.authorship_set.count()
    
    def blogcount(self):
        return self.item_set.count()

    def authorships(self):
        author = self.author_set.all()[0]
        return author.authorship_set.all()
    
    def latestpublications(self):
        from esmg.publications.models import Publication
        return Publication.objects.filter(authorship__author__person=self)[0:5]
    
    def publications(self):
        from esmg.publications.models import Publication
        return Publication.objects.filter(authorship__author__person=self)
    
    def get_page_editorships(self):
        from esmg.apparatus.models import Page
        p = Page.objects.filter(editor=self, disabled=False) | Page.objects.filter(subeditor=self, disabled=False) | Page.objects.filter(subeditor2=self, disabled=False)
        if p.count:
            return p
        else:
            return False

    def pagechildren(self):
        from esmg.apparatus.models import Page
        return Page.objects.get(is_tree_top=True, tree__person=self).child_set.filter(disabled=False)

    def unreadmessages(self):
        from esmg.comms.models import Notification
        n = Notification.objects.filter(unread_recipients=self.user).filter(notification_type="Message").count()
        if n==0:
            return False
        return n
    
    def has_friends(self):
        return self.friends.all().count() > 0
