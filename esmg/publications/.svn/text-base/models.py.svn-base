from django.db import models
from django.utils.encoding import smart_unicode
from django.core.validators import ValidationError
from esmg.people.models import Person
from esmg.groups.models import Group
from django.conf import settings
from django.utils.http import urlquote_plus, urlquote
from esmg.middleware import threadlocals
import os

def is_valid_year(field_data, all_data):
    i = int(field_data)
    if i < 1900 or i > 3000:
        raise ValidationError("%s is not a valid 4-digit year." % i)


class Publication(models.Model):
    PUBLICATION_TYPE_CHOICES = (
        ('journal', 'Journal article'),
        ('book', 'Book'),
        ('chapter', 'Book chapter'),
        ('thesis', 'PhD thesis'),
        ('proceedings', 'Conference proceedings'),
        ('presentation', 'Presentation'),
        ('article', 'Newspaper or magazine article'),
        ('other', 'Other')
    )
    type = models.CharField(maxlength=20, choices=PUBLICATION_TYPE_CHOICES)
    year = models.IntegerField(validator_list=[is_valid_year]) 
    title = models.TextField()
    keywords = models.CharField(maxlength=250, blank=True)
    publication_name = models.CharField(maxlength=200, blank=True)
    volume = models.CharField(maxlength=20, blank=True)
    issue = models.CharField(maxlength=20, blank=True)
    book_title = models.CharField(maxlength=200, blank=True, 
            verbose_name="Book title")
    publisher = models.CharField(maxlength=100, blank=True)
    conference_name = models.CharField(maxlength=100, blank=True)
    institution = models.CharField(maxlength=200, blank=True)
    city = models.CharField(maxlength=100, blank=True)
    pages = models.CharField(maxlength=20, blank=True)
    abstract = models.TextField(blank=True)
    link = models.URLField(verify_exists=True, blank=True)
    suppinfolink = models.URLField(verify_exists=True, blank=True)
    doi = models.CharField(maxlength=100, blank=True)
    file = models.FileField(upload_to='resources/%Y/%m/%d/', blank=True)
   
    def save(self):
        from esmg.resources.models import Resource 

        # save a resource linked to the file if one is uploaded
        if self.file:
            try:
                p = Publication.objects.get(id=self.id)
            except:
                p = False
            
            # if publication already exists and has a file associated, there
            # must already be a resource file (or something's gone wrong and
            # will quietly fail)... 
            if p and p.file:
                try:
                    r = Resource.objects.get(file=p.file)
                except:
                    r = Resource(file=self.file)
            else:
            #new resource
                r = Resource(file=self.file)
            r.keywords = self.keywords
            r.title = smart_unicode(self)
            description = '<i>' + self.title + '</i>, ' + self.details() 
            r.description = description
            r.type = 'doc'
            r.permissions = 'pblc'
            if not r.person:
                r.person = threadlocals.get_current_user().person
            r.save()
        # save Publication
        super(Publication, self).save()

    def __unicode__(self):
        c = self.authorship_set.count()
        if c == 0:
            namestring = "Unknown author"
        else:
            a = self.authorship_set.all()[0]
            namestring = a.author.last_name 
            if c == 2:
                b = self.authorship_set.all()[1]
                namestring += " and " + b.author.last_name
            if c > 2:
                namestring += " et al."
        return namestring + ", " + smart_unicode(self.year)

    def get_absolute_url(self):
        return settings.URLBASE + '/publications/' + smart_unicode(self.id) + '/'
    
    def get_best_link(self):
        if self.link:
            return smart_unicode(self.link)
        elif self.doi:
            return "http://dx.doi.org/" + self.doi
        elif not self.file:
            return "http://scholar.google.com/scholar?q=%s" % (urlquote_plus(self.title))
        else:
            return False

    def details(self):
        typemap = {
            'chapter':      self.chapter_published_details,
            'thesis':       self.thesis_published_details,
            'proceedings':  self.chapter_published_details,
        }
        return typemap.get(self.type, self.normal_published_details)()
        
    def normal_published_details(self): 
        bits = []
        if self.publication_name:
            bits.append(self.publication_name)
        if self.volume:
            bits.append(self.volume)
        if self.issue:
            bits.append("(" + self.issue + ")")
        if self.book_title:
            bits.append(self.book_title)
        if self.publisher:
            bits.append(self.publisher)
        if self.institution:
            bits.append(self.institution)
        if self.conference_name:
            bits.append(self.conference_name)
        if self.city:
            bits.append(self.city)
        if self.pages:
            bits.append(self.pages)
        return ", ".join(bits)
        
    def chapter_published_details(self):
        eds = [smart_unicode(e) for e in self.editorship_set.all()]
        bits = []
        if self.book_title:
            #bits.append("In: " + self.book_title + ", Eds: " + ", ".join(eds))
            bits.append("In: " + self.book_title)
        if self.publisher:
            bits.append(self.publisher)
        if self.city:
            bits.append(self.city)
        if self.pages:
            bits.append("pp " + self.pages)
        return ", ".join(bits)
    
    def thesis_published_details(self):
        bits = []
        bits.append("PhD Thesis")
        if self.institution:
            bits.append(self.institution)
        if self.city:
            bits.append(self.city)
        return ", ".join(bits)
    
    def filename(self):
        path = self.get_file_filename()
        return smart_unicode(os.path.basename(path))
    
    class Meta:
        #get_latest_by = 'title'
        ordering = ('-year', "title")

    class Admin:
        pass


class Author(models.Model):
    first_name = models.CharField(maxlength=50, blank=True)
    last_name = models.CharField(maxlength=100, blank=True)
    email = models.EmailField(blank=True)    
    person = models.ForeignKey(Person, blank=True, null=True, unique=True)

    class Meta:
        ordering = ['last_name']

    class Admin:
        pass
    
    def get_form_author(self):
        """return an email if author is a person - for the purposes of loading
        initial data into the publications form"""
        if self.person:
            return self.person.email
        else:
            return 'no'
        
    def __unicode__(self):
        return self.first_name + ' ' + self.last_name

class Authorship(models.Model):
    publication = models.ForeignKey(Publication, edit_inline=models.TABULAR,
            num_in_admin=10, num_extra_on_change=3)
    author = models.ForeignKey(Author, core=True)
    
    class Meta:
        ordering = 'publication'
        order_with_respect_to = 'publication'
        get_latest_by = 'publication'
    
    class Admin:
        pass
    
    def __unicode__(self):
        return smart_unicode(self.author)

    def get_nonperson_author(self):
        if self.author.person:
            return u""
        else:
            return self.author.first_name + u" " + self.author.last_name + u", " + self.author.email
    
    def get_person_slug(self):
        return self.author.person.slug

    def get_absolute_url(self):
        return "%s/people/%s/" % (settings.URLBASE,
                urlquote_plus(self.author.person.slug))


class Editorship(models.Model):
    publication = models.ForeignKey(Publication, edit_inline=models.TABULAR,
            num_in_admin=3)
    editor = models.ForeignKey(Author, core=True)
    
    class Meta:
        order_with_respect_to = 'publication'
        get_latest_by = 'publication'

    class Admin:
        pass
    
    def __unicode__(self):
        return smart_unicode(self.editor)

    def get_absolute_url(self):
        return "%s/people/%s/" % (settings.URLBASE,
                urlquote_plus(self.author.slug))

class Groupship(models.Model):

    publication = models.ForeignKey(Publication, edit_inline=models.TABULAR,
            num_in_admin=3)
    group = models.ForeignKey(Group, core=True)
    
