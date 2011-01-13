from datetime import datetime
from django.db import models
from django.utils.encoding import smart_unicode

from esmg.people.models import Person
from esmg.groups.models import Group

write_private_help = "Make this wiki page editable only by group members.Otherwise this wiki will be editable by any logged-in member of ResearchPages"
read_private_help = "If this option is set, only group members will be able to see this wiki page. Otherwise, it will be readable by anyone in the world (not just site members)"

class WikiPage(models.Model):
    group = models.ForeignKey(Group, editable=False)
    #identify the wiki 'home' page for the group
    groupwikihome = models.BooleanField(editable=False)
    slug = models.SlugField(editable=False)
    locked_time = models.IntegerField(editable=False, blank=True)
    locked_by = models.ForeignKey(Person, related_name='locked_wikipages',
            blank=True, editable=False)
    disabled = models.BooleanField(editable=False)
    write_private = models.BooleanField("Write permissions", help_text=write_private_help)
    read_private = models.BooleanField("Read permissions", help_text=read_private_help)

    class Admin:
        pass

    def __unicode__(self):
        return str(self.group) + u":" + str(self.slug)
    
    def get_css(self):
        return self.group.defaultcss


class WikiPageContent(models.Model):
    page = models.ForeignKey(WikiPage, related_name="wpcontent", editable=False)
    title = models.CharField(maxlength=100)
    body = models.TextField()
    last_updated = models.DateTimeField(editable=False)
    version = models.PositiveIntegerField(editable=False)
    last_editor = models.ForeignKey(Person, null=True, editable=False)
    
    def save(self):
        if not self.version:
            versioncount = WikiPageContent.objects.filter(page=self.page).count()
            self.version = versioncount + 1
        self.last_updated = datetime.now()
        super(WikiPageContent, self).save()

    def unicode(self):
        return self.title + " on " + smart_unicode(self.page)

    class Admin:
        pass


    class Meta:
        get_latest_by = 'last_updated'
        ordering = ['-version']
    
