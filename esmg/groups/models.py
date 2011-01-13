from django.db import models
from esmg.institutions.models import Institution
from django.conf import settings
from django.utils.encoding import smart_unicode


NAME_CHOICES = (
    ('acronym', 'Acronym'),
    ('name', 'Full Name'),
)

TYPE_CHOICES= (
    ('', ''),
    ('workgroup', 'Between- or within-project working group'),
    ('resgroup', 'Research Group'),
    ('network', 'Research Network'),
    ('project', 'Collaborative Project'),
    ('centre', 'Research Centre'),
    ('instit', 'Research Institution'),
    ('natprog', 'National Programme'),
    ('intprog', 'International Programme'),
)

class Group(models.Model):
    """Represents a sub-site of CMS pages associated with a particular 'group'
    (e.g. research group, scientific project or programme) and is associated with people,
    publications, and page trees by foreign or many-to-many keys on these
    models. Foreignkey on Group relates groups to host institutions.
    """

    from esmg.people.models import Person

    #identifiers
    name = models.CharField(maxlength=100, blank=False, unique=True)
    subtitle = models.CharField(maxlength=100, blank=True)
    acronym = models.CharField(maxlength=25, blank=False, unique=True)
    preferred_name = models.CharField(maxlength=10, choices=NAME_CHOICES,
            blank=False)
    
    #details
    type = models.CharField(maxlength=100, choices=TYPE_CHOICES)
    host_institution = models.ForeignKey(Institution, 
            related_name="groups")
    project_leader = models.ForeignKey(Person, blank=True, null=True,
            related_name="group_leadership")
    start_date = models.DateField(blank=True, null=True)
    finish_date = models.DateField(blank=True, null=True)
    funding_bodies = models.ManyToManyField(Institution, blank=True,
            related_name="funded_groups")
    logo = models.ImageField(upload_to="groups/logos/", blank=True)
    editor = models.ForeignKey(Person, blank=False, null=False)    
    description = models.TextField(blank=True)
    keywords = models.CharField(blank=True, maxlength=200)
    #heirarchy
    parent = models.ForeignKey('self', blank=True, related_name="childset",
            null=True)
    friends = models.ManyToManyField('self', blank=True, related_name="friendset")
    defaultcss = models.URLField(blank='True')
   
    #options
    forum = models.BooleanField(default=False)
    
    #group watchers
    watchers = models.ManyToManyField(Person, related_name="watched_groups",
            editable=True, blank=True, null=True)
    

    class Admin:
        pass
    
    
    class Meta:
        ordering = ['name']

        
    def save(self):
        """ Create new CMS tree for each new project
        """
        from esmg.apparatus.models import Tree, treecreate, treeupdate
        if Tree.objects.filter(group=self).count() == 0:
            treecreate(self.acronym, 'group', self, None, self.editor,
                    self.defaultcss)
        elif Tree.objects.filter(group=self).count() == 1:
            tree = Tree.objects.get(group=self)
            treeupdate(self.acronym, tree.id, self.editor, self.defaultcss)
        else:
            pass
            #error in here
        super(Group, self).save()
        
    def __unicode__(self):
        if self.preferred_name == 'acronym':
            return self.acronym
        else: return self.name

    def get_absolute_url(self):
        return settings.URLBASE + '/' + self.acronym 

    def get_logo_url(self):
        if self.logo:
            return settings.URLBASE + '/media/' + self.logo
        else:
            return settings.DEFAULT_LOGO
    
    def rescount(self):
        return self.resource_set.count()

    def pubcount(self):
        return self.groupship_set.count()

    def newscount(self):
        return self.item_set.filter(type="News").count() 

    def news(self):
        return self.item_set.filter(type="News")[0:3]
    
    def eventscount(self):
        return self.item_set.filter(type="Event").count() 
    
    def events(self):
        return self.item_set.filter(type="Event")[0:3]
    
    def children(self):
        from esmg.apparatus.models import Page
        try:
            return Page.objects.get(is_tree_top=True, tree__group=self).child_set.filter(disabled=False)    
        except:
            return ""

    def members(self):
        from esmg.people.models import Person
        return Person.objects.filter(membership__in=self.membership_set.all())

    def has_wiki(self):
        return self.wikipage_set.count()
    

class Role(models.Model):
    role = models.CharField(max_length=400, blank=False)
    abbreviation = models.CharField(maxlength=10, blank=True)
    preferred_name = models.CharField(maxlength=10, choices=NAME_CHOICES,
            blank=False)

    class Admin:
        pass

    def __unicode__(self):
        if self.preferred_name == 'acronym':
            return self.abbreviation 
        else: return self.role 

    
class Membership(models.Model):
    """ Join table between people and groups to define membership and roles
    """
    from esmg.people.models import Person
    person = models.ForeignKey(Person, blank=False)
    group = models.ForeignKey(Group,blank=False)
    role = models.ForeignKey(Role, blank=True, null=True)

    def __unicode__(self):
        return smart_unicode(self.group) + ": " + smart_unicode(self.person) + ": " + smart_unicode(self.role) 

    class Admin:
        pass

