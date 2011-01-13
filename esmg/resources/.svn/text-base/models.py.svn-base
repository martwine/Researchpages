from django.utils.encoding import smart_unicode
from django.conf import settings
from django.db import models
import os

RESOURCE_TYPE_CHOICES = (
    ('apos', 'Poster'),
    ('bpre', 'Presentation'),
    ('cdoc', 'Document'),
    ('ddat', 'Data File'),
    ('epic', 'Image'),
    ('fres', 'Other type of file')
)

RESOURCE_PERMISSION_CHOICES = (
    ('prvt', 'Private - visible to only person or group'),
    ('rstrc', 'Restricted - Visioble only to active site members'),
    ('pblc', 'Public - visible to everyone'),
)


class Resource(models.Model):
    from esmg.groups.models import Group
    from esmg.people.models import Person
    
    type = models.CharField(maxlength=4, choices=RESOURCE_TYPE_CHOICES,
            default="fres")
    title = models.CharField(maxlength=250)
    description = models.TextField(blank=True)
    keywords = models.CharField(maxlength=250, blank=True)
    file = models.FileField(upload_to='resources/%Y/%m/%d/')
    group = models.ForeignKey(Group, null=True, blank=True)
    person = models.ForeignKey(Person, null=True, blank=True)
    permissions = models.CharField(maxlength=5, choices=RESOURCE_PERMISSION_CHOICES, default="prvt")
    
    class Admin:
        pass

    def filename(self):
        path = self.get_file_filename()
        return smart_unicode(os.path.basename(path))
    
    def __unicode__(self):
        fn = self.filename()
        return fn or "[unknown file]"

    def get_absolute_url(self):
        return "%s/resources/%s/" % (settings.URLBASE, self.id)

    def get_admin_url(self):
        return "%s/admin/resources/resource/%s/" % (settings.URLBASE, self.id)
    
